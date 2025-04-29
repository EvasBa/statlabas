import django_filters
from oscar.core.loading import get_model
from django.utils.translation import gettext_lazy as _
# Importuojam GIS laukus ir funkcijas, jei filtruosime pagal geometriją
# from django.contrib.gis.db.models import PointField
# from django.contrib.gis.measure import D
# from django.contrib.gis.geos import Point
# from django.contrib.gis.db.models.functions import Distance

Product = get_model('catalogue', 'Product')
Category = get_model('catalogue', 'Category')
Partner = get_model('partner', 'Partner')

class ProductFilter(django_filters.FilterSet):
    # --- Filtravimas pagal Kategoriją ---
    # Leidžia filtruoti pagal kategorijos slug'ą (pvz., ?category=gipso-plokstes)
    category = django_filters.CharFilter(
        field_name='categories__slug',
        lookup_expr='iexact', # Tikslus atitikimas, nekreipiant dėmesio į raidžių dydį
        label=_('Category Slug')
    )
    # Galima pridėti filtravimą pagal kelias kategorijas (pvz., ?category=1,2,3)
    # category_in = django_filters.BaseInFilter(field_name='categories__id', lookup_expr='in')

    # --- Filtravimas pagal Kainą ---
    # Leidžia nurodyti minimalią kainą (pvz., ?min_price=10.50)
    min_price = django_filters.NumberFilter(
        field_name="stockrecords__price", # Naudojam modelio lauką 'price'
        lookup_expr='gte', # Greater than or equal (>=)
        label=_('Minimum Price')
    )
    # Leidžia nurodyti maksimalią kainą (pvz., ?max_price=50)
    max_price = django_filters.NumberFilter(
        field_name="stockrecords__price",
        lookup_expr='lte', # Less than or equal (<=)
        label=_('Maximum Price')
    )

    # --- Filtravimas pagal Tiekėją ---
    # Leidžia filtruoti pagal tiekėjo ID (pvz., ?partner=5)
    partner = django_filters.ModelChoiceFilter(field_name='stockrecords__partner',
                                               queryset=Partner.objects.filter(verification_status=Partner.STATUS_VERIFIED))

    # --- Filtravimas pagal Būklę (Jūsų pridėtas laukas) ---
    condition = django_filters.ChoiceFilter(
        choices=Product.CONDITION_CHOICES,
        field_name='condition',
        label=_('Condition')
    )

    # --- Filtravimas pagal Atributus (Sudėtingesnis - pradinis pavyzdys) ---
    # Tai tik paprastas pavyzdys vienam atributui. Dinaminiam filtravimui pagal
    # bet kokį atributą reikėtų sudėtingesnės logikos (galbūt perrašant filter_queryset).
    # manufacturer = django_filters.CharFilter(
    #     method='filter_by_attribute',
    #     label=_('Manufacturer (by attribute code)')
    # )
    # def filter_by_attribute(self, queryset, name, value):
    #     # Filtruoja pagal atributo kodą ir reikšmę
    #     # 'name' čia bus 'manufacturer' (ar kitas lauko pavadinimas FilterSet'e)
    #     return queryset.filter(
    #         attribute_values__attribute__code=name,
    #         attribute_values__value_text__iexact=value # Arba value_option, value_integer...
    #     ).distinct()

    class Meta:
        model = Product
        # Laukai, pagal kuriuos leidžiamas TIKSLUS filtravimas (jei reikia)
        # Dažniausiai naudojame aukščiau apibrėžtus filtrus su lookup_expr
        fields = ['category', 'min_price', 'max_price', 'partner', 'condition']