from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from oscar.core.loading import get_model
from elasticsearch_dsl import analyzer

# Get the models
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')

@registry.register_document
class ProductDocument(Document):
    """Product Elasticsearch document."""

    # Existing fields
    title = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    description = fields.TextField()
    upc = fields.KeywordField()
    condition = fields.KeywordField()
    is_public = fields.BooleanField()
    date_created = fields.DateField()

    # Price fields from StockRecord
    price = fields.FloatField()
    price_currency = fields.KeywordField()
    num_in_stock = fields.IntegerField()

    # Partner information
    partner_name = fields.KeywordField()
    partner_id = fields.IntegerField()

    # Location information
    location_city = fields.KeywordField()
    location_point = fields.GeoPointField()

    # Categories and product class
    categories = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'slug': fields.KeywordField(),
        }
    )
    product_class = fields.ObjectField(
        properties={
            'name': fields.TextField(),
            'slug': fields.KeywordField(),
        }
    )

    class Index:
        name = 'marketplace_products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Product

        # Define related fields to fetch
        related_models = [StockRecord]

    def prepare_price(self, instance):
        """Get the lowest price for the product."""
        stockrecord = instance.stockrecords.order_by('price').first()
        return float(stockrecord.price) if stockrecord else None

    def prepare_price_currency(self, instance):
        """Get the currency from the first stockrecord."""
        stockrecord = instance.stockrecords.first()
        return stockrecord.price_currency if stockrecord else None

    def prepare_num_in_stock(self, instance):
        """Get the stock count from the first stockrecord."""
        stockrecord = instance.stockrecords.first()
        return stockrecord.num_in_stock if stockrecord else 0

    def prepare_partner_name(self, instance):
        """Get the partner name from the first stockrecord."""
        stockrecord = instance.stockrecords.select_related('partner').first()
        return stockrecord.partner.name if stockrecord else None

    def prepare_partner_id(self, instance):
        """Get the partner ID from the first stockrecord."""
        stockrecord = instance.stockrecords.select_related('partner').first()
        return stockrecord.partner.id if stockrecord else None

    def prepare_location_city(self, instance):
        """Get the warehouse city from the first stockrecord."""
        stockrecord = instance.stockrecords.select_related('warehouse').first()
        return stockrecord.warehouse.city if stockrecord and stockrecord.warehouse else None

    def prepare_location_point(self, instance):
        """Get the warehouse location from the first stockrecord."""
        stockrecord = instance.stockrecords.select_related('warehouse').first()
        if stockrecord and stockrecord.warehouse and stockrecord.warehouse.location:
            return {
                'lat': stockrecord.warehouse.location.y,
                'lon': stockrecord.warehouse.location.x
            }
        return None

    def get_instances_from_related(self, related_model):
        """If related model is StockRecord, get all products with stockrecords."""
        if related_model == StockRecord:
            return Product.objects.filter(stockrecords__isnull=False).distinct()

