from rest_framework import serializers
from oscar.core.loading import get_model
from drf_writable_nested.serializers import WritableNestedModelSerializer
from django.db import transaction, IntegrityError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point # Reikalingas Partner modeliui

logger = logging.getLogger(__name__)

# --- Model Imports ---
Partner = get_model('partner', 'Partner')
Warehouse = get_model('locations', 'Warehouse')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
AttributeOption = get_model('catalogue', 'AttributeOption')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductImage = get_model('catalogue', 'ProductImage')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'StockRecord')
Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')

# SimpleJWT Serializer (Customized)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        if hasattr(user, 'partner_profile'):
            token['is_partner'] = True
            token['partner_id'] = user.partner_profile.id
            token['is_verified'] = user.partner_profile.is_verified # Pridėta patikrai
        else:
             token['is_partner'] = False
        return token

# =============================================
# --- Serializers for Reading Data (GET) ---
# =============================================

class PartnerReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'name', 'code'] # Minimalūs laukai

class WarehouseReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'city', 'is_pickup_available']

class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ['option']

class AttributeOptionGroupSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)
    class Meta:
        model = AttributeOptionGroup
        fields = ['id','name', 'options']

class ProductAttributeSerializer(serializers.ModelSerializer):
    option_group = AttributeOptionGroupSerializer(read_only=True)
    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'code', 'type', 'option_group'] # Pataisyta 'options' į 'option_group'

class ProductAttributeValueReadOnlySerializer(serializers.ModelSerializer):
    attribute = ProductAttributeSerializer(read_only=True)
    value = serializers.CharField(source='value_as_text', read_only=True) # Naudojam value_as_text
    class Meta:
        model = ProductAttributeValue
        fields = ['attribute', 'value'] # Pataisyta 'attributes' į 'attribute'

class ProductImageReadOnlySerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    original_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'original_url', 'caption', 'display_order', 'thumbnail_url']
        read_only_fields = ['thumbnail_url', 'original_url']

    def _get_absolute_url(self, image_field):
        request = self.context.get('request')
        if image_field and hasattr(image_field, 'url') and request:
            try:
                return request.build_absolute_uri(image_field.url)
            except ValueError: return None
        elif image_field and hasattr(image_field, 'url'):
             return image_field.url
        return None

    def get_original_url(self, obj):
        return self._get_absolute_url(obj.original)

    def get_thumbnail_url(self, obj):
        # TODO: Implement thumbnail generation (e.g., sorl-thumbnail)
        return self.get_original_url(obj)

class CategoryReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug'] # Paliekam paprastus laukus

class StockRecordReadOnlySerializer(serializers.ModelSerializer): # Pataisytas pavadinimas
    partner = PartnerReadOnlySerializer(read_only=True)
    warehouse = WarehouseReadOnlySerializer(read_only=True)
    # Pridedam kainą be PVM skaitymui
    price = serializers.DecimalField(source='price_excl_tax', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = StockRecord
        fields = [
            'id', 'partner', 'warehouse', 'partner_sku',
            'price_currency', 'price', # Naudojam 'price' (iš source='price_excl_tax')
            'num_in_stock', 'num_allocated', 'low_stock_threshold'
        ]

class ProductReadOnlySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='product-detail', read_only=True)
    product_class = serializers.StringRelatedField()
    attributes = ProductAttributeValueReadOnlySerializer(many=True, read_only=True, source='attribute_values') # Pataisyta į Value serializerį
    categories = CategoryReadOnlySerializer(many=True, read_only=True)
    images = ProductImageReadOnlySerializer(many=True, read_only=True) # Pataisytas serializerio pavadinimas, pataisita source
    stockrecords = StockRecordReadOnlySerializer(many=True, read_only=True) # Pataisytas serializerio pavadinimas
    min_distance = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'url', 'upc', 'title', 'slug', 'description', # Pridėtas kablelis po url
            'product_class',
            'attributes',
            'categories',
            'images',
            'stockrecords',
            'is_public', 'date_created',
            'condition',
            'min_distance', # Pridėtas min_distance
        ]

# =======================================================
# --- Serializers for Writing Data (POST, PUT, PATCH) ---
# =======================================================

class StockRecordWriteSerializer(serializers.ModelSerializer):
    """ Serializer for receiving StockRecord data. Uses 'price' field. """
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.filter(is_active=True),
        allow_null=True,
        required=False
    )
    # --- Naudojame 'price' ---vel pataisyta i price_excl_tax
    price_excl_tax = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=True,
        source='price' 
     ) # Map to model's 'price' field
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    num_in_stock = serializers.IntegerField(required=True, min_value=0)
    partner_sku = serializers.CharField(max_length=128, required=False, allow_blank=True)
    price_currency = serializers.CharField(max_length=12, read_only=True, default=settings.OSCAR_DEFAULT_CURRENCY)

    class Meta:
        model = StockRecord
        # --- Naudojame 'price' ---
        fields = [
            'warehouse', 'partner_sku', 'price_excl_tax',
            'num_in_stock', 'price_currency',
        ]
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    def validate_warehouse(self, value):
        partner = self.context.get('partner')
        if not partner:
             raise serializers.ValidationError(_("Partner context is missing."))
        if value and value.partner != partner:
            raise serializers.ValidationError(_("The selected warehouse does not belong to this partner."))
        return value

