from django.contrib import admin
from oscar.core.loading import get_model
from django.utils.translation import gettext_lazy as _

Partner = get_model('partner', 'Partner')

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'verification_status', 'website']
    list_filter = ['verification_status']
    search_fields = ['name', 'user__email', 'website']
    raw_id_fields = ['user']
    readonly_fields = ['joined_date', 'date_updated']
    fieldsets = (
        (None, {
            'fields': ('name', 'user')
        }),
        (_('Details'), {
            'fields': ('website', 'logo', 'description')
        }),
        (_('Status'), {
            'fields': ('verification_status',)
        }),
        (_('Timestamps'), {
            'fields': ('joined_date', 'date_updated'),
            'classes': ('collapse',)
        })
    )