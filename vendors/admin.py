from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Vendor # Importuojam iš šios app

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    # ... (visas VendorAdmin kodas, kaip buvo anksčiau) ...
    # Patikrinkite, ar visi laukai egzistuoja modelyje
    list_display = ('name', 'user_display', 'verification_status', 'is_verified_display', 'joined_date', 'average_rating')
    list_filter = ('verification_status', 'joined_date')
    search_fields = ('name', 'user__email', 'user__first_name', 'user__last_name', 'user__company_profile__company_name')
    readonly_fields = ('user', 'name', 'code', 'joined_date', 'verified_date', 'date_updated', 'average_rating', 'total_count', 'total_sales')
    fieldsets = (
        # ... (fieldsets kaip anksčiau, be banko duomenų) ...
    )
    actions = ['mark_as_verified', 'mark_as_rejected']

    def user_display(self, obj):
        return str(obj.user)
    user_display.short_description = _('User Account')

    def is_verified_display(self, obj):
        return obj.is_verified # Galima naudoti property tiesiogiai
    is_verified_display.boolean = True
    is_verified_display.short_description = _('Is Verified?')

    @admin.action(description=_('Mark selected vendors as Verified'))
    def mark_as_verified(self, request, queryset):
        # Add logic to mark vendors as verified
        for vendor in queryset:
            vendor.verification_status = Vendor.VERIFICATION_VERIFIED
            vendor.verified_date = timezone.now() if vendor.verification_status == Vendor.VERIFICATION_VERIFIED else None
            vendor.save()
            # Galite pridėti pranešimą apie sėkmingą patvirtinimą
            self.message_user(request, _('Vendor {} marked as verified.').format(vendor.name))
        # ... (veiksmo kodas) ...

    @admin.action(description=_('Mark selected vendors as Rejected'))
    def mark_as_rejected(self, request, queryset):
        # Add logic to mark vendors as rejected
        pass