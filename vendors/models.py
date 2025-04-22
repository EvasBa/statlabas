from django.db import models
from django.conf import settings # Reikalingas AUTH_USER_MODEL
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from oscar.apps.partner.models import Partner as OscarPartner
from config.utils import generate_unique_slug # Arba statulab.utils, priklausomai nuo struktūros
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

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

    default_location_name = models.CharField(
        _('Default Location Name'), 
        max_length=255, blank=True, 
        help_text=_('Name of the default location where items are located if no specific warehouse is used. e.g. Kaunas, Kauno rajonas.')
        )
    default_location = gis_models.PointField(
        _('Default Location Coordinates'),
        srid=4326,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Approximate geographic coordinates automatically determined from the location name.")
    )
    

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
    
    def geocode_default_location(self):
        """
        Bando nustatyti default_location koordinates pagal default_location_name.
        Naudoja Nominatim (OpenStreetMap). Reikalinga geopy biblioteka.
        Grąžina Point objektą arba None.
        """
        if not self.default_location_name:
            return None

        geolocator = Nominatim(user_agent="vendor_geocoder")
        try:
            location = geolocator.geocode(self.default_location_name)
            if location:
                return Point(location.longitude, location.latitude, srid=4326)
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            # Galima užfiksuoti klaidą arba loguoti
            print(f"Geocoding error: {e}")
        return None  

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
        # Nustatome geocode default_location
        update_location = kwargs.pop('update_location', False) 
        if 'default_location_name' in kwargs.get('update_fields', []) or \
           (self.pk is None and self.default_location_name) or \
           (self.default_location_name and not self.default_location) or \
           update_location:
            # Tikrinam, ar default_location_name pasikeitė (jei objektas jau egzistuoja)
            needs_geocode = True
            if self.pk and not update_location:
                 try:
                     orig = Vendor.objects.get(pk=self.pk)
                     if orig.default_location_name == self.default_location_name and self.default_location:
                         needs_geocode = False # Nepasikeitė ir jau turim koordinates
                 except Vendor.DoesNotExist:
                     pass # Naujas objektas

            if needs_geocode:
                new_location = self.geocode_default_location()
                # Nustatome naują lokaciją tik jei geokodavimas pavyko
                if new_location:
                    self.default_location = new_location
                elif not self.pk and not self.default_location: # Jei naujas ir nepavyko, paliekam NULL
                    self.default_location = None
                # Jei redaguojamas ir nepavyko, paliekam seną lokaciją (self.default_location)

        # Išvalome update_fields, jei naudojome savo logikai
        if 'update_fields' in kwargs:
            update_fields = list(kwargs['update_fields']) if kwargs['update_fields'] is not None else None
            if update_fields and 'default_location_name' in update_fields:
                # Jei keitėsi pavadinimas, būtinai įtraukiam ir location į saugomus laukus
                if 'default_location' not in update_fields:
                    update_fields.append('default_location')
                kwargs['update_fields'] = tuple(update_fields)
        # --- Pabaiga: default_location nustatymas ---

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