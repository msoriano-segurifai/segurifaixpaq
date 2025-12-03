import logging
import json
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import ServiceCategory, ServicePlan, UserService
from django.conf import settings
from .serializers import (
    ServiceCategorySerializer, ServicePlanSerializer, ServicePlanListSerializer,
    UserServiceSerializer, UserServiceCreateSerializer
)
from apps.users.permissions import IsAdmin
from apps.paq_wallet.paq_service import PAQPaymentService

logger = logging.getLogger(__name__)


# =============================================================================
# AI PLAN SUGGESTION ENDPOINT
# =============================================================================

# MAPFRE Plan Information for AI Context - PAQ Wallet Integration
MAWDY_PLANS_CONTEXT = """
MAPFRE ofrece planes de asistencia en Guatemala a través de PAQ Wallet con las siguientes opciones:

=== PLAN ASISTENCIA VIAL ===

## Plan Asistencia Vial (Inclusión PAQ) - Q36.88/mes (Q442.56/año)
Plan preferencial para usuarios de PAQ Wallet.
Incluye seguro de Muerte Accidental: Q3,000

## Plan Asistencia Vial (Opcional) - Q38.93/mes (Q467.16/año)
Plan independiente para cualquier persona.
Incluye seguro de Muerte Accidental: Q3,000

SERVICIOS DEL PLAN ASISTENCIA VIAL:
- Grúa del Vehículo (3/año, límite $150 USD) - Por accidente o falla mecánica
- Abasto de Combustible (3/año, límite combinado $150) - 1 galón de emergencia
- Cambio de Neumáticos (3/año, límite combinado $150) - Instalación de llanta
- Paso de Corriente (3/año, límite combinado $150) - Arranque de batería
- Cerrajería Vehicular (3/año, límite combinado $150) - Apertura de vehículo 24/7
- Ambulancia por Accidente (1/año, $100 USD) - Traslado médico de emergencia
- Conductor Profesional (1/año, $60 USD) - Por enfermedad o embriaguez
- Taxi al Aeropuerto (1/año, $60 USD) - Por viaje al extranjero
- Asistencia Legal Telefónica (1/año, $200 USD) - Asesoría legal por accidente
- Apoyo Económico Emergencia Hospital (1/año, $1,000 USD) - Pago directo
- Rayos X (1/año, $300 USD) - Servicio de radiografía
- Descuentos en Red de Proveedores (Hasta 20%)
- Asistentes Telefónicos Incluidos (Cotización repuestos, referencias médicas)

=== PLAN ASISTENCIA MÉDICA ===

## Plan Asistencia Médica (Inclusión PAQ) - Q34.26/mes (Q411.12/año)
Plan preferencial para usuarios de PAQ Wallet.
Incluye seguro de Muerte Accidental: Q3,000

## Plan Asistencia Médica (Opcional) - Q36.31/mes (Q435.72/año)
Plan independiente para cualquier persona.
Incluye seguro de Muerte Accidental: Q3,000

SERVICIOS DEL PLAN ASISTENCIA MÉDICA:
- Orientación Médica Telefónica (Ilimitado) - Consulta médica 24/7
- Conexión con Especialistas (Ilimitado) - Referencias a médicos de la red
- Coordinación de Medicamentos (Ilimitado) - Entrega a domicilio
- Consulta Presencial (3/año, $150 USD) - Médico general, ginecólogo o pediatra
- Cuidados Post-Operatorios Enfermera (1/año, $100 USD) - A domicilio
- Artículos de Aseo (1/año, $100 USD) - Por hospitalización
- Exámenes de Laboratorio Básicos (2/año, $100 USD) - Heces, orina, hematología
- Exámenes Especializados (2/año, $100 USD) - Papanicolau, mamografía, antígeno
- Nutricionista Video Consulta (4/año, $150 USD) - Para grupo familiar
- Psicología Video Consulta (4/año, $150 USD) - Para núcleo familiar
- Mensajería Hospitalización (2/año, $60 USD) - Por emergencia
- Taxi Familiar Hospitalización (2/año, $100 USD) - Por hospitalización del titular
- Ambulancia por Accidente (2/año, $150 USD) - Traslado del titular
- Taxi Post-Alta (1/año, $100 USD) - Traslado al domicilio tras hospitalización

=== PLAN COMBO (VIAL + MÉDICA) ===

## Plan Combo - Q65.00/mes (Q780.00/año)
Combina TODOS los servicios de Vial y Médica con beneficios mejorados:
- Muerte Accidental: Q6,000 (doble cobertura)
- Ambulancia: 3/año (combinado)
- Consultas médicas: 6/año (combinado)
- Video consultas nutrición/psicología: 8/año (combinado)
- Ahorro aproximado de Q6/mes vs comprar ambos por separado

=== RESUMEN DE PRECIOS ===
| Plan                           | Mensual  | Anual     |
|--------------------------------|----------|-----------|
| Asistencia Vial (Inclusión)    | Q36.88   | Q442.56   |
| Asistencia Vial (Opcional)     | Q38.93   | Q467.16   |
| Asistencia Médica (Inclusión)  | Q34.26   | Q411.12   |
| Asistencia Médica (Opcional)   | Q36.31   | Q435.72   |
| Combo (Vial + Médica)          | Q65.00   | Q780.00   |

NOTA IMPORTANTE:
- "Inclusión PAQ" = precio preferencial para usuarios de PAQ Wallet
- "Opcional" = precio estándar para compra independiente
- Todos los planes incluyen seguro de Muerte Accidental
- Proveedor de servicios: MAPFRE Guatemala
- Todos los límites en USD se aplican por evento/uso
"""


