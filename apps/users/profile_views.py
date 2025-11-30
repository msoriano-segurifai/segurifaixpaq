"""
User Profile Views for SegurifAI x PAQ

Comprehensive profile endpoints for:
- SegurifAI Users: E-learning gamification + Subscription countdown
- MAWDY Field Techs: Work history + Performance stats
"""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_full_profile(request):
    """
    Get comprehensive user profile with e-learning and subscription info.

    GET /api/users/full-profile/

    Returns:
    {
        "user": {...basic info...},
        "e_learning": {
            "points": {...},
            "modules": {...},
            "achievements": [...],
            "credits": {...}
        },
        "subscription": {
            "active_subscriptions": [...],
            "renewal_countdown": {...}
        }
    }
    """
    user = request.user

    # Basic user info
    user_data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone_number,
        'role': user.role,
        'paq_wallet_id': user.paq_wallet_id,
        'created_at': user.date_joined.isoformat() if user.date_joined else None,
    }

    # E-Learning Gamification
    e_learning = _get_elearning_data(user)

    # Subscription Info with Countdown
    subscription = _get_subscription_data(user)

    return Response({
        'user': user_data,
        'e_learning': e_learning,
        'subscription': subscription,
    })


def _get_elearning_data(user):
    """Get e-learning gamification data for a user"""
    from apps.gamification.models import (
        UserPoints, UserProgress, UserAchievement,
        UserDiscountCredits, EducationalModule
    )

    # Points & Level
    try:
        points = UserPoints.objects.get(user=user)
        points_data = {
            'total_points': points.puntos_totales,
            'level': points.nivel,
            'level_display': points.get_nivel_display(),
            'modules_completed': points.modulos_completados,
            'streak_days': points.racha_dias,
            'last_activity': points.ultima_actividad.isoformat() if points.ultima_actividad else None,
            'next_level': _get_next_level_info(points),
        }
    except UserPoints.DoesNotExist:
        points_data = {
            'total_points': 0,
            'level': 'NOVATO',
            'level_display': 'Novato',
            'modules_completed': 0,
            'streak_days': 0,
            'last_activity': None,
            'next_level': {'level': 'APRENDIZ', 'points_needed': 100},
        }

    # Module Progress
    total_modules = EducationalModule.objects.filter(activo=True).count()
    completed = UserProgress.objects.filter(
        user=user, estado='COMPLETADO'
    ).count()
    in_progress = UserProgress.objects.filter(
        user=user, estado='EN_PROGRESO'
    ).count()

    # Recent progress
    recent_progress = UserProgress.objects.filter(
        user=user
    ).select_related('modulo').order_by('-completado_en', '-iniciado_en')[:5]

    modules_data = {
        'total_available': total_modules,
        'completed': completed,
        'in_progress': in_progress,
        'completion_percentage': round((completed / total_modules * 100), 1) if total_modules > 0 else 0,
        'recent': [
            {
                'module_id': p.modulo.id,
                'title': p.modulo.titulo,
                'category': p.modulo.categoria,
                'status': p.estado,
                'quiz_score': p.porcentaje_quiz if p.quiz_completado else None,
                'points_earned': p.puntos_obtenidos,
                'completed_at': p.completado_en.isoformat() if p.completado_en else None,
            }
            for p in recent_progress
        ]
    }

    # Achievements
    achievements = UserAchievement.objects.filter(
        user=user
    ).select_related('achievement').order_by('-obtenido_en')[:10]

    achievements_data = [
        {
            'id': a.achievement.id,
            'name': a.achievement.nombre,
            'description': a.achievement.descripcion,
            'icon': a.achievement.icono,
            'points_bonus': a.achievement.puntos_bonus,
            'earned_at': a.obtenido_en.isoformat(),
        }
        for a in achievements
    ]

    # Discount Credits
    try:
        credits = UserDiscountCredits.objects.get(user=user)
        credits_data = {
            'available_balance': float(credits.saldo_disponible),
            'total_earned': float(credits.total_acumulado),
            'total_used': float(credits.total_usado),
            'last_used': credits.ultimo_uso.isoformat() if credits.ultimo_uso else None,
            'currency': 'GTQ',
        }
    except UserDiscountCredits.DoesNotExist:
        credits_data = {
            'available_balance': 0,
            'total_earned': 0,
            'total_used': 0,
            'last_used': None,
            'currency': 'GTQ',
        }

    return {
        'points': points_data,
        'modules': modules_data,
        'achievements': achievements_data,
        'achievements_count': len(achievements_data),
        'credits': credits_data,
    }


