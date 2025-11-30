from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssistanceRequestViewSet, RequestUpdateViewSet, RequestDocumentViewSet
from .document_views import (
    upload_document,
    get_request_documents,
    get_required_documents,
    check_documents_complete,
    manual_review,
    delete_document,
    get_document_types,
    pending_reviews
)
from .tracking_views import (
    get_tracking_info,
    get_active_tracking,
    update_provider_location,
    mark_arrived,
    mark_completed,
    start_service,
    get_route_history,
    calculate_eta,
    # Public/SSO tracking
    public_tracking,
    public_tracking_simple,
    # Dispatch endpoints for MAWDY assistants
    get_available_jobs,
    accept_job,
    depart_for_job,
    get_my_active_jobs,
)
from .evidence_views import (
    get_evidence_options,
    get_evidence_status,
    get_form_template,
    create_evidence_form,
    update_evidence_form,
    submit_evidence_form,
    get_my_evidence_forms,
    get_evidence_form,
    get_pending_evidence_forms,
    review_evidence_form,
    ai_review_document,
)
from .live_tracking import (
    live_tracking,
    live_route_history,
    paq_live_tracking,
)
from .vehicle_validation import (
    validate_vehicle,
    get_pending_validations,
    approve_validation,
    reject_validation,
)
from .health_validation import (
    validate_health,
    get_pending_health_validations,
    approve_health_validation,
    reject_health_validation,
)
from .service_validation import (
    validate_service,
)

router = DefaultRouter()
router.register(r'requests', AssistanceRequestViewSet, basename='assistance-request')
router.register(r'updates', RequestUpdateViewSet, basename='request-update')
router.register(r'documents', RequestDocumentViewSet, basename='request-document')

urlpatterns = [
    path('', include(router.urls)),

    # Real-Time Tracking (delivery-app style)
    path('tracking/active/', get_active_tracking, name='active-tracking'),
    path('tracking/update-location/', update_provider_location, name='update-location'),
    path('tracking/calculate-eta/', calculate_eta, name='calculate-eta'),
    path('tracking/<int:request_id>/', get_tracking_info, name='tracking-info'),
    path('tracking/<int:request_id>/route/', get_route_history, name='route-history'),
    path('tracking/<int:request_id>/arrived/', mark_arrived, name='mark-arrived'),
    path('tracking/<int:request_id>/start/', start_service, name='start-service'),
    path('tracking/<int:request_id>/completed/', mark_completed, name='mark-completed'),

    # PAQ User Tracking (requires PAQ SSO token in X-PAQ-Token header)
    path('tracking/paq/<str:tracking_token>/', public_tracking, name='paq-tracking'),

    # Simple Public Tracking (no auth required - for testing)
    path('tracking/public/<str:tracking_token>/', public_tracking_simple, name='public-tracking'),

    # Live Tracking - Food Delivery Style (poll every 3-5 seconds)
    path('live/<int:request_id>/', live_tracking, name='live-tracking'),
    path('live/<int:request_id>/route/', live_route_history, name='live-route'),
    path('live/paq/<str:tracking_token>/', paq_live_tracking, name='paq-live-tracking'),

    # Dispatch Endpoints (MAWDY Assistants/Field Technicians)
    path('dispatch/available/', get_available_jobs, name='available-jobs'),
    path('dispatch/my-jobs/', get_my_active_jobs, name='my-active-jobs'),
    path('dispatch/<int:request_id>/accept/', accept_job, name='accept-job'),
    path('dispatch/<int:request_id>/depart/', depart_for_job, name='depart-for-job'),

    # Document Upload with AI Review
    path('docs/upload/', upload_document, name='document-upload'),
    path('docs/types/', get_document_types, name='document-types'),
    path('docs/pending/', pending_reviews, name='pending-reviews'),
    path('docs/<int:request_id>/', get_request_documents, name='request-documents'),
    path('docs/<int:request_id>/required/', get_required_documents, name='required-documents'),
    path('docs/<int:request_id>/status/', check_documents_complete, name='document-status'),
    path('docs/<int:document_id>/review/', manual_review, name='manual-review'),
    path('docs/<int:document_id>/delete/', delete_document, name='delete-document'),
    path('docs/<int:document_id>/ai-review/', ai_review_document, name='ai-review-document'),
    # Evidence Flow (unified options and status)
    path('evidence/<int:request_id>/options/', get_evidence_options, name='evidence-options'),
    path('evidence/<int:request_id>/status/', get_evidence_status, name='evidence-status'),

    # Evidence Forms (alternative to photos)
    path('evidence/template/<str:form_type>/', get_form_template, name='evidence-template'),
    path('evidence/forms/', get_my_evidence_forms, name='my-evidence-forms'),
    path('evidence/forms/create/', create_evidence_form, name='create-evidence-form'),
    path('evidence/forms/<int:form_id>/', get_evidence_form, name='get-evidence-form'),
    path('evidence/forms/<int:form_id>/update/', update_evidence_form, name='update-evidence-form'),
    path('evidence/forms/<int:form_id>/submit/', submit_evidence_form, name='submit-evidence-form'),
    path('evidence/admin/pending/', get_pending_evidence_forms, name='pending-evidence-forms'),
    path('evidence/admin/<int:form_id>/review/', review_evidence_form, name='review-evidence-form'),

    # Vehicle Validation (AI + Human Review)
    path('validate-vehicle/', validate_vehicle, name='validate-vehicle'),
    path('vehicle-validations/pending/', get_pending_validations, name='pending-validations'),
    path('vehicle-validations/<int:validation_id>/approve/', approve_validation, name='approve-validation'),
    path('vehicle-validations/<int:validation_id>/reject/', reject_validation, name='reject-validation'),

    # Health Emergency Validation (AI + Human Review)
    path('validate-health/', validate_health, name='validate-health'),
    path('health-validations/pending/', get_pending_health_validations, name='pending-health-validations'),
    path('health-validations/<int:validation_id>/approve/', approve_health_validation, name='approve-health-validation'),
    path('health-validations/<int:validation_id>/reject/', reject_health_validation, name='reject-health-validation'),

    # Generic Service Validation (AI + Human Review for all MAWDY services)
    path('validate-service/', validate_service, name='validate-service'),
]