@api_view(['POST'])
@permission_classes([AllowAny])
def ai_plan_suggestion(request):
    """
    AI-powered plan suggestion endpoint using Anthropic Claude.
    Analyzes user's needs and recommends the best MAWDY plan.
    """
    prompt = request.data.get('prompt', '').strip()

    if not prompt:
        return Response(
            {'error': 'Por favor describe tus necesidades de seguro/asistencia'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        import anthropic

        # Initialize Anthropic client
        client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else None
        )

        # Build the AI prompt
        system_prompt = f"""Eres un asistente experto de MAPFRE Guatemala, proveedor de asistencia vial y de salud a través de PAQ Wallet.
Tu trabajo es analizar las necesidades del usuario, recomendar planes Y comparar planes cuando se solicite.

{MAWDY_PLANS_CONTEXT}

INSTRUCCIONES:
1. Analiza la consulta del usuario
2. Si el usuario pide COMPARAR planes (ej: "compara Vial vs Médica", "diferencia entre Inclusión y Opcional"):
   - Proporciona una comparación detallada
   - Usa el campo "is_comparison" = true
   - Incluye los planes comparados en "compared_plans"
   - Lista las diferencias clave en "comparison_details"
3. Si el usuario pide una RECOMENDACIÓN basada en sus necesidades:
   - Recomienda el plan más adecuado
   - Usa el campo "is_comparison" = false
4. Menciona servicios específicos relevantes
5. Responde SIEMPRE en español
6. Sé conciso pero informativo (máximo 300 palabras)
7. Devuelve la respuesta en formato JSON con esta estructura:

Para COMPARACIONES:
{{
    "is_comparison": true,
    "compared_plans": ["Plan 1", "Plan 2"],
    "comparison_details": [
        {{"aspect": "Precio", "plan1": "Q36.88/mes", "plan2": "Q38.93/mes", "winner": "Plan 1"}},
        {{"aspect": "Servicios", "plan1": "13 servicios", "plan2": "13 servicios", "winner": "Empate"}},
        {{"aspect": "Requisitos", "plan1": "Usuario PAQ Wallet", "plan2": "Sin requisitos", "winner": "Depende"}}
    ],
    "recommendation": "Plan recomendado basado en la comparación",
    "message": "Resumen de la comparación en lenguaje amigable",
    "key_differences": ["Diferencia 1", "Diferencia 2", "Diferencia 3"]
}}

Para RECOMENDACIONES:
{{
    "is_comparison": false,
    "recommended_plan": "Asistencia Vial (Inclusión)" | "Asistencia Vial (Opcional)" | "Asistencia Médica (Inclusión)" | "Asistencia Médica (Opcional)" | "Combo",
    "confidence": "alta" | "media" | "baja",
    "reason": "Explicación breve de por qué este plan es ideal",
    "key_services": ["Servicio 1", "Servicio 2", "Servicio 3"],
    "message": "Mensaje amigable para el usuario explicando la recomendación",
    "price_monthly": "Q36.88",
    "price_yearly": "Q442.56"
}}"""

        user_message = f"Necesidades del usuario: {prompt}"

        # Call Anthropic API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": user_message}
            ],
            system=system_prompt
        )

        # Parse response
        response_text = message.content[0].text

        # Try to parse as JSON
        try:
            # Extract JSON from response (in case there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(response_text)

            return Response({
                'success': True,
                'recommendation': result
            })

        except json.JSONDecodeError:
            # If JSON parsing fails, return text response
            return Response({
                'success': True,
                'recommendation': {
                    'recommended_plan': 'Combo',
                    'confidence': 'media',
                    'reason': 'Basado en tu consulta, te recomendamos revisar nuestros planes.',
                    'key_services': [],
                    'message': response_text
                }
            })

    except ImportError:
        logger.warning('Anthropic package not installed')
        return Response({
            'success': True,
            'recommendation': {
                'recommended_plan': 'Combo',
                'confidence': 'baja',
                'reason': 'Servicio de IA no disponible temporalmente.',
                'key_services': ['Grúa del Vehículo', 'Consulta Médica', 'Ambulancia'],
                'message': 'Te recomendamos el Plan Combo que incluye protección vial y de salud para ti y tu familia.'
            }
        })

    except Exception as e:
        logger.error(f'AI plan suggestion error: {str(e)}')
        return Response({
            'success': True,
            'recommendation': {
                'recommended_plan': 'Combo',
                'confidence': 'baja',
                'reason': 'Error al procesar tu consulta.',
                'key_services': ['Grúa del Vehículo', 'Consulta Médica', 'Ambulancia'],
                'message': 'Te recomendamos el Plan Combo que ofrece protección integral para vehículo y salud.'
            }
        })


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Service Categories (Read-only for users)"""

    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        """Override list to wrap response in expected format"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'categories': serializer.data})


class ServicePlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Service Plans"""

    queryset = ServicePlan.objects.filter(is_active=True)
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price_monthly', 'price_yearly', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ServicePlanListSerializer
        return ServicePlanSerializer

    def list(self, request, *args, **kwargs):
        """Override list to add test user special pricing"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        # Check if this is the test user (configurable phone)
        is_test_user = False
        if request.user.is_authenticated and request.user.phone_number:
            # Normalize phone number (remove spaces, dashes, +502 prefix)
            user_phone = request.user.phone_number.replace(' ', '').replace('-', '').replace('+502', '')
            is_test_user = user_phone == getattr(settings, 'PAQ_TEST_PHONE', '30082653')

        # Modify data to add test user pricing
        data = serializer.data
        if is_test_user:
            for plan in data:
                plan['test_user_discount'] = True
                plan['discounted_price'] = 5.00  # Q5.00 special pricing

        return Response({'plans': data})

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured service plans"""
        featured_plans = self.queryset.filter(is_featured=True)
        serializer = self.get_serializer(featured_plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_type>[^/.]+)')
    def by_category(self, request, category_type=None):
        """Get service plans by category type"""
        plans = self.queryset.filter(category__category_type=category_type)
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)


class UserServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for User Services"""

    queryset = UserService.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['plan__name', 'status']
    ordering_fields = ['created_at', 'start_date', 'end_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserServiceCreateSerializer
        return UserServiceSerializer

    def get_queryset(self):
        """Filter user services based on user role"""
        user = self.request.user

        if user.is_admin:
            return self.queryset.all()
        else:
            return self.queryset.filter(user=user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get user's active services"""
        active_services = self.get_queryset().filter(status=UserService.Status.ACTIVE)
        serializer = self.get_serializer(active_services, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my')
    def my_subscriptions(self, request):
        """Get current user's subscriptions"""
        from datetime import date

        subscriptions = self.get_queryset().filter(user=request.user).order_by('-created_at')

        # Add extra fields for frontend
        data = []
        for sub in subscriptions:
            days_remaining = (sub.end_date - date.today()).days if sub.end_date else 0
            data.append({
                'id': sub.id,
                'plan_name': sub.plan.name,
                'plan_id': sub.plan.id,
                'category': sub.plan.category.name,
                'plan_category': sub.plan.category.category_type,
                'plan_price': float(sub.plan.price_monthly),
                'status': sub.status,
                'start_date': sub.start_date,
                'end_date': sub.end_date,
                'days_remaining': days_remaining,
                'auto_renew': sub.auto_renew,
                'requests_this_month': sub.requests_this_month,
                'max_requests': sub.plan.max_requests_per_month,
                'created_at': sub.created_at
            })

        return Response({'subscriptions': data})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a user service"""
        user_service = self.get_object()
        user_service.status = UserService.Status.CANCELLED
        user_service.end_date = timezone.now().date()
        user_service.save()
        logger.info(f'User {request.user.email} cancelled service {user_service.id}')
        return Response({'message': 'Service cancelled successfully'})

    def destroy(self, request, *args, **kwargs):
        """
        Delete a user service subscription.
        Only the owner or admin can delete.
        """
        user_service = self.get_object()

        # Verify ownership (get_queryset already filters, but double-check)
        if not request.user.is_admin and user_service.user != request.user:
            return Response(
                {'error': 'No tienes permiso para eliminar este servicio'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Log the deletion
        logger.info(
            f'User {request.user.email} deleted subscription {user_service.id} '
            f'(plan: {user_service.plan.name})'
        )

        # Mark as cancelled before deleting (for audit trail)
        user_service.status = UserService.Status.CANCELLED
        user_service.save()

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='purchase')
    def purchase(self, request):
        """
        Purchase subscription with standard card payment.
        For demo/development: Creates subscription directly.
        In production: Would integrate with Stripe or other payment gateway.
        """
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')

        if not plan_id:
            return Response(
                {'error': 'plan_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = ServicePlan.objects.get(id=plan_id, is_active=True)
        except ServicePlan.DoesNotExist:
            return Response(
                {'error': 'Plan no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate dates
        start_date = timezone.now().date()
        duration_days = 365 if billing_cycle == 'yearly' else 30
        end_date = start_date + timedelta(days=duration_days)

        # For demo: Create subscription directly
        # In production: Integrate with Stripe/payment gateway here
        user_service = UserService.objects.create(
            user=request.user,
            plan=plan,
            status=UserService.Status.ACTIVE,
            start_date=start_date,
            end_date=end_date,
            next_renewal_date=end_date,
            auto_renew=False
        )

        logger.info(
            f'Subscription created via card payment: '
            f'user={request.user.email}, plan={plan.name}, billing={billing_cycle}'
        )

        serializer = UserServiceSerializer(user_service)
        return Response({
            'success': True,
            'message': '¡Suscripción activada exitosamente!',
            'subscription': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='purchase-with-paq')
    def purchase_with_paq(self, request):
        """
        Initiate PAQ payment for subscription purchase
        Step 1: Generate PAYPAQ token and send SMS to customer
        """
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')  # monthly or yearly
        phone_number = request.data.get('phone_number')

        if not plan_id or not phone_number:
            return Response(
                {'error': 'plan_id y phone_number son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = ServicePlan.objects.get(id=plan_id, is_active=True)
        except ServicePlan.DoesNotExist:
            return Response(
                {'error': 'Plan no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if this is the test user (configurable phone)
        is_test_user = False
        if request.user.is_authenticated and request.user.phone_number:
            # Normalize phone number (remove spaces, dashes, +502 prefix)
            user_phone = request.user.phone_number.replace(' ', '').replace('-', '').replace('+502', '')
            is_test_user = user_phone == getattr(settings, 'PAQ_TEST_PHONE', '30082653')

        # Get price based on billing cycle
        if billing_cycle == 'yearly':
            amount = plan.price_yearly or plan.price_monthly * 12
            duration_days = 365
        else:
            amount = plan.price_monthly
            duration_days = 30

        # Apply test user special pricing (configurable, default Q5.00)
        if is_test_user:
            amount = getattr(settings, 'PAQ_TEST_PRICE', Decimal('5.00'))
            logger.info(f'Test user pricing applied: Q{amount} for phone {phone_number}')

        # Generate PAYPAQ token using PAQ API (emite_token)
        reference = f'SUB-{request.user.id}-{plan.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}'

        emit_result = PAQPaymentService.emit_token(
            phone_number=phone_number,
            amount=amount,
            reference=reference,
            description=f'Suscripcion {plan.name} - SegurifAI',
            customer_name=f'{request.user.first_name} {request.user.last_name}'.strip(),
            customer_email=request.user.email,
            validity_hours=24
        )

        if not emit_result.get('success'):
            logger.error(f'PAQ emite_token failed: {emit_result}')
            return Response(
                {'error': emit_result.get('error', 'Error al generar código PAYPAQ')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Return all data needed for confirmation step (stateless approach for JWT)
        return Response({
            'success': True,
            'message': 'Código PAYPAQ enviado a tu teléfono por SMS',
            'transaction_id': emit_result.get('transaction_id'),
            'amount': float(amount),
            'plan_name': plan.name,
            'phone_last4': emit_result.get('phone_last4'),
            # Include data needed for confirmation step (frontend stores this)
            'pending_data': {
                'plan_id': plan.id,
                'billing_cycle': billing_cycle,
                'amount': str(amount),
                'duration_days': duration_days,
                'reference': reference
            }
        })

    @action(detail=False, methods=['post'], url_path='confirm-paq-payment')
    def confirm_paq_payment(self, request):
        """
        Confirm PAQ payment with PAYPAQ code
        Step 2: Process payment using PAQ-GO with the code received via SMS
        """
        paypaq_code = request.data.get('paypaq_code') or request.data.get('otp_token')  # Support both field names
        phone_number = request.data.get('phone_number')

        # Get pending data from request (stateless approach for JWT)
        pending = request.data.get('pending_data')

        if not paypaq_code or not phone_number:
            return Response(
                {'error': 'paypaq_code y phone_number son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not pending or not pending.get('plan_id'):
            return Response(
                {'error': 'Datos de suscripción no encontrados. Inicia el proceso nuevamente.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process payment with PAQ-GO
        payment_result = PAQPaymentService.process_payment(
            token_code=paypaq_code,
            phone_number=phone_number
        )

        if not payment_result.get('success'):
            logger.error(f'PAQ-GO payment failed: {payment_result}')
            return Response(
                {'error': payment_result.get('error', 'Código PAYPAQ inválido o expirado')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Payment successful - create subscription
        try:
            plan = ServicePlan.objects.get(id=pending['plan_id'])

            # Calculate dates
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=pending['duration_days'])

            # Create user service
            user_service = UserService.objects.create(
                user=request.user,
                plan=plan,
                status=UserService.Status.ACTIVE,
                start_date=start_date,
                end_date=end_date,
                next_renewal_date=end_date,
                auto_renew=False
            )

            # Record wallet transaction for auditing/testing
            try:
                from apps.paq_wallet.models import WalletTransaction
                WalletTransaction.objects.create(
                    user=request.user,
                    transaction_type=WalletTransaction.TransactionType.PAYMENT,
                    amount=Decimal(str(pending.get('amount'))),
                    currency='GTQ',
                    reference_number=pending.get('reference', f'SUB-{request.user.id}-{plan.id}'),
                    external_transaction_id=payment_result.get('transaction_id') or '',
                    user_service=user_service,
                    status=WalletTransaction.Status.COMPLETED,
                    status_message='PAQ-GO payment success',
                    metadata={
                        'test_mode': getattr(settings, 'PAQ_TEST_MODE', False),
                        'phone': phone_number,
                        'pending_data': pending
                    }
                )
            except Exception as tx_err:
                logger.warning(f'Could not record wallet transaction: {tx_err}')

            logger.info(
                f'Subscription created via PAQ-GO payment: '
                f'user={request.user.email}, plan={plan.name}, '
                f'amount={pending["amount"]}, paq_transaction={payment_result.get("transaction_id")}'
            )

            serializer = UserServiceSerializer(user_service)
            return Response({
                'success': True,
                'message': '¡Pago exitoso! Tu suscripción está activa.',
                'subscription': serializer.data,
                'paq_transaction_id': payment_result.get('transaction_id'),
                'paq_authorization': payment_result.get('authorization')
            })

        except Exception as e:
            logger.error(f'Error creating subscription after PAQ-GO payment: {str(e)}')
            return Response(
                {'error': 'Pago procesado pero hubo un error activando la suscripción. Contacta soporte.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
