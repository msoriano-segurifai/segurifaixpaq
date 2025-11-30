"""
Organization Admin Management Views

Endpoints for managing team accounts:
- SegurifAI Admin: Can create/manage all accounts, view all reports
- MAWDY Admin: Can create MAWDY field tech and admin accounts
- PAQ Admin: Can create PAQ admin accounts
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


# =============================================================================
# SegurifAI Admin Endpoints (Super Admin - can manage everything)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def segurifai_list_team(request):
    """
    List all SegurifAI team members.

    GET /api/admin/segurifai/team/

    Only accessible by SegurifAI Admin.
    """
    if not request.user.is_admin:
        return Response(
            {'error': 'Solo administradores de SegurifAI pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    team = User.objects.filter(
        role__in=[User.Role.ADMIN, User.Role.SEGURIFAI_TEAM]
    ).order_by('role', 'email')

    return Response({
        'count': team.count(),
        'team': [
            {
                'id': u.id,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'role': u.role,
                'is_active': u.is_active,
                'date_joined': u.date_joined.isoformat()
            }
            for u in team
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def segurifai_create_team_member(request):
    """
    Create a new SegurifAI team member.

    POST /api/admin/segurifai/team/create/

    Body:
    {
        "email": "team@segurifai.gt",
        "password": "SecurePassword123!",
        "first_name": "Juan",
        "last_name": "Perez",
        "role": "SEGURIFAI_TEAM"  // or "ADMIN" for super admin
    }

    Only accessible by SegurifAI Admin.
    """
    if not request.user.is_admin:
        return Response(
            {'error': 'Solo administradores de SegurifAI pueden crear cuentas'},
            status=status.HTTP_403_FORBIDDEN
        )

    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    role = request.data.get('role', User.Role.SEGURIFAI_TEAM)

    if not email or not password:
        return Response(
            {'error': 'email y password son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate role is valid for SegurifAI
    if role not in [User.Role.ADMIN, User.Role.SEGURIFAI_TEAM]:
        return Response(
            {'error': 'role debe ser ADMIN o SEGURIFAI_TEAM'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Este email ya está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate password
    try:
        validate_password(password)
    except ValidationError as e:
        return Response(
            {'error': 'Contraseña inválida', 'details': list(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role
    )

    return Response({
        'success': True,
        'message': f'Cuenta de equipo SegurifAI creada exitosamente',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def segurifai_list_all_admins(request):
    """
    List all admin accounts across all organizations.

    GET /api/admin/segurifai/all-admins/

    Only accessible by SegurifAI Admin (super admin view).
    """
    if not request.user.is_admin:
        return Response(
            {'error': 'Solo administradores de SegurifAI pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    admin_roles = [
        User.Role.ADMIN, User.Role.SEGURIFAI_TEAM,
        User.Role.MAWDY_ADMIN, User.Role.PAQ_ADMIN
    ]

    admins = User.objects.filter(role__in=admin_roles).order_by('role', 'email')

    return Response({
        'count': admins.count(),
        'admins': [
            {
                'id': u.id,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'role': u.role,
                'role_display': u.get_role_display(),
                'is_active': u.is_active,
                'date_joined': u.date_joined.isoformat()
            }
            for u in admins
        ]
    })


# =============================================================================
# MAWDY Admin Endpoints
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mawdy_list_team(request):
    """
    List all MAWDY team members.

    GET /api/admin/mawdy/team/

    Accessible by MAWDY Admin or SegurifAI Admin.
    """
    if not (request.user.is_admin or request.user.is_mawdy_admin):
        return Response(
            {'error': 'Solo administradores de MAWDY o SegurifAI pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    team = User.objects.filter(
        role__in=[User.Role.MAWDY_ADMIN, User.Role.MAWDY_FIELD_TECH, User.Role.PROVIDER]
    ).order_by('role', 'email')

    return Response({
        'count': team.count(),
        'team': [
            {
                'id': u.id,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'role': u.role,
                'role_display': u.get_role_display(),
                'is_active': u.is_active,
                'date_joined': u.date_joined.isoformat()
            }
            for u in team
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mawdy_create_team_member(request):
    """
    Create a new MAWDY team member.

    POST /api/admin/mawdy/team/create/

    Body:
    {
        "email": "tecnico@mawdy.gt",
        "password": "SecurePassword123!",
        "first_name": "Carlos",
        "last_name": "Lopez",
        "role": "MAWDY_FIELD_TECH"  // or "MAWDY_ADMIN" or "PROVIDER"
    }

    Accessible by MAWDY Admin or SegurifAI Admin.
    """
    if not (request.user.is_admin or request.user.is_mawdy_admin):
        return Response(
            {'error': 'Solo administradores de MAWDY o SegurifAI pueden crear cuentas'},
            status=status.HTTP_403_FORBIDDEN
        )

    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    role = request.data.get('role', User.Role.MAWDY_FIELD_TECH)

    if not email or not password:
        return Response(
            {'error': 'email y password son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate role is valid for MAWDY
    valid_mawdy_roles = [User.Role.MAWDY_ADMIN, User.Role.MAWDY_FIELD_TECH, User.Role.PROVIDER]
    if role not in valid_mawdy_roles:
        return Response(
            {'error': 'role debe ser MAWDY_ADMIN, MAWDY_FIELD_TECH, o PROVIDER'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Este email ya está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate password
    try:
        validate_password(password)
    except ValidationError as e:
        return Response(
            {'error': 'Contraseña inválida', 'details': list(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role
    )

    return Response({
        'success': True,
        'message': f'Cuenta de equipo MAWDY creada exitosamente',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'role_display': user.get_role_display()
        }
    }, status=status.HTTP_201_CREATED)


# =============================================================================
# PAQ Admin Endpoints
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paq_list_team(request):
    """
    List all PAQ admin team members.

    GET /api/admin/paq/team/

    Accessible by PAQ Admin or SegurifAI Admin.
    """
    if not (request.user.is_admin or request.user.is_paq_admin):
        return Response(
            {'error': 'Solo administradores de PAQ o SegurifAI pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )

    team = User.objects.filter(role=User.Role.PAQ_ADMIN).order_by('email')

    return Response({
        'count': team.count(),
        'team': [
            {
                'id': u.id,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'role': u.role,
                'is_active': u.is_active,
                'date_joined': u.date_joined.isoformat()
            }
            for u in team
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def paq_create_admin(request):
    """
    Create a new PAQ admin account.

    POST /api/admin/paq/team/create/

    Body:
    {
        "email": "admin@paq.gt",
        "password": "SecurePassword123!",
        "first_name": "Maria",
        "last_name": "Garcia"
    }

    Accessible by PAQ Admin or SegurifAI Admin.
    """
    if not (request.user.is_admin or request.user.is_paq_admin):
        return Response(
            {'error': 'Solo administradores de PAQ o SegurifAI pueden crear cuentas'},
            status=status.HTTP_403_FORBIDDEN
        )

    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    if not email or not password:
        return Response(
            {'error': 'email y password son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Este email ya está registrado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate password
    try:
        validate_password(password)
    except ValidationError as e:
        return Response(
            {'error': 'Contraseña inválida', 'details': list(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=User.Role.PAQ_ADMIN
    )

    return Response({
        'success': True,
        'message': f'Cuenta de administrador PAQ creada exitosamente',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        }
    }, status=status.HTTP_201_CREATED)


# =============================================================================
# Common Admin Endpoints
# =============================================================================

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_user_status(request, user_id):
    """
    Activate or deactivate a user account.

    PATCH /api/admin/users/<user_id>/toggle-status/

    Body:
    {
        "is_active": false
    }

    SegurifAI Admin can toggle any account.
    MAWDY Admin can toggle MAWDY team accounts.
    PAQ Admin can toggle PAQ admin accounts.
    """
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check permissions
    can_manage = False
    if request.user.is_admin:
        can_manage = True
    elif request.user.is_mawdy_admin and target_user.is_mawdy_team:
        can_manage = True
    elif request.user.is_paq_admin and target_user.is_paq_admin:
        can_manage = True

    if not can_manage:
        return Response(
            {'error': 'No tienes permiso para modificar este usuario'},
            status=status.HTTP_403_FORBIDDEN
        )

    is_active = request.data.get('is_active')
    if is_active is None:
        return Response(
            {'error': 'is_active es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    target_user.is_active = bool(is_active)
    target_user.save()

    return Response({
        'success': True,
        'message': f'Usuario {"activado" if target_user.is_active else "desactivado"}',
        'user': {
            'id': target_user.id,
            'email': target_user.email,
            'is_active': target_user.is_active
        }
    })
