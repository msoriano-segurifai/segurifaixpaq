"""
Promo Code API Views
"""
import logging
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

from .models import PromoCode, PromoCodeUsage, Campaign
from .services import PromoCodeService
from .serializers import (
    PromoCodeSerializer,
    PromoCodeCreateSerializer,
    PromoCodeUsageSerializer,
    CampaignSerializer,
    ValidateCodeSerializer
)
from apps.users.permissions import IsAdmin
from apps.services.models import ServicePlan


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_promo_code(request):
    """
    Validate a promo code before applying it.

    POST /api/promotions/validate/

    Body:
    {
        "code": "PROMO2025",
        "plan_id": 1,        (optional)
        "amount": 100.00     (optional)
    }
    """
    serializer = ValidateCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data['code']
    plan_id = serializer.validated_data.get('plan_id')
    amount = serializer.validated_data.get('amount')

    plan = None
    if plan_id:
        try:
            plan = ServicePlan.objects.get(id=plan_id)
            if not amount:
                amount = plan.price
        except ServicePlan.DoesNotExist:
            # Plan not found - continue without plan validation
            logger.warning(f'Promo code validation: Plan {plan_id} not found')

    result = PromoCodeService.validate_code(
        code=code,
        user=request.user,
        plan=plan,
        amount=Decimal(str(amount)) if amount else None
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_promo_code(request):
    """
    Apply a promo code to get discount.

    POST /api/promotions/apply/

    Body:
    {
        "code": "PROMO2025",
        "original_price": 100.00,
        "user_service_id": 1    (optional)
    }
    """
    code = request.data.get('code')
    original_price = request.data.get('original_price')
    user_service_id = request.data.get('user_service_id')

    if not code:
        return Response(
            {'error': 'code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not original_price:
        return Response(
            {'error': 'original_price is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user_service = None
    if user_service_id:
        from apps.services.models import UserService
        try:
            user_service = UserService.objects.get(id=user_service_id, user=request.user)
        except UserService.DoesNotExist:
            # User service not found - continue without linking
            logger.warning(f'Promo code apply: UserService {user_service_id} not found for user {request.user.id}')

    result = PromoCodeService.apply_code(
        code=code,
        user=request.user,
        original_price=Decimal(str(original_price)),
        user_service=user_service
    )

    if result.get('valid') is False:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_codes(request):
    """
    Get list of promo codes available to the current user.

    GET /api/promotions/available/
    """
    codes = PromoCodeService.get_available_codes_for_user(request.user)

    return Response({
        'codes': codes,
        'count': len(codes)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_usage_history(request):
    """
    Get user's promo code usage history.

    GET /api/promotions/my-usage/
    """
    usages = PromoCodeUsage.objects.filter(
        user=request.user
    ).select_related('promo_code').order_by('-used_at')

    serializer = PromoCodeUsageSerializer(usages, many=True)

    return Response({
        'usages': serializer.data,
        'count': usages.count(),
        'total_saved': sum(float(u.discount_amount) for u in usages)
    })


class PromoCodeViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing promo codes.

    list: GET /api/promotions/codes/
    create: POST /api/promotions/codes/
    retrieve: GET /api/promotions/codes/{id}/
    update: PUT /api/promotions/codes/{id}/
    delete: DELETE /api/promotions/codes/{id}/
    """
    queryset = PromoCode.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return PromoCodeCreateSerializer
        return PromoCodeSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """Get usage statistics for a promo code."""
        promo = self.get_object()
        usages = promo.usages.all()

        return Response({
            'code': promo.code,
            'total_uses': promo.current_uses,
            'max_uses': promo.max_uses,
            'remaining_uses': (promo.max_uses - promo.current_uses) if promo.max_uses else 'Unlimited',
            'total_discount_given': sum(float(u.discount_amount) for u in usages),
            'unique_users': usages.values('user').distinct().count(),
            'recent_usages': PromoCodeUsageSerializer(usages[:10], many=True).data
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a promo code."""
        promo = self.get_object()
        promo.status = PromoCode.Status.INACTIVE
        promo.save()

        return Response({
            'success': True,
            'message': f'Codigo {promo.code} desactivado'
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a promo code."""
        promo = self.get_object()
        promo.status = PromoCode.Status.ACTIVE
        promo.save()

        return Response({
            'success': True,
            'message': f'Codigo {promo.code} activado'
        })


class CampaignViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing campaigns.
    """
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get campaign statistics."""
        campaign = self.get_object()
        promo_codes = campaign.promo_codes.all()

        total_uses = sum(p.current_uses for p in promo_codes)
        all_usages = PromoCodeUsage.objects.filter(promo_code__in=promo_codes)
        total_discount = sum(float(u.discount_amount) for u in all_usages)

        return Response({
            'campaign': campaign.name,
            'total_codes': promo_codes.count(),
            'total_uses': total_uses,
            'total_discount_given': total_discount,
            'unique_users': all_usages.values('user').distinct().count(),
            'codes': [
                {
                    'code': p.code,
                    'uses': p.current_uses,
                    'status': p.status
                }
                for p in promo_codes
            ]
        })
