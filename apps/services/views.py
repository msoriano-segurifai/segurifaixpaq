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

# MAWDY Plan Information for AI Context
MAWDY_PLANS_CONTEXT = """
MAWDY ofrece dos planes de asistencia en Guatemala:

## Plan Drive (Asistencia Vial) - Q24.41/mes (Q292.86/año)
Ideal para propietarios de vehículos que necesitan asistencia en carretera.

Servicios incluidos:
- Grúa del Vehículo (3/año, Q1,163 de cobertura) - Por accidente o falla mecánica
- Abasto de Combustible (Ilimitado) - 1 galón de emergencia
- Cambio de Neumáticos (3/año, Q1,163) - Instalación de llanta de repuesto
- Paso de Corriente (Ilimitado) - Servicio de arranque de batería
- Cerrajería Vehicular (Ilimitado) - Apertura de vehículo 24/7
- Ambulancia por Accidente (1/año, Q775) - Traslado médico de emergencia
- Conductor Profesional (1/año, Q465) - Por enfermedad o embriaguez
- Taxi al Aeropuerto (1/año, Q465) - Por viaje al extranjero
- Asistencia Legal Telefónica (1/año, Q1,550) - Asesoría legal por accidente
- Apoyo Económico Emergencia (1/año, Q7,750) - Pago directo al hospital
- Rayos X (1/año, Q2,325) - Servicio de radiografía
- Descuentos en Red de Proveedores (Hasta 20%)
- Asistente Cotización de Repuestos
- Asistente Referencias Médicas

## Plan Health (Asistencia Salud) - Q22.48/mes (Q269.70/año)
Ideal para familias que buscan cobertura de salud preventiva y de emergencia.

Servicios incluidos:
- Orientación Médica Telefónica (Ilimitado) - Consulta médica 24/7
- Conexión con Especialistas (Ilimitado) - Referencias a médicos de la red
- Consulta Presencial (3/año, Q1,163) - Médico general, ginecólogo o pediatra
- Medicamentos a Domicilio (Ilimitado) - Coordinación de envío
- Cuidados Post-Operatorios (1/año, Q775) - Enfermera a domicilio
- Artículos de Aseo (1/año, Q775) - Por hospitalización
- Exámenes de Laboratorio Básicos (2/año, Q775) - Heces, orina, hematología
- Exámenes Especializados (2/año, Q775) - Papanicolau, mamografía, antígeno
- Nutricionista Video (4/año, Q1,163) - Video consulta familiar
- Psicología Video (4/año, Q1,163) - Video consulta familiar
- Mensajería Hospitalización (2/año, Q465) - Por emergencia
- Taxi Familiar (2/año, Q775) - Por hospitalización del titular (15km)
- Ambulancia por Accidente (2/año, Q1,163) - Traslado del titular
- Taxi Post-Alta (1/año, Q775) - Traslado al domicilio tras hospitalización

## Combo (Drive + Health)
Para protección integral: vehículo y salud familiar. Combina todos los beneficios de ambos planes con un descuento especial.
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
        system_prompt = f"""Eres un asistente experto de MAWDY, la empresa líder de asistencia vial y de salud en Guatemala.
Tu trabajo es analizar las necesidades del usuario y recomendar el mejor plan.

{MAWDY_PLANS_CONTEXT}

INSTRUCCIONES:
1. Analiza las necesidades del usuario
2. Recomienda el plan más adecuado (Drive, Health, o Combo)
3. Explica brevemente por qué ese plan es ideal para sus necesidades
4. Menciona 2-3 servicios específicos del plan que serían más útiles para el usuario
5. Responde SIEMPRE en español
6. Sé conciso pero informativo (máximo 200 palabras)
7. Devuelve la respuesta en formato JSON con esta estructura:
{{
    "recommended_plan": "Drive" | "Health" | "Combo",
    "confidence": "alta" | "media" | "baja",
    "reason": "Explicación breve de por qué este plan es ideal",
    "key_services": ["Servicio 1", "Servicio 2", "Servicio 3"],
    "message": "Mensaje amigable para el usuario explicando la recomendación"
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
