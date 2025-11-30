from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Provider, ProviderReview
from .serializers import (
    ProviderSerializer, ProviderListSerializer, ProviderDetailSerializer,
    ProviderReviewSerializer, ProviderReviewCreateSerializer
)
from apps.users.permissions import IsAdmin, CanAccessProviderData


class ProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for Providers"""

    queryset = Provider.objects.filter(status=Provider.Status.ACTIVE)
    permission_classes = [CanAccessProviderData]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company_name', 'city', 'state']
    ordering_fields = ['rating', 'total_completed', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProviderListSerializer
        elif self.action == 'retrieve':
            return ProviderDetailSerializer
        return ProviderSerializer

    def get_queryset(self):
        """Filter providers based on user role and query params"""
        queryset = self.queryset
        user = self.request.user

        # Admins see all providers
        if user.is_authenticated and user.is_admin:
            queryset = Provider.objects.all()
        # Providers see only themselves
        elif user.is_authenticated and user.is_provider:
            queryset = Provider.objects.filter(user=user)

        # Filter by service category if provided
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(service_categories__category_type=category)

        # Filter by availability
        available = self.request.query_params.get('available', None)
        if available:
            queryset = queryset.filter(is_available=True)

        return queryset.distinct()

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available providers"""
        available_providers = self.queryset.filter(is_available=True)
        serializer = self.get_serializer(available_providers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """Toggle provider availability"""
        provider = self.get_object()
        provider.is_available = not provider.is_available
        provider.save()
        return Response({
            'message': 'Availability updated',
            'is_available': provider.is_available
        })


class ProviderReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Provider Reviews"""

    queryset = ProviderReview.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ProviderReviewCreateSerializer
        return ProviderReviewSerializer

    def get_queryset(self):
        """Filter reviews by provider if specified"""
        queryset = self.queryset
        provider_id = self.request.query_params.get('provider', None)
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        return queryset
