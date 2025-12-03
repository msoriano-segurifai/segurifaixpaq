from django.contrib import admin
from django.utils.html import format_html
from .models import Booking, BookingStatusHistory


class BookingStatusHistoryInline(admin.TabularInline):
    """Inline admin for booking status history"""
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ['previous_status', 'new_status', 'changed_by', 'notes', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin configuration for Booking model"""
    list_display = [
        'reference_code', 'user_name', 'service_name', 'status_badge',
        'priority_badge', 'scheduled_date', 'scheduled_time', 'created_at'
    ]
    list_filter = ['status', 'priority', 'service_type', 'scheduled_date', 'created_at']
    search_fields = [
        'reference_code', 'service_name', 'user__email',
        'user__first_name', 'user__last_name', 'location_address'
    ]
    readonly_fields = ['reference_code', 'created_at', 'updated_at', 'cancelled_at', 'completed_at']
    date_hierarchy = 'scheduled_date'
    ordering = ['-scheduled_date', '-created_at']

    fieldsets = (
        ('Informacion General', {
            'fields': ('reference_code', 'user', 'status', 'priority')
        }),
        ('Servicio', {
            'fields': ('service_type', 'service_name', 'description')
        }),
        ('Programacion', {
            'fields': ('scheduled_date', 'scheduled_time', 'estimated_duration_minutes')
        }),
        ('Ubicacion', {
            'fields': ('location_address', 'location_latitude', 'location_longitude', 'location_notes')
        }),
        ('Contacto', {
            'fields': ('contact_name', 'contact_phone')
        }),
        ('Asignacion', {
            'fields': ('assigned_provider',)
        }),
        ('Notas', {
            'fields': ('user_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Cancelacion', {
            'fields': ('cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Finalizacion', {
            'fields': ('completed_at', 'completion_notes'),
            'classes': ('collapse',)
        }),
        ('Calificacion', {
            'fields': ('rating', 'rating_comment'),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [BookingStatusHistoryInline]

    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'Usuario'

    def status_badge(self, obj):
        colors = {
            'PENDING': '#ffc107',      # Yellow
            'CONFIRMED': '#17a2b8',    # Blue
            'IN_PROGRESS': '#007bff',  # Primary
            'COMPLETED': '#28a745',    # Green
            'CANCELLED': '#dc3545',    # Red
            'NO_SHOW': '#6c757d',      # Gray
            'RESCHEDULED': '#fd7e14',  # Orange
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def priority_badge(self, obj):
        colors = {
            'LOW': '#6c757d',
            'NORMAL': '#17a2b8',
            'HIGH': '#fd7e14',
            'URGENT': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'

    def save_model(self, request, obj, form, change):
        """Track status changes in admin"""
        if change:
            # Get previous status
            old_obj = Booking.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                # Log the status change
                BookingStatusHistory.objects.create(
                    booking=obj,
                    previous_status=old_obj.status,
                    new_status=obj.status,
                    changed_by=request.user,
                    notes=f'Cambiado desde admin'
                )
        super().save_model(request, obj, form, change)


@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for BookingStatusHistory model"""
    list_display = ['booking', 'previous_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['booking__reference_code', 'notes']
    readonly_fields = ['booking', 'previous_status', 'new_status', 'changed_by', 'notes', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