class AttributeValueWriteSerializer(serializers.Serializer):
    code = serializers.SlugField(max_length=128, required=True)
    value = serializers.JSONField(required=True) # Naudoja JSONField

class ProductImageWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, help_text=_("ID of existing image to update (optional)."))
    original = serializers.ImageField(required=False, allow_null=True, use_url=False)
    display_order = serializers.IntegerField(required=False, default=0)
    caption = serializers.CharField(max_length=200, required=False, allow_blank=True)

    class Meta:
        model = ProductImage
        fields = ['id', 'original', 'caption', 'display_order']


class ProductWriteSerializer(WritableNestedModelSerializer):
    # --- Nested Write Serializers ---
    stockrecord = StockRecordWriteSerializer(required=True, allow_null=False, write_only=True) # <<< Pridėtas write_only=True
    attributes = AttributeValueWriteSerializer(many=True, required=False, write_only=True) # <<< Pridėtas write_only=True
    images = ProductImageWriteSerializer(many=True, required=False, write_only=True) # <<< Pridėtas write_only=True
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True, required=False, write_only=True # <<< Pridėtas write_only=True
    )
    product_class = serializers.SlugRelatedField(
        slug_field='slug', queryset=ProductClass.objects.all(), required=True
    )
    condition = serializers.ChoiceField(choices=Product.CONDITION_CHOICES, required=False)

    class Meta:
        model = Product
        fields = [
            'id', # Skaitymui
            'product_class',
            'title',
            'description',
            'upc',
            'structure',
            'is_public',
            'condition',
            # --- Write-only laukai ---
            'categories',
            'attributes',
            'stockrecord',
            'images',
        ]
        read_only_fields = ['id']

    @transaction.atomic
    def create(self, validated_data):
        logger.debug(f"--- ProductWriteSerializer CREATE ---")
        logger.debug(f"Initial validated_data: {validated_data}")

        # Pop nested data BEFORE calling super().create() if not using WritableNestedModelSerializer for them
        # Since we use WritableNestedModelSerializer, we let it handle basic fields first
        stockrecord_data = validated_data.pop('stockrecord') # <<< Išimam rankiniam apdorojimui
        attributes_data = validated_data.pop('attributes', [])
        images_data = validated_data.pop('images', [])
        categories_data = validated_data.pop('categories', [])
        logger.debug(f"Data after popping nested: {validated_data}")

        upc = validated_data.get('upc')
        product = None
        if upc:
            product = Product.objects.filter(upc=upc).first()

        partner = self.context['partner']
        logger.debug(f"Context partner: {partner}")

        if product:
            logger.info(f"Product with UPC {upc} found (ID: {product.pk}). Creating stock record for partner {partner.pk}.")
            # Prepare data for StockRecord using MODEL field names
            stockrecord_defaults = {
                'partner_sku': stockrecord_data.get('partner_sku', product.upc or f'SKU-{product.pk}'),
                'price_excl_tax': stockrecord_data.get('price_excl_tax'), # <<< Naudojam MODELIO lauką
                'num_in_stock': stockrecord_data.get('num_in_stock'),
                'price_currency': settings.OSCAR_DEFAULT_CURRENCY,
                'warehouse': stockrecord_data.get('warehouse')
            }
            logger.debug(f"Defaults for get_or_create StockRecord: {stockrecord_defaults}")
            stockrecord, created = StockRecord.objects.get_or_create(
                product=product,
                partner=partner,
                # warehouse=stockrecord_data.get('warehouse'), # Optional key part
                defaults=stockrecord_defaults
            )
            if not created:
                 logger.warning(f"StockRecord for product {product.pk} / partner {partner.pk} already exists.")
            if categories_data:
                 product.categories.add(*categories_data)
        else:
            logger.info(f"Product with UPC {upc} not found. Creating new product for partner {partner.pk}.")
            # Create Product object using super().create() from WritableNestedModelSerializer
            # It will handle basic fields
            product = super().create(validated_data)
            logger.debug(f"Product created with ID: {product.pk}")

            # Create StockRecord manually
            stockrecord_create_kwargs = {
                'product': product,
                'partner': partner,
                'partner_sku': stockrecord_data.get('partner_sku', product.upc or f'SKU-{product.pk}'),
                'price': stockrecord_data.get('price', 0), # <<< Naudojam MODELIO lauką, vel pataisyta
                'num_in_stock': stockrecord_data.get('num_in_stock'),
                'price_currency': settings.OSCAR_DEFAULT_CURRENCY,
                'warehouse': stockrecord_data.get('warehouse')
            }
            logger.debug(f"Kwargs for StockRecord create: {stockrecord_create_kwargs}")
            StockRecord.objects.create(**stockrecord_create_kwargs)

            # Save related M2M/FK data AFTER product is created
            self._save_attributes(product, attributes_data)
            if categories_data:
                 product.categories.set(categories_data)
            self._save_images(product, images_data)

        logger.info(f"Product processing finished for ID: {product.pk}")
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        logger.debug(f"--- ProductWriteSerializer UPDATE for instance {instance.pk} ---")
        logger.debug(f"Initial validated_data: {validated_data}")

        stockrecord_data = validated_data.pop('stockrecord', None)
        attributes_data = validated_data.pop('attributes', None)
        images_data = validated_data.pop('images', None)
        categories_data = validated_data.pop('categories', None)

        partner = self.context['partner']
        logger.debug(f"Context partner: {partner}")

        # Update Product instance using super().update() from WritableNested
        product = super().update(instance, validated_data)
        logger.debug(f"Product {product.pk} updated basic fields.")

        # Update StockRecord
        if stockrecord_data:
            stockrecord = StockRecord.objects.filter(product=product, partner=partner).first()
            if stockrecord:
                 logger.debug(f"Updating stock record {stockrecord.pk}")
                 stockrecord.partner_sku = stockrecord_data.get('partner_sku', stockrecord.partner_sku)
                 stockrecord.price_excl_tax = stockrecord_data.get('price_excl_tax', stockrecord.price_excl_tax) # <<< Naudojam MODELIO lauką
                 stockrecord.num_in_stock = stockrecord_data.get('num_in_stock', stockrecord.num_in_stock)
                 new_warehouse = stockrecord_data.get('warehouse')
                 if new_warehouse is not None:
                     if new_warehouse and new_warehouse.partner != partner:
                         raise serializers.ValidationError({'stockrecord': {'warehouse': 'Invalid warehouse selected.'}})
                     stockrecord.warehouse = new_warehouse
                 stockrecord.save()
            else:
                 logger.warning(f"StockRecord not found for product {product.pk} / partner {partner.pk} during update.")

        # Update Attributes, Categories, Images if data was provided
        if attributes_data is not None: self._save_attributes(product, attributes_data)
        if categories_data is not None: product.categories.set(categories_data)
        if images_data is not None: self._save_images(product, images_data)

        logger.info(f"Product {product.pk} update finished.")
        return product

    # --- _save_attributes ir _save_images metodai lieka tokie patys ---
    def _save_attributes(self, product, attributes_data):
        # ... (metodo kodas) ...
        logger.debug(f"Saving attributes for product {product.pk}: {attributes_data}")
        valid_attribute_codes = ProductAttribute.objects.filter(
            product_class=product.product_class
        ).values_list('code', flat=True)
        current_attributes = {val.attribute.code: val for val in product.attribute_values.all()}
        received_codes = {attr_data.get('code') for attr_data in attributes_data if attr_data.get('code')}

        for code_to_delete in current_attributes.keys() - received_codes:
            current_attributes[code_to_delete].delete()
            logger.debug(f"Deleted attribute '{code_to_delete}' for product {product.pk}")

        for attr_data in attributes_data:
            code = attr_data.get('code')
            value = attr_data.get('value')
            if not code or value is None: continue
            if code not in valid_attribute_codes:
                logger.warning(f"Attribute code '{code}' not valid for class '{product.product_class}'. Skipping.")
                continue
            try:
                attribute = ProductAttribute.objects.get(code=code, product_class=product.product_class)
                defaults={'value': attribute.validate_value(value)}
                attr_value_obj, created = ProductAttributeValue.objects.update_or_create(
                    product=product, attribute=attribute, defaults=defaults
                )
                logger.debug(f"{'Created' if created else 'Updated'} attribute '{code}' for product {product.pk}")
            except ProductAttribute.DoesNotExist: logger.error(f"Attribute code '{code}' should exist but not found.")
            except (ValidationError, TypeError) as e: logger.error(f"Invalid value '{value}' for attribute '{code}': {e}")
            except Exception as e: logger.error(f"Error saving attribute '{code}' for product {product.pk}: {e}", exc_info=True)

    def _save_images(self, product, images_data):
        # ... (metodo kodas) ...
        logger.debug(f"Saving images for product {product.pk}: {images_data}")
        ids_to_keep = set()
        for img_data in images_data:
            image_id = img_data.get('id')
            original_file = img_data.get('original')
            caption = img_data.get('caption', '')
            display_order = img_data.get('display_order', 0)

            if image_id:
                ids_to_keep.add(image_id)
                try:
                    img_obj = ProductImage.objects.get(pk=image_id, product=product)
                    if original_file: img_obj.original = original_file
                    img_obj.caption = caption
                    img_obj.display_order = display_order
                    img_obj.save()
                    logger.debug(f"Updated image {image_id} for product {product.pk}")
                except ProductImage.DoesNotExist: logger.warning(f"Image ID {image_id} not found for product {product.pk}. Skipping update.")
            elif original_file:
                 new_image = product.images.create(original=original_file, caption=caption, display_order=display_order)
                 ids_to_keep.add(new_image.pk)
                 logger.debug(f"Created new image for product {product.pk}")

        if product.pk:
            images_to_delete = product.images.exclude(pk__in=ids_to_keep)
            if images_to_delete.exists():
                logger.debug(f"Deleting images {list(images_to_delete.values_list('pk', flat=True))} for product {product.pk}")
                images_to_delete.delete()