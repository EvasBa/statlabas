from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import CompanyProfile # Importuojam iš šios app

# Jei norėsite inline, reikės jį pritaikyti rodyti CustomUserAdmin
# Kol kas palikime tik standartinį adminą

@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user_email', 'company_registration_number', 'company_vat_number') # Pakeistas user į user_email
    search_fields = ('company_name', 'user__email', 'company_registration_number', 'company_vat_number')
    readonly_fields = ('user', 'date_created', 'date_updated')

    # Pagalbinis metodas rodyti user email sąraše
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _('User Email')