from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _
from django.conf import settings # Reikės AUTH_USER_MODEL, jei susiesim tiesiogiai

# Importuojam geopy (jei įdiegta)
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    from django.contrib.gis.geos import Point
    geopy_available = True
except ImportError:
    geopy_available = False
    Nominatim = None
    Point = None

import logging
logger = logging.getLogger(__name__)

class Warehouse(models.Model):
    # vendor = models.ForeignKey( # <<< Pridėsime vėliau
    #     'vendors.Vendor',
    #     on_delete=models.CASCADE,
    #     related_name='warehouses',
    #     verbose_name=_("Vendor")
    # )
    name = models.CharField(
        _("Warehouse/Location Name"),
        max_length=150,
        db_index=True,
        help_text=_("A name for this location, e.g., 'Main Warehouse', 'Kaunas Pickup Point'.")
    )
    address_line = models.CharField(
        _("Address Line"),
        max_length=255,
        help_text=_("Street address and number.")
    )
    city = models.CharField(
        _("City"),
        max_length=100,
        db_index=True
    )
    zip_code = models.CharField(
        _("Zip/Post Code"),
        max_length=20,
        blank=True
    )
    country = models.CharField(
        _("Country"),
        max_length=100,
        # Rekomenduotina naudoti django-countries, bet pradžiai užtenka CharField
        help_text=_("Country name.")
    )
    location = gis_models.PointField(
        _("Location Coordinates"),
        srid=4326,
        null=True, # Nustatysime per save()
        blank=True,
        db_index=True,
        editable=False, # Paprastai neredaguojamas tiesiogiai admin'e
        help_text=_("Geographic coordinates (longitude, latitude), set automatically from address.")
    )
    phone = models.CharField(_("Warehouse Phone"), max_length=30, blank=True)
    is_pickup_available = models.BooleanField(_("Pickup Available From Here?"), default=True)
    operating_hours = models.TextField(_("Operating Hours"), blank=True)
    is_active = models.BooleanField(_("Is Active?"), default=True, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def get_full_address(self):
        """ Helper method to get a formatted address string. """
        parts = [self.address_line, self.city, self.zip_code, self.country]
        return ", ".join(filter(None, parts)) # Filtruoja tuščias reikšmes

    def geocode_address(self):
        """
        Tries to determine coordinates from the address fields using Nominatim.
        Returns a Point object or None.
        """
        if not geopy_available:
            return None

        address_str = self.get_full_address()
        if not address_str:
            return None

        geolocator = Nominatim(user_agent="statulab_warehouse_geocoder")
        try:
            location_data = geolocator.geocode(address_str, exactly_one=True, timeout=10)
            if location_data:
                return Point(location_data.longitude, location_data.latitude, srid=4326)
            else:
                logger.warning(f"Geocoding failed for warehouse {self.pk}: No location found for '{address_str}'.")
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error for warehouse {self.pk} ('{address_str}'): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected geocoding error for warehouse {self.pk}: {e}", exc_info=True)
            return None

    def save(self, *args, **kwargs):
        # Prieš saugant, bandom nustatyti koordinates, jei jos tuščios arba adresas pasikeitė
        update_location = kwargs.pop('update_location', False)
        needs_geocode = False

        if self.pk: # Jei objektas jau egzistuoja
             # Tikrinam ar pasikeitė adresas
             try:
                 orig = Warehouse.objects.get(pk=self.pk)
                 if orig.get_full_address() != self.get_full_address() or update_location:
                     needs_geocode = True
             except Warehouse.DoesNotExist:
                 needs_geocode = True # Turėtų neįvykti, bet apsidraudžiam
        else: # Naujas objektas
             needs_geocode = True

        if needs_geocode and (not self.location or update_location):
             new_location = self.geocode_address()
             if new_location:
                 self.location = new_location
             # Jei geokodavimas nepavyko, paliekam location koks buvo (arba NULL)

        super().save(*args, **kwargs)

    def __str__(self):
        # Pridedam vendor vardą, kai bus ryšys
        # if self.vendor:
        #     return f"{self.name} ({self.vendor.name})"
        return f"{self.name} ({self.city})"

    class Meta:
        verbose_name = _("Warehouse")
        verbose_name_plural = _("Warehouses")
        ordering = ['name'] # Pakeisime, kai bus vendor
        # Unikalumas? Galbūt vendor + name turi būti unikalus?
        # constraints = [
        #     models.UniqueConstraint(fields=['vendor', 'name'], name='unique_vendor_warehouse_name')
        # ]