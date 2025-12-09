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

# SegurifAI Plan Information for AI Context - December 2025
# All prices and limits in GTQ (Quetzales guatemaltecos)
MAWDY_PLANS_CONTEXT = """
SegurifAI ofrece 3 planes de asistencia en Guatemala a través de PAQ Wallet:

=== PROTEGE TU TARJETA (PRF - Protección de Tarjeta) ===
Precio: Q34.99/mes (Q419.88/año)
Incluye Seguro de Muerte Accidental: Q3,000

SERVICIOS:
- Tarjetas Perdidas o Robadas (48 horas para notificar)
- Protección contra Clonación de Tarjeta
- Falsificación de Banda Magnética
- Cobertura Digital: Ingeniería Social
- Cobertura Digital: Phishing
- Cobertura Digital: Robo de Identidad
- Cobertura Digital: Suplantación (Spoofing)
- Cobertura Digital: Vishing
- Compras Fraudulentas por Internet
- Asistencias SegurifAI incluidas

IDEAL PARA: Personas que usan tarjetas de débito/crédito y quieren protección contra fraude digital.

=== PROTEGE TU SALUD (Asistencia Médica) ===
Precio: Q34.99/mes (Q419.88/año)
Incluye Seguro de Muerte Accidental: Q3,000

SERVICIOS (todos los límites en GTQ):
- Orientación Médica Telefónica (Ilimitado) - Consulta 24/7
- Conexión con Especialistas de la Red (Ilimitado)
- Coordinación de Medicamentos a Domicilio (Ilimitado)
- Consulta Presencial Médico/Ginecólogo/Pediatra (3/año, Q1,170)
- Cuidados Post Operatorios Enfermera (1/año, Q780)
- Artículos de Aseo por Hospitalización (1/año, Q780)
- Exámenes Lab: Heces, Orina, Hematología (2/año, Q780)
- Exámenes: Papanicoláu/Mamografía/Antígeno (2/año, Q780)
- Nutricionista Video Consulta Familiar (4/año, Q1,170)
- Psicología Video Consulta Familiar (4/año, Q1,170)
- Mensajería por Hospitalización (2/año, Q470)
- Taxi Familiar por Hospitalización (2/año, Q780)
- Ambulancia por Accidente (2/año, Q1,170)
- Taxi al Domicilio tras Alta (1/año, Q780)
- Asistencias SegurifAI incluidas

IDEAL PARA: Familias, personas con condiciones de salud, quienes valoran acceso médico y bienestar.

=== PROTEGE TU RUTA (Asistencia Vial) ===
Precio: Q39.99/mes (Q479.88/año)
Incluye Seguro de Muerte Accidental: Q3,000

SERVICIOS (todos los límites en GTQ):
- Grúa del Vehículo (3/año, Q1,170) - Por accidente o falla mecánica
- Abasto de Combustible 1 galón (3/año, Q1,170 combinado)
- Cambio de Neumáticos (3/año, Q1,170 combinado)
- Paso de Corriente (3/año, Q1,170 combinado)
- Emergencia de Cerrajería (3/año, Q1,170 combinado)
- Ambulancia por Accidente (1/año, Q780)
- Conductor Profesional (1/año, Q470) - Por enfermedad o embriaguez
- Taxi al Aeropuerto (1/año, Q470) - Por viaje al extranjero
- Asistencia Legal Telefónica (1/año, Q1,560)
- Apoyo Económico Sala Emergencia (1/año, Q7,800) - Pago directo al hospital
- Rayos X (1/año, Q2,340, hasta 20% descuento)
- Descuentos en Red de Proveedores (hasta 20%)
- Asistente Telefónico Cotización Repuestos (Incluido)
- Asistente Telefónico Referencias Médicas por Accidente (Incluido)
- Asistencias SegurifAI incluidas

IDEAL PARA: Conductores, personas que viajan frecuentemente, dueños de vehículos.

=== RESUMEN DE PRECIOS ===
| Plan                  | Mensual  | Anual     |
|-----------------------|----------|-----------|
| Protege tu Tarjeta    | Q34.99   | Q419.88   |
| Protege tu Salud      | Q34.99   | Q419.88   |
| Protege tu Ruta       | Q39.99   | Q479.88   |

NOTA: Todos los planes incluyen Seguro de Muerte Accidental Q3,000 y Asistencias SegurifAI.
Proveedor de servicios: SegurifAI Guatemala a través de PAQ Wallet.
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
        system_prompt = f"""Eres un asistente experto de SegurifAI Guatemala, proveedor de asistencia vial, médica y protección de tarjetas a través de PAQ Wallet.
Tu trabajo es analizar las necesidades del usuario, recomendar planes Y comparar planes cuando se solicite.

{MAWDY_PLANS_CONTEXT}

=== MAPEO DE NOMBRES (IMPORTANTE) ===
Los usuarios pueden usar nombres antiguos. Siempre usa los NUEVOS nombres en tus respuestas:
- "Drive", "Vial", "Asistencia Vial" → PROTEGE TU RUTA
- "Health", "Salud", "Asistencia Médica" → PROTEGE TU SALUD
- "Tarjeta", "Card", "PRF" → PROTEGE TU TARJETA

