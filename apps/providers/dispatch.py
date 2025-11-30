"""
MAWDY Field Tech Dispatch System

Delivery-app style dispatch for motorcycle field technicians.
Features:
- Real-time location tracking
- Radius-based job matching
- Push notification alerts
- Job acceptance workflow
- Earnings tracking
"""
import math
import logging
from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import timedelta

from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, F
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


# =============================================================================
# Constants
# =============================================================================

# Default search radius in kilometers
DEFAULT_SEARCH_RADIUS_KM = 10
MAX_SEARCH_RADIUS_KM = 50

# Job offer timeout (seconds before offer expires)
JOB_OFFER_TIMEOUT_SECONDS = 60

# Maximum concurrent job offers per request
MAX_CONCURRENT_OFFERS = 5

# Earnings per service type (in GTQ)
BASE_EARNINGS = {
    'CERRAJERIA': Decimal('75.00'),
    'COMBUSTIBLE': Decimal('50.00'),
    'LLANTA_PINCHADA': Decimal('60.00'),
    'PASO_CORRIENTE': Decimal('45.00'),
    'AMBULANCIA_ACCIDENTE': Decimal('150.00'),
    'GRUA': Decimal('200.00'),
    'DEFAULT': Decimal('50.00'),
}

# Distance bonus per km (in GTQ)
DISTANCE_BONUS_PER_KM = Decimal('5.00')


# =============================================================================
# Models
# =============================================================================

class FieldTechProfile(models.Model):
    """
    Profile for MAWDY field technicians (motorcycle delivery style).
    """
    class VehicleType(models.TextChoices):
        MOTORCYCLE = 'MOTORCYCLE', 'Motocicleta'
        CAR = 'CAR', 'Automovil'
        TOW_TRUCK = 'TOW_TRUCK', 'Grua'
        AMBULANCE = 'AMBULANCE', 'Ambulancia'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente Aprobacion'
        ACTIVE = 'ACTIVE', 'Activo'
        SUSPENDED = 'SUSPENDED', 'Suspendido'
        INACTIVE = 'INACTIVE', 'Inactivo'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='field_tech_profile'
    )

    # Vehicle info
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
        default=VehicleType.MOTORCYCLE
    )
    vehicle_plate = models.CharField(max_length=20)
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_year = models.IntegerField(null=True, blank=True)

    # Skills/Services this tech can handle
    service_capabilities = models.JSONField(
        default=list,
        help_text='List of service codes tech can handle: ["CERRAJERIA", "COMBUSTIBLE", ...]'
    )

    # Current status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Location & availability
    is_online = models.BooleanField(default=False)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    # Performance
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.00'))
    total_jobs_completed = models.IntegerField(default=0)
    total_jobs_accepted = models.IntegerField(default=0)
    total_jobs_declined = models.IntegerField(default=0)
    acceptance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))

    # Earnings
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    weekly_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    daily_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Push notifications
    fcm_token = models.CharField(max_length=500, blank=True, help_text='Firebase Cloud Messaging token')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'providers'
        verbose_name = 'Field Tech Profile'
        verbose_name_plural = 'Field Tech Profiles'

    def __str__(self):
        return f"{self.user.email} - {self.vehicle_type}"

    @property
    def is_available(self):
        """Check if tech is online and has recent location"""
        if not self.is_online or self.status != self.Status.ACTIVE:
            return False
        if not self.last_location_update:
            return False
        # Location must be updated within last 5 minutes
        cutoff = timezone.now() - timedelta(minutes=5)
        return self.last_location_update >= cutoff

    def update_location(self, latitude: float, longitude: float):
        """Update current location"""
        self.current_latitude = Decimal(str(latitude))
        self.current_longitude = Decimal(str(longitude))
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])

    def go_online(self):
        """Set tech as online"""
        self.is_online = True
        self.save(update_fields=['is_online'])

    def go_offline(self):
        """Set tech as offline"""
        self.is_online = False
        self.save(update_fields=['is_online'])


class FieldTechShift(models.Model):
    """Track field tech work shifts"""

    tech = models.ForeignKey(
        FieldTechProfile,
        on_delete=models.CASCADE,
        related_name='shifts'
    )

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Shift stats
    jobs_completed = models.IntegerField(default=0)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Location tracking
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        app_label = 'providers'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.tech.user.email} - {self.started_at.date()}"

    @property
    def duration(self):
        """Get shift duration"""
        end = self.ended_at or timezone.now()
        return end - self.started_at

    def end_shift(self):
        """End the current shift"""
        self.ended_at = timezone.now()
        self.save(update_fields=['ended_at'])


