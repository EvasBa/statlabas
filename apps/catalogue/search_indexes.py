from haystack import indexes
from oscar.core.loading import get_model
from django.contrib.gis.geos import Point # Reikia Point
from django.db import models

Product = get_model('catalogue', 'Product')

class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', boost=1.5)
    product_class = indexes.CharField(model_attr='product_class__name', faceted=True, null=True)
    upc = indexes.CharField(model_attr='upc', null=True)
    categories = indexes.MultiValueField(faceted=True)
    category_slugs = indexes.MultiValueField(faceted=True)
    price = indexes.DecimalField(faceted=True, null=True)
    partner_name = indexes.CharField(faceted=True, null=True)
    condition = indexes.CharField(model_attr='condition', faceted=True, null=True)
    location_city = indexes.CharField(faceted=True, null=True)
    date_created = indexes.DateTimeField(model_attr='date_created')
    is_public = indexes.BooleanField(model_attr='is_public')

    # --- Geografinis Laukas ---
    location_point = indexes.LocationField(null=True)

    def get_model(self):
        return Product

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_public=True).prefetch_related(
            'categories', 'attribute_values__attribute', 'stockrecords__partner',
            'stockrecords__warehouse'
        ).distinct()

    def prepare_categories(self, obj):
        return [category.name for category in obj.categories.all()]

    def prepare_category_slugs(self, obj):
        return [category.slug for category in obj.categories.all()]

    def prepare_price(self, obj): # Jau yra
        stockrecords = obj.stockrecords.filter(num_in_stock__gt=0)
        if stockrecords.exists():
            return stockrecords.aggregate(min_price=models.Min('price'))['min_price'] # Naudojam 'price' iš StockRecord
        return None


    def prepare_partner_name(self, obj):
        # ... (logika iš ankstesnio pavyzdžio) ...
        first_stockrecord = obj.stockrecords.filter(num_in_stock__gt=0).first()
        if first_stockrecord and first_stockrecord.partner:
            return first_stockrecord.partner.name
        return None

    def prepare_location_point(self, obj):
        """ Grąžina produkto (likučio) geografines koordinates. """
        # Imame pirmo aktyvaus stockrecord'o lokaciją
        first_stockrecord = obj.stockrecords.filter(num_in_stock__gt=0).order_by('pk').first()
        if first_stockrecord:
            if first_stockrecord.warehouse and first_stockrecord.warehouse.location:
                return first_stockrecord.warehouse.location # GIS Point objektas
            elif first_stockrecord.partner and first_stockrecord.partner.default_location:
                return first_stockrecord.partner.default_location # GIS Point objektas
        return None

    def prepare_location_point(self, obj):
        """ Grąžina produkto (likučio) geografines koordinates. """
        first_stockrecord = obj.stockrecords.filter(num_in_stock__gt=0).first()
        if first_stockrecord:
            if first_stockrecord.warehouse and first_stockrecord.warehouse.location:
                return first_stockrecord.warehouse.location # GIS Point objektas
            elif first_stockrecord.partner and first_stockrecord.partner.default_location:
                return first_stockrecord.partner.default_location # GIS Point objektas
        return None # Arba galite grąžinti numatytąjį tašką, jei norite visada turėti reikšmę