=== COMBOS Y PAQUETES ===
Los usuarios pueden suscribirse a MÚLTIPLES planes para protección completa:
- Combo Ruta + Salud: Q74.98/mes (Q39.99 + Q34.99)
- Combo Ruta + Tarjeta: Q74.98/mes (Q39.99 + Q34.99)
- Combo Salud + Tarjeta: Q69.98/mes (Q34.99 + Q34.99)
- Protección Total (3 planes): Q109.97/mes - Incluye TODOS los servicios

=== EJEMPLOS DE RECOMENDACIONES ===
- "Manejo mucho y mi carro es viejo" → PROTEGE TU RUTA (grúa, paso de corriente, cerrajería)
- "Tengo hijos pequeños" → PROTEGE TU SALUD (pediatra, psicología, medicamentos a domicilio)
- "Uso mucho mi tarjeta en internet" → PROTEGE TU TARJETA (phishing, fraude online, robo identidad)
- "Protección completa" → Recomendar Combo de 2 o 3 planes según presupuesto
- "¿Qué incluye combo?" → Explicar los paquetes disponibles

INSTRUCCIONES:
1. Analiza la consulta del usuario
2. Si el usuario pide COMPARAR planes (ej: "Drive vs Health", "Ruta vs Salud", "compara Tarjeta y Salud"):
   - Proporciona una comparación detallada
   - Usa el campo "is_comparison" = true
   - SIEMPRE usa los NUEVOS nombres de planes en "compared_plans"
   - Lista las diferencias clave en "comparison_details"
3. Si el usuario pregunta por COMBO o protección múltiple:
   - Explica las opciones de combinar planes
   - Recomienda la mejor combinación según sus necesidades
4. Si el usuario pide una RECOMENDACIÓN basada en sus necesidades:
   - Recomienda el plan más adecuado
   - Usa el campo "is_comparison" = false
5. Menciona servicios específicos relevantes a su situación
6. Responde SIEMPRE en español
7. Sé conciso pero informativo (máximo 300 palabras)
8. Devuelve la respuesta en formato JSON con esta estructura:

Para COMPARACIONES:
{{
    "is_comparison": true,
    "compared_plans": ["Plan 1", "Plan 2"],
    "comparison_details": [
        {{"aspect": "Precio", "plan1": "Q34.99/mes", "plan2": "Q39.99/mes", "winner": "Plan 1"}},
        {{"aspect": "Servicios", "plan1": "11 servicios", "plan2": "16 servicios", "winner": "Plan 2"}},
        {{"aspect": "Enfoque", "plan1": "Protección digital", "plan2": "Asistencia vial", "winner": "Depende"}}
    ],
    "recommendation": "Plan recomendado basado en la comparación",
    "message": "Resumen de la comparación en lenguaje amigable",
    "key_differences": ["Diferencia 1", "Diferencia 2", "Diferencia 3"]
}}

Para RECOMENDACIONES (plan único):
{{
    "is_comparison": false,
    "is_combo": false,
    "recommended_plan": "Protege tu Tarjeta" | "Protege tu Salud" | "Protege tu Ruta",
    "confidence": "alta" | "media" | "baja",
    "reason": "Explicación breve de por qué este plan es ideal",
    "key_services": ["Servicio 1", "Servicio 2", "Servicio 3"],
    "message": "Mensaje amigable para el usuario explicando la recomendación",
    "price_monthly": "Q34.99",
    "price_yearly": "Q419.88"
}}

Para COMBOS (múltiples planes):
{{
    "is_comparison": false,
    "is_combo": true,
    "recommended_plan": "Combo Ruta + Salud" | "Combo Ruta + Tarjeta" | "Combo Salud + Tarjeta" | "Protección Total",
    "included_plans": ["Protege tu Ruta", "Protege tu Salud"],
    "confidence": "alta" | "media" | "baja",
    "reason": "Explicación de por qué esta combinación es ideal",
    "key_services": ["Servicio de Plan 1", "Servicio de Plan 2", "Servicio adicional"],
    "message": "Mensaje amigable explicando los beneficios del combo",
    "price_monthly": "Q74.98",
    "individual_prices": ["Q39.99 (Ruta)", "Q34.99 (Salud)"]
}}"""

        user_message = f"Necesidades del usuario: {prompt}"

        # Call Anthropic API - Using Haiku for fast responses
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=600,
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
                    'recommended_plan': 'Protege tu Ruta',
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
                'recommended_plan': 'Protege tu Ruta',
                'confidence': 'baja',
                'reason': 'Servicio de IA no disponible temporalmente.',
                'key_services': ['Grúa del Vehículo (Q1,170)', 'Paso de Corriente', 'Ambulancia por Accidente'],
                'message': 'Te recomendamos Protege tu Ruta (Q39.99/mes) que incluye grúa, paso de corriente y ambulancia 24/7.'
            }
        })

    except Exception as e:
        logger.error(f'AI plan suggestion error: {str(e)}')
        return Response({
            'success': True,
            'recommendation': {
                'recommended_plan': 'Protege tu Salud',
                'confidence': 'baja',
                'reason': 'Error al procesar tu consulta.',
                'key_services': ['Orientación Médica 24/7', 'Consultas Presenciales', 'Ambulancia por Accidente'],
                'message': 'Te recomendamos revisar nuestros planes: Protege tu Tarjeta, Protege tu Salud y Protege tu Ruta.'
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
