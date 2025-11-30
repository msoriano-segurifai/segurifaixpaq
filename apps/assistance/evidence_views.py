"""
Evidence Form API Views

Endpoints for form-based evidence submission as alternative to photos.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .ai_review import EvidenceForm, EvidenceFormReviewService, ClaudeVisionReviewService
from .models import AssistanceRequest
from .documents import AssistanceDocument
from .evidence_flow import EvidenceFlowService
from apps.users.permissions import IsAdmin


# =============================================================================
# Evidence Flow Endpoints (Unified)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_evidence_options(request, request_id):
    """
    Get available evidence submission options for a request.

    GET /api/assistance/evidence/options/<request_id>/

    Returns what evidence options are available based on assistance type:
    - Health: Form-only (no photos)
    - Roadside: Photos first, then form fallback

    Response includes the automation flow and fallback to MAWDY admin.
    """
    try:
        assistance_request = AssistanceRequest.objects.get(
            id=request_id,
            user=request.user
        )
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    options = EvidenceFlowService.get_evidence_options(assistance_request)
    return Response(options)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_evidence_status(request, request_id):
    """
    Get the overall evidence status for a request.

    GET /api/assistance/evidence/status/<request_id>/

    Returns whether evidence is complete, pending, or missing.
    """
    try:
        assistance_request = AssistanceRequest.objects.get(
            id=request_id,
            user=request.user
        )
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    status_info = EvidenceFlowService.get_request_evidence_status(assistance_request)
    return Response(status_info)


# =============================================================================
# Evidence Form Endpoints
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_form_template(request, form_type):
    """
    Get the form template/schema for a specific form type.

    GET /api/assistance/evidence/template/<form_type>/

    form_type: VEHICLE_DAMAGE, ROADSIDE_ISSUE, HEALTH_INCIDENT
    """
    form_type = form_type.upper()
    valid_types = ['VEHICLE_DAMAGE', 'ROADSIDE_ISSUE', 'HEALTH_INCIDENT', 'GENERAL']

    if form_type not in valid_types:
        return Response(
            {'error': f'Tipo de formulario no valido. Use: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    template = EvidenceFormReviewService.get_form_template(form_type)

    return Response({
        'form_type': form_type,
        'template': template
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_evidence_form(request):
    """
    Create a new evidence form for an assistance request.

    POST /api/assistance/evidence/forms/

    Body:
    {
        "request_id": 123,
        "form_type": "VEHICLE_DAMAGE",
        "incident_date": "2025-01-15T10:30:00Z",
        "incident_description": "Mi vehiculo fue golpeado...",
        "location_description": "Zona 10, frente al centro comercial...",
        "vehicle_make": "Toyota",
        "vehicle_model": "Corolla",
        ...
    }
    """
    request_id = request.data.get('request_id')

    if not request_id:
        return Response(
            {'error': 'request_id es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        assistance_request = AssistanceRequest.objects.get(
            id=request_id,
            user=request.user
        )
    except AssistanceRequest.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Create form
    form_type = request.data.get('form_type', 'GENERAL').upper()

    form = EvidenceForm.objects.create(
        request=assistance_request,
        form_type=form_type,
        incident_date=request.data.get('incident_date', timezone.now()),
        incident_description=request.data.get('incident_description', ''),
        location_description=request.data.get('location_description', ''),
        # Vehicle fields
        vehicle_make=request.data.get('vehicle_make', ''),
        vehicle_model=request.data.get('vehicle_model', ''),
        vehicle_year=request.data.get('vehicle_year'),
        vehicle_color=request.data.get('vehicle_color', ''),
        vehicle_plate=request.data.get('vehicle_plate', ''),
        damage_description=request.data.get('damage_description', ''),
        damage_location=request.data.get('damage_location', ''),
        # Health fields
        symptoms_description=request.data.get('symptoms_description', ''),
        medical_history=request.data.get('medical_history', ''),
        current_medications=request.data.get('current_medications', ''),
        allergies=request.data.get('allergies', ''),
        # Roadside fields
        issue_type=request.data.get('issue_type', ''),
        attempted_solutions=request.data.get('attempted_solutions', ''),
        # Witness
        witness_name=request.data.get('witness_name', ''),
        witness_phone=request.data.get('witness_phone', ''),
    )

    # Analyze for completeness
    analysis = EvidenceFormReviewService.analyze_form(form)

    return Response({
        'success': True,
        'form_id': form.id,
        'status': form.status,
        'analysis': analysis,
        'message': 'Formulario creado. Complete los campos requeridos antes de enviar.'
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_evidence_form(request, form_id):
    """
    Update an existing evidence form.

    PUT /api/assistance/evidence/forms/<form_id>/
    """
    try:
        form = EvidenceForm.objects.get(
            id=form_id,
            request__user=request.user
        )
    except EvidenceForm.DoesNotExist:
        return Response(
            {'error': 'Formulario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if form.status not in [EvidenceForm.Status.DRAFT, EvidenceForm.Status.NEEDS_INFO]:
        return Response(
            {'error': 'Este formulario ya fue enviado y no puede ser modificado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update fields
    updatable_fields = [
        'incident_date', 'incident_description', 'location_description',
        'vehicle_make', 'vehicle_model', 'vehicle_year', 'vehicle_color',
        'vehicle_plate', 'damage_description', 'damage_location',
        'symptoms_description', 'medical_history', 'current_medications',
        'allergies', 'issue_type', 'attempted_solutions',
        'witness_name', 'witness_phone'
    ]

    for field in updatable_fields:
        if field in request.data:
            setattr(form, field, request.data[field])

    form.save()

    # Re-analyze
    analysis = EvidenceFormReviewService.analyze_form(form)

    return Response({
        'success': True,
        'form_id': form.id,
        'status': form.status,
        'analysis': analysis
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_evidence_form(request, form_id):
    """
    Submit an evidence form for review.

    POST /api/assistance/evidence/forms/<form_id>/submit/

    Body:
    {
        "declaration_accepted": true
    }

    BUSINESS RULES:
    1. First validates form completeness
    2. Uses AI to analyze form content for consistency
    3. If AI approves with high confidence → auto-approve
    4. If AI has low confidence or detects issues → escalate to MAWDY admin
    5. MAWDY admin makes final decision (approve/reject)
    """
    try:
        form = EvidenceForm.objects.get(
            id=form_id,
            request__user=request.user
        )
    except EvidenceForm.DoesNotExist:
        return Response(
            {'error': 'Formulario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if form.status not in [EvidenceForm.Status.DRAFT, EvidenceForm.Status.NEEDS_INFO]:
        return Response(
            {'error': 'Este formulario ya fue enviado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Basic field validation first
    basic_analysis = EvidenceFormReviewService.analyze_form(form)

    if not basic_analysis['can_submit']:
        return Response({
            'success': False,
            'error': 'El formulario tiene errores que deben ser corregidos',
            'issues': basic_analysis['issues']
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check declaration
    if not request.data.get('declaration_accepted'):
        return Response(
            {'error': 'Debe aceptar la declaracion de veracidad'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Submit the form
    form.declaration_accepted = True
    form.submit()

    # Now run AI analysis for content validation
    ai_result = EvidenceFormReviewService.ai_analyze_form(form)

    # Save AI analysis results
    form.ai_analysis = ai_result.get('ai_analysis', {})
    form.ai_confidence_score = ai_result.get('confidence', 0)

    if ai_result.get('action') == 'auto_approve':
        # AI approved with high confidence
        form.status = EvidenceForm.Status.APPROVED
        form.review_notes = 'Aprobado automaticamente por IA'
        form.reviewed_at = timezone.now()
        form.save()

        return Response({
            'success': True,
            'message': 'Formulario aprobado automaticamente',
            'form_id': form.id,
            'status': form.status,
            'approval_type': 'automated',
            'confidence': ai_result.get('confidence', 0),
            'submitted_at': form.submitted_at.isoformat()
        })

    elif ai_result.get('action') == 'request_more_info':
        # AI needs more info - let user correct
        form.status = EvidenceForm.Status.NEEDS_INFO
        form.review_notes = ai_result.get('missing_info', 'Informacion incompleta')
        form.save()

        return Response({
            'success': True,
            'message': 'Se requiere informacion adicional',
            'form_id': form.id,
            'status': form.status,
            'issues': ai_result.get('issues', []),
            'submitted_at': form.submitted_at.isoformat()
        })

    else:
        # Escalate to MAWDY admin for manual review
        form.status = EvidenceForm.Status.REVIEWING
        form.review_notes = f"Escalado para revision: {ai_result.get('escalation_reason', 'Revision requerida')}"
        form.save()

        return Response({
            'success': True,
            'message': 'Formulario enviado para revision por agente MAWDY',
            'form_id': form.id,
            'status': form.status,
            'review_type': 'mawdy_admin',
            'escalation_reason': ai_result.get('escalation_reason', ''),
            'submitted_at': form.submitted_at.isoformat()
        })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_my_evidence_forms(request):
    """
    GET: List all evidence forms for the current user.
    POST: Create a new evidence form (alias for create_evidence_form).

    GET /api/assistance/evidence/forms/
    POST /api/assistance/evidence/forms/
    """
    if request.method == 'POST':
        return create_evidence_form(request)

    forms = EvidenceForm.objects.filter(
        request__user=request.user
    ).select_related('request').order_by('-created_at')

    return Response({
        'count': forms.count(),
        'forms': [
            {
                'id': f.id,
                'request_id': f.request.id,
                'request_number': f.request.request_number,
                'form_type': f.form_type,
                'status': f.status,
                'created_at': f.created_at.isoformat(),
                'submitted_at': f.submitted_at.isoformat() if f.submitted_at else None,
                'reviewed_at': f.reviewed_at.isoformat() if f.reviewed_at else None,
            }
            for f in forms
        ]
    })


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def get_evidence_form(request, form_id):
    """
    Get or update a specific evidence form.

    GET /api/assistance/evidence/forms/<form_id>/
    PUT /api/assistance/evidence/forms/<form_id>/
    """
    if request.method == 'PUT':
        return update_evidence_form(request, form_id)

    try:
        form = EvidenceForm.objects.select_related('request').get(id=form_id)

        # Check access
        if form.request.user != request.user and not request.user.is_admin:
            return Response(
                {'error': 'No tienes acceso a este formulario'},
                status=status.HTTP_403_FORBIDDEN
            )
    except EvidenceForm.DoesNotExist:
        return Response(
            {'error': 'Formulario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'id': form.id,
        'request_id': form.request.id,
        'request_number': form.request.request_number,
        'form_type': form.form_type,
        'status': form.status,
        'incident_date': form.incident_date.isoformat() if form.incident_date else None,
        'incident_description': form.incident_description,
        'location_description': form.location_description,
        'vehicle': {
            'make': form.vehicle_make,
            'model': form.vehicle_model,
            'year': form.vehicle_year,
            'color': form.vehicle_color,
            'plate': form.vehicle_plate,
        },
        'damage': {
            'location': form.damage_location,
            'description': form.damage_description,
        },
        'health': {
            'symptoms': form.symptoms_description,
            'medical_history': form.medical_history,
            'medications': form.current_medications,
            'allergies': form.allergies,
        },
        'roadside': {
            'issue_type': form.issue_type,
            'attempted_solutions': form.attempted_solutions,
        },
        'witness': {
            'name': form.witness_name,
            'phone': form.witness_phone,
        },
        'declaration_accepted': form.declaration_accepted,
        'review': {
            'status': form.status,
            'notes': form.review_notes,
            'rejection_reason': form.rejection_reason,
            'reviewed_at': form.reviewed_at.isoformat() if form.reviewed_at else None,
        },
        'created_at': form.created_at.isoformat(),
        'submitted_at': form.submitted_at.isoformat() if form.submitted_at else None,
    })


# =============================================================================
# Admin Review Endpoints
# =============================================================================

def is_mawdy_reviewer(user):
    """Check if user can review evidence forms (SegurifAI or MAWDY admin)"""
    return user.is_admin or user.is_mawdy_admin or user.role == 'MAWDY_ADMIN'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_evidence_forms(request):
    """
    Get all pending evidence forms for admin review.

    GET /api/assistance/evidence/admin/pending/

    Accessible by SegurifAI Admin or MAWDY Admin team members.
    """
    if not is_mawdy_reviewer(request.user):
        return Response(
            {'error': 'Solo administradores pueden revisar formularios'},
            status=status.HTTP_403_FORBIDDEN
        )

    forms = EvidenceForm.objects.filter(
        status__in=[EvidenceForm.Status.SUBMITTED, EvidenceForm.Status.REVIEWING]
    ).select_related('request', 'request__user').order_by('submitted_at')

    return Response({
        'count': forms.count(),
        'forms': [
            {
                'id': f.id,
                'request_id': f.request.id,
                'request_number': f.request.request_number,
                'form_type': f.form_type,
                'status': f.status,
                'user_email': f.request.user.email if f.request.user else None,
                'submitted_at': f.submitted_at.isoformat() if f.submitted_at else None,
                'incident_summary': f.incident_description[:100] if f.incident_description else '',
            }
            for f in forms
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_evidence_form(request, form_id):
    """
    Review and approve/reject an evidence form.

    POST /api/assistance/evidence/admin/<form_id>/review/

    Body:
    {
        "action": "approve" or "reject",
        "notes": "Review notes...",
        "rejection_reason": "Required if rejecting"
    }

    Accessible by SegurifAI Admin or MAWDY Admin team members.
    """
    if not is_mawdy_reviewer(request.user):
        return Response(
            {'error': 'Solo administradores pueden revisar formularios'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        form = EvidenceForm.objects.get(id=form_id)
    except EvidenceForm.DoesNotExist:
        return Response(
            {'error': 'Formulario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    action = request.data.get('action', '').lower()

    if action not in ['approve', 'reject', 'needs_info']:
        return Response(
            {'error': 'action debe ser "approve", "reject", o "needs_info"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    form.review_notes = request.data.get('notes', '')

    if action == 'approve':
        form.approve(request.user)
        message = 'Formulario aprobado'
    elif action == 'reject':
        reason = request.data.get('rejection_reason', '')
        if not reason:
            return Response(
                {'error': 'rejection_reason es requerido para rechazar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        form.reject(request.user, reason)
        message = 'Formulario rechazado'
    else:  # needs_info
        form.status = EvidenceForm.Status.NEEDS_INFO
        form.reviewed_by = request.user
        form.reviewed_at = timezone.now()
        form.save()
        message = 'Solicitada mas informacion'

    return Response({
        'success': True,
        'message': message,
        'form_id': form.id,
        'status': form.status
    })


# =============================================================================
# AI Document Review Endpoint
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_review_document(request, document_id):
    """
    Trigger AI review for a document.

    POST /api/assistance/docs/<document_id>/ai-review/
    """
    try:
        document = AssistanceDocument.objects.get(id=document_id)

        # Check access
        if document.request.user != request.user and not request.user.is_admin:
            return Response(
                {'error': 'No tienes acceso a este documento'},
                status=status.HTTP_403_FORBIDDEN
            )
    except AssistanceDocument.DoesNotExist:
        return Response(
            {'error': 'Documento no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Run AI review
    result = ClaudeVisionReviewService.review_document(document)

    # Update document
    document.review_status = result['status']
    document.ai_confidence_score = result['confidence']
    document.ai_review_notes = result['notes']
    document.ai_detected_issues = result['issues']
    document.reviewed_at = timezone.now()
    document.save()

    return Response({
        'success': True,
        'document_id': document.id,
        'review': {
            'status': result['status'],
            'confidence': result['confidence'],
            'notes': result['notes'],
            'issues': result['issues'],
        }
    })
