from django.db import models
from django.conf import settings # Reikia AUTH_USER_MODEL
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from accounts.models import CustomUser # Importuojame iš accounts

class CompanyProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_profile',
        primary_key=True,
        limit_choices_to={'user_type': CustomUser.USER_TYPE_COMPANY}, # Naudojame importuotą CustomUser
        verbose_name=_('User Account')
    )
    company_name = models.CharField(_('Company Name'), max_length=255, db_index=True, blank=False)
    company_registration_number = models.CharField(_('Company Registration Number'), max_length=30, blank=True)
    company_vat_number = models.CharField(_('VAT Number'), max_length=50, blank=True)
    legal_address = models.CharField(_('Legal Address'), max_length=255, blank=True)
    legal_city = models.CharField(_('Legal City'), max_length=150, blank=True)
    legal_zip_code = models.CharField(_('Legal Zip Code'), max_length=20, blank=True)
    legal_country = models.CharField(_('Legal Country'), max_length=150, blank=True)
    company_phone = models.CharField(_('Company Phone'), max_length=30, blank=True)
    company_email = models.EmailField(_('Company Email'), blank=True)
    contact_person = models.CharField(_('Contact Person'), max_length=255, blank=True)
    contact_person_phone = models.CharField(_('Contact Person Phone'), max_length=30, blank=True)
    contact_person_email = models.EmailField(_('Contact Person Email'), blank=True)
    contact_person_position = models.CharField(_('Contact Person Position'), max_length=100, blank=True) # Sutrumpinta max_length
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def clean(self):
        # --- Patikrinti user importą, jei reikia ---
        # (user pasiekiamas per self.user)
        if self.user_id and not self.user.is_company:
             raise ValidationError({'user': _('Company profile can only be associated with a company user type.')})
        super().clean()

    def __str__(self):
        return self.company_name or f"Company Profile for {self.user.email}"

    class Meta:
        verbose_name = _('Company Profile')
        verbose_name_plural = _('Company Profiles')
        ordering = ['company_name']