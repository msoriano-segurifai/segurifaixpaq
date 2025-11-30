"""
Views for Assistance Document Upload and AI Review
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import AssistanceRequest
from .documents import AssistanceDocument, DocumentReviewService, REQUIRED_DOCUMENTS
from .document_serializers import (
    AssistanceDocumentSerializer,
    DocumentUploadSerializer,
    DocumentReviewResultSerializer,
    DocumentStatusSerializer,
    ManualReviewSerializer,
    RequiredDocumentSerializer
)
from apps.users.permissions import IsAdmin


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Upload a document for an assistance request.
    Document will be automatically reviewed by AI.

    POST /api/assistance/documents/upload/

    Form Data:
    - request_id: ID of the assistance request
    - document_type: Type of document (PHOTO_VEHICLE, PHOTO_DAMAGE, etc.)
    - file: The document file
    """
    serializer = DocumentUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Get the assistance request
    assistance_request = get_object_or_404(
        AssistanceRequest,
        id=serializer.validated_data['request_id']
    )

    # Check user has access to this request
    user = request.user
    if not user.is_admin and assistance_request.user != user:
        return Response(
            {'error': 'No tiene permiso para subir documentos a esta solicitud'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get file info
    uploaded_file = serializer.validated_data['file']
    original_filename = uploaded_file.name
    file_size = uploaded_file.size
    mime_type = uploaded_file.content_type or ''

    # Create document record
    document = AssistanceDocument.objects.create(
        request=assistance_request,
        document_type=serializer.validated_data['document_type'],
        file=uploaded_file,
        original_filename=original_filename,
        file_size=file_size,
        mime_type=mime_type,
        review_status=AssistanceDocument.ReviewStatus.REVIEWING
    )

    # Perform AI review
    review_result = DocumentReviewService.review_document(document)

    # Update document with review results
    document.review_status = review_result['status']
    document.ai_confidence_score = review_result['confidence']
    document.ai_review_notes = review_result['notes']
    document.ai_detected_issues = review_result['issues']
    document.reviewed_at = timezone.now()
    document.save()

    # Prepare response
    doc_serializer = AssistanceDocumentSerializer(document)

    return Response({
        'success': True,
        'message': 'Documento subido y revisado',
        'document': doc_serializer.data,
        'review': {
            'status': review_result['status'],
            'confidence': review_result['confidence'],
            'issues': review_result['issues'],
            'notes': review_result['notes']
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_request_documents(request, request_id):
    """
    Get all documents for an assistance request.

    GET /api/assistance/documents/<request_id>/
    """
    assistance_request = get_object_or_404(AssistanceRequest, id=request_id)

    # Check user has access
    user = request.user
    if not user.is_admin and assistance_request.user != user:
        return Response(
            {'error': 'No tiene permiso para ver estos documentos'},
            status=status.HTTP_403_FORBIDDEN
        )

    documents = assistance_request.ai_documents.all()
    serializer = AssistanceDocumentSerializer(documents, many=True)

    return Response({
        'request_id': request_id,
        'request_number': assistance_request.request_number,
        'documents': serializer.data,
        'count': documents.count()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_required_documents(request, request_id):
    """
    Get list of required documents for an assistance request,
    showing which are uploaded and which are still needed.

    GET /api/assistance/documents/<request_id>/required/
    """
    assistance_request = get_object_or_404(AssistanceRequest, id=request_id)

    # Check user has access
    user = request.user
    if not user.is_admin and assistance_request.user != user:
        return Response(
            {'error': 'No tiene permiso para ver esta informacion'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get assistance type
    if assistance_request.service_category:
        assistance_type = assistance_request.service_category.category_type
    else:
        assistance_type = 'ROADSIDE'

    required_docs = REQUIRED_DOCUMENTS.get(assistance_type, [])

    # Get uploaded documents
    uploaded_docs = {
        doc.document_type: doc
        for doc in assistance_request.ai_documents.all()
    }

    # Build response with status for each required document
    result = []
    for doc_info in required_docs:
        doc_type = doc_info['type']
        uploaded_doc = uploaded_docs.get(doc_type)

        result.append({
            'type': doc_type,
            'required': doc_info['required'],
            'description': doc_info['description'],
            'uploaded': uploaded_doc is not None,
            'approved': uploaded_doc.review_status == AssistanceDocument.ReviewStatus.APPROVED if uploaded_doc else False,
            'document_id': uploaded_doc.id if uploaded_doc else None,
            'review_status': uploaded_doc.review_status if uploaded_doc else None,
            'review_notes': uploaded_doc.ai_review_notes if uploaded_doc else None
        })

    return Response({
        'request_id': request_id,
        'assistance_type': assistance_type,
        'documents': result
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_documents_complete(request, request_id):
    """
    Check if all required documents are uploaded and approved.

    GET /api/assistance/documents/<request_id>/status/
    """
    assistance_request = get_object_or_404(AssistanceRequest, id=request_id)

    # Check user has access
    user = request.user
    if not user.is_admin and assistance_request.user != user:
        return Response(
            {'error': 'No tiene permiso para ver esta informacion'},
            status=status.HTTP_403_FORBIDDEN
        )

    status_result = DocumentReviewService.check_documents_complete(assistance_request)

    return Response({
        'request_id': request_id,
        **status_result
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def manual_review(request, document_id):
    """
    Manually review a document (admin only).

    POST /api/assistance/documents/<document_id>/review/

    Body:
    {
        "status": "APPROVED" | "REJECTED" | "NEEDS_RESUBMIT",
        "notes": "Optional review notes"
    }
    """
    document = get_object_or_404(AssistanceDocument, id=document_id)

    serializer = ManualReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Update document
    document.review_status = serializer.validated_data['status']
    if serializer.validated_data.get('notes'):
        document.ai_review_notes += f'\n\nRevision manual: {serializer.validated_data["notes"]}'
    document.reviewed_at = timezone.now()
    document.reviewed_by = request.user
    document.save()

    doc_serializer = AssistanceDocumentSerializer(document)

    return Response({
        'success': True,
        'message': 'Documento revisado manualmente',
        'document': doc_serializer.data
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    """
    Delete a document.

    DELETE /api/assistance/documents/<document_id>/delete/
    """
    document = get_object_or_404(AssistanceDocument, id=document_id)

    # Check user has access
    user = request.user
    if not user.is_admin and document.request.user != user:
        return Response(
            {'error': 'No tiene permiso para eliminar este documento'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Can't delete approved documents
    if document.review_status == AssistanceDocument.ReviewStatus.APPROVED:
        return Response(
            {'error': 'No puede eliminar documentos aprobados'},
            status=status.HTTP_400_BAD_REQUEST
        )

    document_id = document.id
    document.delete()

    return Response({
        'success': True,
        'message': 'Documento eliminado',
        'document_id': document_id
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_types(request):
    """
    Get list of all document types.

    GET /api/assistance/documents/types/
    """
    types = [
        {'value': choice[0], 'label': choice[1]}
        for choice in AssistanceDocument.DocumentType.choices
    ]

    return Response({
        'document_types': types
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def pending_reviews(request):
    """
    Get all documents pending review (admin only).

    GET /api/assistance/documents/pending/
    """
    pending = AssistanceDocument.objects.filter(
        review_status__in=[
            AssistanceDocument.ReviewStatus.PENDING,
            AssistanceDocument.ReviewStatus.REVIEWING,
            AssistanceDocument.ReviewStatus.NEEDS_RESUBMIT
        ]
    ).select_related('request', 'request__user').order_by('-uploaded_at')

    serializer = AssistanceDocumentSerializer(pending, many=True)

    return Response({
        'pending_documents': serializer.data,
        'count': pending.count()
    })
