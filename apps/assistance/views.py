from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AssistanceRequest, RequestUpdate, RequestDocument
from .serializers import (
    AssistanceRequestSerializer, AssistanceRequestListSerializer,
    AssistanceRequestCreateSerializer, AssistanceRequestUpdateSerializer,
    RequestUpdateSerializer, RequestUpdateCreateSerializer,
    RequestDocumentSerializer, RequestDocumentCreateSerializer
)
from apps.users.permissions import IsAdmin, CanCreateAssistanceRequest


class AssistanceRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for Assistance Requests"""

    queryset = AssistanceRequest.objects.all()
    permission_classes = [CanCreateAssistanceRequest]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['request_number', 'title', 'description', 'location_city']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AssistanceRequestListSerializer
        elif self.action == 'create':
            return AssistanceRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AssistanceRequestUpdateSerializer
        return AssistanceRequestSerializer

    def get_queryset(self):
        """Filter assistance requests based on user role"""
        user = self.request.user
        queryset = self.queryset

        if user.is_admin:
            # Admins see all requests
            pass
        elif user.is_provider:
            # Providers see only their assigned requests
            queryset = queryset.filter(provider__user=user)
        else:
            # Regular users see only their own requests
            queryset = queryset.filter(user=user)

        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by service category if provided
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(service_category__category_type=category)

        return queryset

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending assistance requests"""
        pending_requests = self.get_queryset().filter(status=AssistanceRequest.Status.PENDING)
        serializer = self.get_serializer(pending_requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active assistance requests"""
        active_requests = self.get_queryset().filter(
            status__in=[AssistanceRequest.Status.ASSIGNED, AssistanceRequest.Status.IN_PROGRESS]
        )
        serializer = self.get_serializer(active_requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_provider(self, request, pk=None):
        """Assign a provider to the assistance request"""
        assistance_request = self.get_object()
        provider_id = request.data.get('provider_id')

        if not provider_id:
            return Response({'error': 'provider_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.providers.models import Provider
        try:
            provider = Provider.objects.get(id=provider_id, status=Provider.Status.ACTIVE)
            assistance_request.provider = provider
            assistance_request.status = AssistanceRequest.Status.ASSIGNED
            assistance_request.save()

            # Create update
            RequestUpdate.objects.create(
                request=assistance_request,
                user=request.user,
                update_type=RequestUpdate.UpdateType.STATUS_CHANGE,
                message=f'Provider {provider.company_name} has been assigned to this request.'
            )

            return Response({'message': 'Provider assigned successfully'})
        except Provider.DoesNotExist:
            return Response({'error': 'Provider not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an assistance request"""
        assistance_request = self.get_object()
        cancellation_reason = request.data.get('reason', '')

        assistance_request.status = AssistanceRequest.Status.CANCELLED
        assistance_request.cancellation_reason = cancellation_reason
        assistance_request.save()

        return Response({'message': 'Request cancelled successfully'})


class RequestUpdateViewSet(viewsets.ModelViewSet):
    """ViewSet for Request Updates"""

    queryset = RequestUpdate.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return RequestUpdateCreateSerializer
        return RequestUpdateSerializer

    def get_queryset(self):
        """Filter updates by request if specified"""
        queryset = self.queryset
        request_id = self.request.query_params.get('request', None)
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        return queryset


class RequestDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for Request Documents"""

    queryset = RequestDocument.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return RequestDocumentCreateSerializer
        return RequestDocumentSerializer

    def get_queryset(self):
        """Filter documents by request if specified"""
        queryset = self.queryset
        request_id = self.request.query_params.get('request', None)
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        return queryset
