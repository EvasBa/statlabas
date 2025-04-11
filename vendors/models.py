from django.db import models
from django.conf import settings # Reikalingas AUTH_USER_MODEL
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from oscar.apps.partner.models import Partner as OscarPartner
from config.utils import generate_unique_slug # Arba statulab.utils, priklausomai nuo struktūros

class Vendor(OscarPartner):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='vendor_profile',
        verbose_name=_('Associated User Account'),
        help_text=_('The user account that manages this vendor profile.')
    )
    logo = models.ImageField(_('Logo'), upload_to='vendor_logos/', blank=True, null=True, help_text=_('Upload a logo for the vendor.'))
    website = models.URLField(_('Website'), blank=True, null=True, help_text=_('Vendor website URL.'))
    description = models.TextField(_('Description'), blank=True, null=True, help_text=_('Vendor description.'))
    joined_date = models.DateTimeField(_('Joined Date'), auto_now_add=True, help_text=_('Date when the vendor joined.'))
    date_updated = models.DateTimeField(auto_now=True)

    VERIFICATION_PENDING = 'pending'
    VERIFICATION_VERIFIED = 'verified'
    VERIFICATION_REJECTED = 'rejected'
    VERIFICATION_STATUS_CHOICES = [
        (VERIFICATION_PENDING, _('Pending')),
        (VERIFICATION_VERIFIED, _('Verified')),
        (VERIFICATION_REJECTED, _('Rejected')),
    ]
    verification_status = models.CharField(
        _('Verification Status'),
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default=VERIFICATION_PENDING,
        help_text=_('Status of vendor verification.')
    )
    verified_date = models.DateTimeField(_('Verified Date'), blank=True, null=True, help_text=_('Date when the vendor was verified.'))
    rejection_reason = models.TextField(_('Rejection Reason'), blank=True, null=True, help_text=_('Reason for vendor rejection.'))
    average_rating = models.DecimalField(_('Average Rating'), max_digits=3, decimal_places=2, default=0.00, help_text=_('Average rating of the vendor.'))
    total_count = models.PositiveIntegerField(_('Total Count'), default=0, help_text=_('Total number of products from this vendor.'))
    total_sales = models.DecimalField(_('Total Sales'), max_digits=10, decimal_places=2, default=0.00, help_text=_('Total sales amount for this vendor.'))
    return_policy = models.TextField(_('Return Policy'), blank=True, null=True, help_text=_('Return policy of the vendor.'))
    payment_terms = models.TextField(_('Payment Terms'), blank=True, null=True, help_text=_('Payment terms of the vendor.'))
    update_date = models.DateTimeField(_('Update Date'), auto_now=True, help_text=_('Date when the vendor profile was last updated.'))


    @property
    def is_verified(self):
        return self.verification_status == self.VERIFICATION_VERIFIED

    def get_vendor_display_name(self):
        # Naudoja self.user, kuris yra CustomUser iš accounts
        # Patikrinti, ar CompanyProfile pasiekiamas teisingai per related_name
        # Taip, 'company_profile' yra teisingas related_name
        if self.user.is_company and hasattr(self.user, 'company_profile') and self.user.company_profile.company_name:
             return self.user.company_profile.company_name
        elif self.user.get_full_name():
             return self.user.get_full_name()
        return self.user.email

    def save(self, *args, **kwargs):
        self.name = self.get_vendor_display_name()
        if not self.code:
            base_slug_name = self.name or f"vendor-{self.user_id}"
            base_slug = slugify(base_slug_name, allow_unicode=False)
            if not base_slug:
                 base_slug = f"vendor-{self.user_id}"
            self.code = generate_unique_slug(self, base_slug, 'code') # Naudoja importuotą funkciją

        if self.verification_status == self.VERIFICATION_VERIFIED and not self.verified_date:
            self.verified_date = timezone.now()
        # ... (kita save logika) ...
        super().save(*args, **kwargs)

    def __str__(self):
        status_display = self.get_verification_status_display()
        return f'{self.name or self.code} ({status_display})' # Pridėtas self.code kaip fallback

    class Meta:
        verbose_name = _('Vendor')
        verbose_name_plural = _('Vendors')
        ordering = ['name']
        # Nurodome unikalumo apribojimą (nors OneToOne jau daro)
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_vendor_user_association')
        ]