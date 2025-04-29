from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.utils.translation import gettext_lazy as _
# --- Importuojame Warehouse ---
from .models import Warehouse
# --- Importuojame Partner (kad galėtume naudoti nuorodai ir filtravimui) ---
from oscar.core.loading import get_model # Geriau naudoti get_model
Partner = get_model('partner', 'Partner') # Gaunam mūsų forkintą Partner

@admin.register(Warehouse)
class WarehouseAdmin(gis_admin.OSMGeoAdmin):
    gis_field = 'location'
    list_display = (
        'name', 'city', 'partner_link', 'is_pickup_available', 'is_active', # <<< Pridėtas partner_link
    )
    list_filter = (
        'is_active', 'is_pickup_available', 'city', 'country',
        'partner' # <<< Pridėtas partner filtras
    )
    search_fields = (
        'name', 'city', 'address_line', 'zip_code',
        'partner__name', 'partner__user__email' # <<< Pridėta paieška pagal partnerį
    )
    # Naudojam raw_id_fields dideliam partnerių skaičiui (geresnis našumas nei dropdown)
    raw_id_fields = ('partner',) # <<< Leidžia patogiai ieškoti ir pasirinkti partnerį

    fieldsets = (
        # --- Pridedame partner lauką prie pagrindinės informacijos ---
        (None, {'fields': ('partner', 'name', 'is_active',)}),
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        (_('Address'), {'fields': ('address_line', 'city', 'zip_code', 'country')}),
        (_('Contact & Access'), {'fields': ('phone', 'operating_hours', 'is_pickup_available')}),
        (_('Map Location'), {'fields': ('location',)}),
    )
    readonly_fields = ('location',) # Paliekam read-only

    # --- Metodas nuorodai į partnerį sąraše ---
    @admin.display(description=_('Partner/Vendor'))
    def partner_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.partner:
            # Kuriam nuorodą į partnerio redagavimo puslapį admin'e
            link = reverse("admin:partner_partner_change", args=[obj.partner.pk]) # Naudojam app_label 'partner' ir model_name 'partner'
            return format_html('<a href="{}">{}</a>', link, obj.partner.name or obj.partner.code)
        return "-"
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # Žemėlapio nustatymai lieka tie patys
    default_lon = 23.9
    default_lat = 54.89
    default_zoom = 6