class JobOffer(models.Model):
    """
    Job offers sent to field techs (like delivery app offers).
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        ACCEPTED = 'ACCEPTED', 'Aceptado'
        DECLINED = 'DECLINED', 'Rechazado'
        EXPIRED = 'EXPIRED', 'Expirado'
        CANCELLED = 'CANCELLED', 'Cancelado'

    # The assistance request being offered
    assistance_request = models.ForeignKey(
        'assistance.AssistanceRequest',
        on_delete=models.CASCADE,
        related_name='job_offers'
    )

    # The tech receiving the offer
    tech = models.ForeignKey(
        FieldTechProfile,
        on_delete=models.CASCADE,
        related_name='job_offers'
    )

    # Offer details
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Distance from tech to job location
    distance_km = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_arrival_minutes = models.IntegerField()

    # Earnings for this job
    base_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    distance_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2)

    # Timestamps
    offered_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)

    # Priority (lower = higher priority, first to receive offer)
    priority = models.IntegerField(default=0)

    # Completion form data (required when completing job)
    completion_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Completion form data: notes, photos, signature, customer satisfaction'
    )

    class Meta:
        app_label = 'providers'
        ordering = ['priority', 'offered_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['tech', 'status']),
        ]

    def __str__(self):
        return f"Offer #{self.id} - {self.tech.user.email} - {self.status}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def accept(self):
        """Accept this job offer"""
        if self.status != self.Status.PENDING:
            return False
        if self.is_expired:
            self.status = self.Status.EXPIRED
            self.save()
            return False

        with transaction.atomic():
            self.status = self.Status.ACCEPTED
            self.responded_at = timezone.now()
            self.save()

            # Cancel all other pending offers for this request
            JobOffer.objects.filter(
                assistance_request=self.assistance_request,
                status=self.Status.PENDING
            ).exclude(id=self.id).update(
                status=self.Status.CANCELLED,
                responded_at=timezone.now()
            )

            # Update tech stats
            self.tech.total_jobs_accepted += 1
            self.tech.save(update_fields=['total_jobs_accepted'])

            return True

    def decline(self):
        """Decline this job offer"""
        if self.status != self.Status.PENDING:
            return False

        self.status = self.Status.DECLINED
        self.responded_at = timezone.now()
        self.save()

        # Update tech stats
        self.tech.total_jobs_declined += 1
        self.tech.save(update_fields=['total_jobs_declined'])

        return True


class FieldTechLocationHistory(models.Model):
    """Track field tech location history during shifts"""

    tech = models.ForeignKey(
        FieldTechProfile,
        on_delete=models.CASCADE,
        related_name='location_history'
    )
    shift = models.ForeignKey(
        FieldTechShift,
        on_delete=models.CASCADE,
        related_name='locations',
        null=True,
        blank=True
    )

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)

    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'providers'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['tech', 'recorded_at']),
        ]


class DispatchActionLog(models.Model):
    """
    Audit log for all dispatch actions.

    Records every action taken in the dispatch system for:
    - Compliance and auditing
    - Admin monitoring
    - Dispute resolution
    - Performance analysis
    """
    class ActionType(models.TextChoices):
        # Job lifecycle
        JOB_CREATED = 'JOB_CREATED', 'Trabajo Creado'
        JOB_OFFERED = 'JOB_OFFERED', 'Oferta Enviada'
        JOB_ACCEPTED = 'JOB_ACCEPTED', 'Oferta Aceptada'
        JOB_DECLINED = 'JOB_DECLINED', 'Oferta Rechazada'
        JOB_EXPIRED = 'JOB_EXPIRED', 'Oferta Expirada'
        JOB_CANCELLED = 'JOB_CANCELLED', 'Trabajo Cancelado'
        JOB_COMPLETED = 'JOB_COMPLETED', 'Trabajo Completado'

        # Tech status
        TECH_ONLINE = 'TECH_ONLINE', 'Técnico En Línea'
        TECH_OFFLINE = 'TECH_OFFLINE', 'Técnico Desconectado'
        TECH_LOCATION_UPDATE = 'TECH_LOCATION', 'Ubicación Actualizada'

        # Dispatch events
        DISPATCH_STARTED = 'DISPATCH_STARTED', 'Despacho Iniciado'
        TECH_EN_ROUTE = 'TECH_EN_ROUTE', 'Técnico En Camino'
        TECH_ARRIVED = 'TECH_ARRIVED', 'Técnico Llegó'
        SERVICE_STARTED = 'SERVICE_STARTED', 'Servicio Iniciado'
        SERVICE_COMPLETED = 'SERVICE_COMPLETED', 'Servicio Completado'

        # Admin actions
        ADMIN_REASSIGN = 'ADMIN_REASSIGN', 'Reasignación por Admin'
        ADMIN_CANCEL = 'ADMIN_CANCEL', 'Cancelación por Admin'

    # What happened
    action = models.CharField(max_length=30, choices=ActionType.choices)

    # Related entities
    job_offer = models.ForeignKey(
        JobOffer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_logs'
    )
    assistance_request = models.ForeignKey(
        'assistance.AssistanceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispatch_logs'
    )
    tech = models.ForeignKey(
        FieldTechProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_logs'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispatch_actions'
    )

    # Location at time of action
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Additional details
    details = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'providers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['assistance_request', 'created_at']),
            models.Index(fields=['tech', 'created_at']),
        ]
        verbose_name = 'Dispatch Action Log'
        verbose_name_plural = 'Dispatch Action Logs'

    def __str__(self):
        return f"{self.get_action_display()} at {self.created_at}"

    @classmethod
    def log_action(cls, action: str, **kwargs):
        """
        Convenience method to log a dispatch action.

        Usage:
            DispatchActionLog.log_action(
                DispatchActionLog.ActionType.JOB_ACCEPTED,
                job_offer=offer,
                tech=tech,
                performed_by=user,
                details={'response_time_seconds': 15}
            )
        """
        return cls.objects.create(action=action, **kwargs)


# =============================================================================
# Dispatch Service
# =============================================================================

class DispatchService:
    """
    Service for dispatching jobs to nearby field techs.
    Works like a food delivery app dispatch system.
    """

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        Returns distance in kilometers.
        """
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(float(lat1))
        lat2_rad = math.radians(float(lat2))
        delta_lat = math.radians(float(lat2) - float(lat1))
        delta_lon = math.radians(float(lon2) - float(lon1))

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    def estimate_arrival_time(distance_km: float, vehicle_type: str = 'MOTORCYCLE') -> int:
        """
        Estimate arrival time in minutes based on distance and vehicle type.
        Accounts for urban traffic in Guatemala City.
        """
        # Average speeds in km/h (accounting for traffic)
        speeds = {
            'MOTORCYCLE': 25,  # Motorcycles can navigate traffic
            'CAR': 20,
            'TOW_TRUCK': 15,
            'AMBULANCE': 30,  # Can use sirens
        }

        speed = speeds.get(vehicle_type, 20)
        time_hours = distance_km / speed
        time_minutes = int(time_hours * 60)

        # Minimum 5 minutes, add 2 minutes buffer
        return max(5, time_minutes + 2)

    @classmethod
    def find_nearby_techs(
        cls,
        latitude: float,
        longitude: float,
        service_code: str,
        radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
        limit: int = MAX_CONCURRENT_OFFERS
    ) -> List[Dict[str, Any]]:
        """
        Find available field techs within radius who can handle the service.
        Returns list sorted by distance (closest first).
        """
        # Get all online, active techs
        from .dispatch import FieldTechProfile

        cutoff = timezone.now() - timedelta(minutes=5)

        available_techs = FieldTechProfile.objects.filter(
            status=FieldTechProfile.Status.ACTIVE,
            is_online=True,
            last_location_update__gte=cutoff,
            current_latitude__isnull=False,
            current_longitude__isnull=False
        )

        # Filter by service capability
        nearby_techs = []

        for tech in available_techs:
            # Check if tech can handle this service
            if service_code not in tech.service_capabilities and 'ALL' not in tech.service_capabilities:
                continue

            # Check if tech doesn't have an active job
            active_offers = JobOffer.objects.filter(
                tech=tech,
                status=JobOffer.Status.ACCEPTED,
                assistance_request__status__in=['PENDING', 'IN_PROGRESS', 'EN_ROUTE']
            ).exists()

            if active_offers:
                continue

            # Calculate distance
            distance = cls.calculate_distance(
                latitude, longitude,
                float(tech.current_latitude),
                float(tech.current_longitude)
            )

            if distance <= radius_km:
                eta = cls.estimate_arrival_time(distance, tech.vehicle_type)
                nearby_techs.append({
                    'tech': tech,
                    'distance_km': round(distance, 2),
                    'eta_minutes': eta,
                    'rating': float(tech.rating),
                    'jobs_completed': tech.total_jobs_completed,
                })

        # Sort by distance, then by rating (higher is better)
        nearby_techs.sort(key=lambda x: (x['distance_km'], -x['rating']))

        return nearby_techs[:limit]

    @classmethod
    def calculate_earnings(cls, service_code: str, distance_km: float) -> Dict[str, Decimal]:
        """Calculate earnings for a job"""
        base = BASE_EARNINGS.get(service_code, BASE_EARNINGS['DEFAULT'])
        distance_bonus = DISTANCE_BONUS_PER_KM * Decimal(str(max(0, distance_km - 3)))  # Bonus after 3km

        return {
            'base_earnings': base,
            'distance_bonus': round(distance_bonus, 2),
            'total_earnings': base + distance_bonus,
        }

    @classmethod
    def dispatch_job(cls, assistance_request) -> Dict[str, Any]:
        """
        Dispatch a job to nearby field techs.
        Creates job offers for the closest available techs.
        """
        from apps.assistance.models import AssistanceRequest

        # Get job location
        lat = float(assistance_request.location_latitude) if assistance_request.location_latitude else None
        lon = float(assistance_request.location_longitude) if assistance_request.location_longitude else None

        if not lat or not lon:
            return {
                'success': False,
                'error': 'La solicitud no tiene coordenadas de ubicacion',
                'error_code': 'NO_LOCATION'
            }

        # Extract service code from incident_type (format: MAWDY_SERVICECODE)
        service_code = assistance_request.incident_type.replace('MAWDY_', '') if assistance_request.incident_type else 'DEFAULT'

        # Find nearby techs
        nearby_techs = cls.find_nearby_techs(lat, lon, service_code)

        if not nearby_techs:
            # Expand search radius
            nearby_techs = cls.find_nearby_techs(lat, lon, service_code, radius_km=MAX_SEARCH_RADIUS_KM)

        if not nearby_techs:
            return {
                'success': False,
                'error': 'No hay tecnicos disponibles en tu area',
                'error_code': 'NO_TECHS_AVAILABLE'
            }

        # Create job offers
        offers_created = []
        expires_at = timezone.now() + timedelta(seconds=JOB_OFFER_TIMEOUT_SECONDS)

        for priority, tech_info in enumerate(nearby_techs):
            tech = tech_info['tech']
            earnings = cls.calculate_earnings(service_code, tech_info['distance_km'])

            offer = JobOffer.objects.create(
                assistance_request=assistance_request,
                tech=tech,
                distance_km=Decimal(str(tech_info['distance_km'])),
                estimated_arrival_minutes=tech_info['eta_minutes'],
                base_earnings=earnings['base_earnings'],
                distance_bonus=earnings['distance_bonus'],
                total_earnings=earnings['total_earnings'],
                expires_at=expires_at,
                priority=priority
            )

            offers_created.append({
                'offer_id': offer.id,
                'tech_email': tech.user.email,
                'distance_km': tech_info['distance_km'],
                'eta_minutes': tech_info['eta_minutes'],
                'total_earnings': float(earnings['total_earnings']),
            })

            # TODO: Send push notification to tech
            # cls.send_job_notification(tech, offer)

        return {
            'success': True,
            'message': f'Oferta enviada a {len(offers_created)} tecnicos',
            'offers_count': len(offers_created),
            'offers': offers_created,
            'expires_in_seconds': JOB_OFFER_TIMEOUT_SECONDS
        }

    @classmethod
    def get_pending_offers_for_tech(cls, tech: FieldTechProfile) -> List[JobOffer]:
        """Get all pending job offers for a tech"""
        now = timezone.now()

        # Expire old offers first
        JobOffer.objects.filter(
            tech=tech,
            status=JobOffer.Status.PENDING,
            expires_at__lt=now
        ).update(status=JobOffer.Status.EXPIRED)

        return list(JobOffer.objects.filter(
            tech=tech,
            status=JobOffer.Status.PENDING,
            expires_at__gte=now
        ).select_related('assistance_request', 'assistance_request__user').order_by('priority'))

    @classmethod
    def get_active_job_for_tech(cls, tech: FieldTechProfile) -> Optional[JobOffer]:
        """Get the tech's current active job"""
        return JobOffer.objects.filter(
            tech=tech,
            status=JobOffer.Status.ACCEPTED,
            assistance_request__status__in=['PENDING', 'IN_PROGRESS', 'EN_ROUTE', 'ARRIVED']
        ).select_related('assistance_request', 'assistance_request__user').first()

    @classmethod
    def complete_job(cls, offer: JobOffer) -> Dict[str, Any]:
        """Mark a job as completed and update earnings"""
        with transaction.atomic():
            # Update tech stats
            tech = offer.tech
            tech.total_jobs_completed += 1
            tech.daily_earnings += offer.total_earnings
            tech.weekly_earnings += offer.total_earnings
            tech.total_earnings += offer.total_earnings

            # Update acceptance rate
            total_offers = tech.total_jobs_accepted + tech.total_jobs_declined
            if total_offers > 0:
                tech.acceptance_rate = Decimal(str(
                    (tech.total_jobs_accepted / total_offers) * 100
                ))

            tech.save()

            # Update current shift if any
            current_shift = FieldTechShift.objects.filter(
                tech=tech,
                ended_at__isnull=True
            ).first()

            if current_shift:
                current_shift.jobs_completed += 1
                current_shift.earnings += offer.total_earnings
                current_shift.save()

            return {
                'success': True,
                'earnings': float(offer.total_earnings),
                'total_jobs_completed': tech.total_jobs_completed,
                'daily_earnings': float(tech.daily_earnings),
            }
