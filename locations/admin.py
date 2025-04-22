from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.utils.translation import gettext_lazy as _
from .models import Warehouse

@admin.register(Warehouse)
class WarehouseAdmin(gis_admin.OSMGeoAdmin): # Naudojam OSMGeoAdmin žemėlapiui
    gis_field = 'location' # Nurodom GIS lauką
    list_display = (
        'name', 'city', 'country', 'is_pickup_available', 'is_active',
        # 'vendor' # Pridėsime vėliau
    )
    list_filter = ('city', 'country', 'is_active', 'is_pickup_available',
                   # 'vendor' # Pridėsime vėliau
                  )
    search_fields = ('name', 'city', 'address_line', 'zip_code',
                     # 'vendor__name', 'vendor__user__email' # Pridėsime vėliau
                    )
    # Apibrėžiame laukus redagavimo formoje
    fieldsets = (
        (None, {'fields': ('name', 'is_active',)}), # 'vendor',
        (_('Address'), {'fields': ('address_line', 'city', 'zip_code', 'country')}),
        (_('Contact & Access'), {'fields': ('phone', 'operating_hours', 'is_pickup_available')}),
        (_('Map Location'), {'fields': ('location',)}), # GIS laukas
    )
    # Padarome location neredaguojamu tiesiogiai (nes nustatomas iš adreso)
    # Bet OSMGeoAdmin gali jį rodyti žemėlapyje
    readonly_fields = ('location',) # Galima užkomentuoti, jei norite leisti rankinį keitimą

    # Default map settings
    default_lon = 23.9
    default_lat = 54.89
    default_zoom = 6