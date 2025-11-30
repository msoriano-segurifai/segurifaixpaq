from django.contrib import admin
from .models import AssistanceRequest, RequestUpdate, RequestDocument


class RequestUpdateInline(admin.TabularInline):
    model = RequestUpdate
    extra = 0
    readonly_fields = ('created_at',)


class RequestDocumentInline(admin.TabularInline):
    model = RequestDocument
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(AssistanceRequest)
class AssistanceRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'user', 'service_category', 'status', 'priority', 'provider', 'created_at')
    list_filter = ('status', 'priority', 'service_category', 'created_at')
    search_fields = ('request_number', 'user__email', 'title', 'description', 'location_city')
    readonly_fields = ('request_number', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    inlines = [RequestUpdateInline, RequestDocumentInline]

    fieldsets = (
        ('Request Information', {
            'fields': ('request_number', 'user', 'user_service', 'service_category', 'provider')
        }),
        ('Details', {
            'fields': ('title', 'description', 'priority', 'status')
        }),
        ('Location', {
            'fields': ('location_address', 'location_city', 'location_state', 'location_latitude', 'location_longitude')
        }),
        ('Roadside Assistance Details', {
            'fields': ('vehicle_make', 'vehicle_model', 'vehicle_year', 'vehicle_plate'),
            'classes': ('collapse',)
        }),
        ('Health Assistance Details', {
            'fields': ('patient_name', 'patient_age', 'symptoms'),
            'classes': ('collapse',)
        }),
        ('Card Insurance Details', {
            'fields': ('card_last_four', 'incident_type'),
            'classes': ('collapse',)
        }),
        ('Time Tracking', {
            'fields': ('estimated_arrival_time', 'actual_arrival_time', 'completion_time')
        }),
        ('Cost', {
            'fields': ('estimated_cost', 'actual_cost')
        }),
        ('Notes', {
            'fields': ('admin_notes', 'cancellation_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(RequestUpdate)
class RequestUpdateAdmin(admin.ModelAdmin):
    list_display = ('request', 'update_type', 'user', 'created_at')
    list_filter = ('update_type', 'created_at')
    search_fields = ('request__request_number', 'message')
    readonly_fields = ('created_at',)


@admin.register(RequestDocument)
class RequestDocumentAdmin(admin.ModelAdmin):
    list_display = ('request', 'document_type', 'uploaded_by', 'description', 'created_at')
    list_filter = ('document_type', 'created_at')
    search_fields = ('request__request_number', 'description')
    readonly_fields = ('created_at',)
