from django.contrib import admin
from .models import Provider, ProviderReview


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'status', 'rating', 'total_completed', 'is_available', 'created_at')
    list_filter = ('status', 'is_available', 'service_categories')
    search_fields = ('company_name', 'business_license', 'user__email', 'city', 'state')
    readonly_fields = ('rating', 'total_reviews', 'total_completed', 'created_at', 'updated_at')
    filter_horizontal = ('service_categories',)
    fieldsets = (
        ('Company Information', {
            'fields': ('user', 'company_name', 'business_license', 'tax_id')
        }),
        ('Contact Information', {
            'fields': ('business_phone', 'business_email', 'website')
        }),
        ('Address & Location', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country', 'latitude', 'longitude')
        }),
        ('Services', {
            'fields': ('service_categories', 'service_radius_km', 'service_areas')
        }),
        ('Availability', {
            'fields': ('is_available', 'working_hours')
        }),
        ('Ratings & Performance', {
            'fields': ('rating', 'total_reviews', 'total_completed')
        }),
        ('Documents', {
            'fields': ('certificate', 'insurance_policy')
        }),
        ('Status', {
            'fields': ('status', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ProviderReview)
class ProviderReviewAdmin(admin.ModelAdmin):
    list_display = ('provider', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('provider__company_name', 'user__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