def _get_next_level_info(points):
    """Get info about next level requirements"""
    thresholds = {
        'NOVATO': ('APRENDIZ', 100),
        'APRENDIZ': ('CONOCEDOR', 250),
        'CONOCEDOR': ('EXPERTO', 500),
        'EXPERTO': ('MAESTRO', 1000),
        'MAESTRO': (None, None),
    }
    next_level, points_needed = thresholds.get(points.nivel, (None, None))
    if next_level:
        return {
            'level': next_level,
            'points_needed': points_needed,
            'points_remaining': max(0, points_needed - points.puntos_totales),
            'progress_percentage': round(min(100, (points.puntos_totales / points_needed * 100)), 1),
        }
    return {'level': None, 'message': 'Nivel maximo alcanzado!'}


def _get_subscription_data(user):
    """Get subscription data with renewal countdown"""
    from apps.services.models import UserService
    from apps.services.renewal import SubscriptionRenewalService

    today = timezone.now().date()

    # Get active subscriptions
    subscriptions = UserService.objects.filter(
        user=user,
        status__in=['ACTIVE', 'EXPIRED']
    ).select_related('plan').order_by('end_date')

    subs_data = []
    nearest_renewal = None

    for sub in subscriptions:
        days_remaining = (sub.end_date - today).days if sub.end_date else 0

        # Get category name safely
        category_name = None
        if sub.plan and hasattr(sub.plan, 'category') and sub.plan.category:
            if hasattr(sub.plan.category, 'name'):
                category_name = sub.plan.category.name
            else:
                category_name = str(sub.plan.category)

        sub_info = {
            'id': sub.id,
            'plan_name': sub.plan.name if sub.plan else None,
            'plan_category': category_name,
            'status': sub.status,
            'start_date': sub.start_date.isoformat() if sub.start_date else None,
            'end_date': sub.end_date.isoformat() if sub.end_date else None,
            'days_remaining': max(0, days_remaining),
            'is_expiring_soon': 0 < days_remaining <= 7,
            'is_expired': days_remaining < 0,
            'auto_renew': sub.auto_renew,
        }

        # Add renewal info
        if sub.plan:
            renewal_status = SubscriptionRenewalService.get_renewal_status(sub)
            sub_info['renewal_info'] = {
                'can_renew': renewal_status['can_renew'],
                'original_price': renewal_status['pricing']['original_price'],
                'credits_applicable': renewal_status['pricing']['credits_applicable'],
                'final_price': renewal_status['pricing']['final_price'],
                'can_pay_with_credits_only': renewal_status['pricing']['can_pay_with_credits_only'],
            }

        subs_data.append(sub_info)

        # Track nearest renewal
        if sub.status == 'ACTIVE' and days_remaining >= 0:
            if nearest_renewal is None or days_remaining < nearest_renewal['days']:
                nearest_renewal = {
                    'subscription_id': sub.id,
                    'plan_name': sub.plan.name if sub.plan else None,
                    'days': days_remaining,
                    'end_date': sub.end_date.isoformat() if sub.end_date else None,
                }

    # Build countdown
    countdown = None
    if nearest_renewal:
        days = nearest_renewal['days']
        if days == 0:
            countdown = {'message': 'Tu suscripcion vence HOY', 'urgency': 'critical'}
        elif days == 1:
            countdown = {'message': 'Tu suscripcion vence MANANA', 'urgency': 'critical'}
        elif days <= 3:
            countdown = {'message': f'Tu suscripcion vence en {days} dias', 'urgency': 'high'}
        elif days <= 7:
            countdown = {'message': f'Tu suscripcion vence en {days} dias', 'urgency': 'medium'}
        else:
            countdown = {'message': f'{days} dias restantes', 'urgency': 'low'}

        countdown.update(nearest_renewal)

    return {
        'active_subscriptions': subs_data,
        'total_subscriptions': len(subs_data),
        'renewal_countdown': countdown,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def field_tech_profile(request):
    """
    Get MAWDY Field Tech profile with work history.

    GET /api/providers/dispatch/my-profile/

    Returns comprehensive field tech data including:
    - Personal info & vehicle details
    - Performance stats (rating, acceptance rate)
    - Earnings (daily, weekly, total)
    - Work history (completed jobs)
    - Current shift info
    """
    user = request.user

    # Must be a field tech
    try:
        from apps.providers.dispatch import FieldTechProfile, JobOffer, FieldTechShift
        tech = FieldTechProfile.objects.get(user=user)
    except FieldTechProfile.DoesNotExist:
        return Response(
            {'error': 'No tienes perfil de tecnico de campo'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Basic profile info
    profile_data = {
        'id': tech.id,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.email,
            'phone': user.phone_number,
        },
        'vehicle': {
            'type': tech.vehicle_type,
            'type_display': tech.get_vehicle_type_display(),
            'plate': tech.vehicle_plate,
            'model': tech.vehicle_model,
            'year': tech.vehicle_year,
        },
        'service_capabilities': tech.service_capabilities,
        'status': tech.status,
        'status_display': tech.get_status_display(),
        'is_online': tech.is_online,
        'is_available': tech.is_available,
        'current_location': {
            'latitude': float(tech.current_latitude) if tech.current_latitude else None,
            'longitude': float(tech.current_longitude) if tech.current_longitude else None,
            'last_update': tech.last_location_update.isoformat() if tech.last_location_update else None,
        },
        'created_at': tech.created_at.isoformat(),
    }

    # Performance stats
    performance = {
        'rating': float(tech.rating),
        'rating_stars': round(float(tech.rating), 1),
        'total_jobs_completed': tech.total_jobs_completed,
        'total_jobs_accepted': tech.total_jobs_accepted,
        'total_jobs_declined': tech.total_jobs_declined,
        'acceptance_rate': float(tech.acceptance_rate),
        'acceptance_rate_display': f'{float(tech.acceptance_rate):.1f}%',
    }

    # Earnings
    earnings = {
        'daily': float(tech.daily_earnings),
        'weekly': float(tech.weekly_earnings),
        'total': float(tech.total_earnings),
        'currency': 'GTQ',
    }

    # Work history - completed jobs
    completed_jobs = JobOffer.objects.filter(
        tech=tech,
        status=JobOffer.Status.ACCEPTED,
        assistance_request__status='COMPLETED'
    ).select_related(
        'assistance_request', 'assistance_request__user'
    ).order_by('-responded_at')[:20]

    work_history = []
    for job in completed_jobs:
        req = job.assistance_request
        work_history.append({
            'job_id': job.id,
            'request_id': req.id,
            'request_number': req.request_number,
            'title': req.title,
            'service_type': req.incident_type,
            'location': {
                'address': req.location_address,
                'city': req.location_city,
            },
            'distance_km': float(job.distance_km),
            'earnings': float(job.total_earnings),
            'accepted_at': job.responded_at.isoformat() if job.responded_at else None,
            'completed_at': req.completed_at.isoformat() if hasattr(req, 'completed_at') and req.completed_at else None,
            'customer_name': req.user.get_full_name() or req.user.email.split('@')[0] if req.user else None,
        })

    # Current shift
    current_shift = FieldTechShift.objects.filter(
        tech=tech,
        ended_at__isnull=True
    ).first()

    shift_data = None
    if current_shift:
        shift_data = {
            'id': current_shift.id,
            'started_at': current_shift.started_at.isoformat(),
            'duration_hours': round(current_shift.duration.total_seconds() / 3600, 2),
            'jobs_completed': current_shift.jobs_completed,
            'earnings': float(current_shift.earnings),
            'total_distance_km': float(current_shift.total_distance_km),
        }

    # Current active job
    active_job = JobOffer.objects.filter(
        tech=tech,
        status=JobOffer.Status.ACCEPTED,
        assistance_request__status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS', 'EN_ROUTE']
    ).select_related('assistance_request', 'assistance_request__user').first()

    active_job_data = None
    if active_job:
        req = active_job.assistance_request
        active_job_data = {
            'job_id': active_job.id,
            'request_id': req.id,
            'request_number': req.request_number,
            'title': req.title,
            'status': req.status,
            'location': {
                'address': req.location_address,
                'city': req.location_city,
                'latitude': float(req.location_latitude) if req.location_latitude else None,
                'longitude': float(req.location_longitude) if req.location_longitude else None,
            },
            'customer': {
                'name': req.user.get_full_name() or req.user.email.split('@')[0] if req.user else None,
                'phone': req.user.phone_number if req.user else None,
            },
            'earnings': float(active_job.total_earnings),
            'eta_minutes': active_job.estimated_arrival_minutes,
        }

    # Summary stats
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    today_jobs = JobOffer.objects.filter(
        tech=tech,
        status=JobOffer.Status.ACCEPTED,
        assistance_request__status='COMPLETED',
        responded_at__date=today
    ).count()

    week_jobs = JobOffer.objects.filter(
        tech=tech,
        status=JobOffer.Status.ACCEPTED,
        assistance_request__status='COMPLETED',
        responded_at__date__gte=week_start
    ).count()

    summary = {
        'jobs_today': today_jobs,
        'jobs_this_week': week_jobs,
        'active_job': active_job_data is not None,
    }

    return Response({
        'profile': profile_data,
        'performance': performance,
        'earnings': earnings,
        'current_shift': shift_data,
        'active_job': active_job_data,
        'work_history': work_history,
        'work_history_count': len(work_history),
        'summary': summary,
    })
