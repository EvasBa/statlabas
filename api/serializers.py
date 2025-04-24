from rest_framework import serializers
from oscar.core.loading import get_model
from drf_writable_nested.serializers import WritableNestedModelSerializer
from django.db import transaction, IntegrityError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# models for the serializer
Partner = get_model('partner', 'Partner')
Warehouse = get_model('locations', 'Warehouse')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
AttrbuteOption = get_model('catalogue', 'AttributeOption')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
#AttributeOptionValue = get_model('catalogue', 'AttributeOptionValue')
ProductImage = get_model('catalogue', 'ProductImage')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'StockRecord')
Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')

#---- Serializers for reading

class PartnerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Partner model.
    """
    class Meta:
        model = Partner
        fields = ['id', 'name', 'email', 'phone', 'website', 'description', 'return_policy', 'verification_status', 'joined_date']

class WarehouseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Warehouse model.
    """
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'address_line', 'city', 'zip_code', 'country', 'location', 'phone', 'is_pickup_available', 'operating_hours', 'is_active']


class AttributeOptionSerializer(serializers.ModelSerializer):
    """
    Serializer for the AttributeOption model.
    """
    class Meta:
        model = AttrbuteOption
        fields = ['options']

class AttributeOptionGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for the AttributeOptionGroup model.
    """
    options = AttributeOptionSerializer(many=True, read_only=True)
    class Meta:
        model = AttributeOptionGroup
        fields = ['id','name', 'options']

class ProductAttributeSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProductAttribute model.
    """
    option_group = AttributeOptionGroupSerializer(read_only=True)
    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'code', 'type','options']

class ProductAttributeValueSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProductAttributeValue model.
    """
    attribute = ProductAttributeSerializer(read_only=True)
    value = serializers.CharField(source='value_as_string')
    class Meta:
        model = ProductAttributeValue
        fields = ['attribute', 'value']

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProductImage model.
    """
    thumbnail = serializers.SerializerMethodField()
    class Meta:
        model = ProductImage
        fields = ['id', 'original', 'caption','display_order', 'thumbnail_url']
        read_only_fields = ['thumbnail']
    def get_thumbnail_url(self, obj):
        """
        Returns the thumbnail URL for the product image.
        """
        request = self.context.get('request')
        if obj.original and request:
            return request.build_absolute_uri(obj.original.url)
        elif obj.original:
            return obj.original.url
        return None
    
class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image',]
        
class StockRecorReadOnlydSerializer(serializers.ModelSerializer):
    """
    Serializer for the StockRecord model.
    """
    partner = PartnerSerializer(read_only=True)
    warehouse = WarehouseSerializer(read_only=True)

    class Meta:
        model = StockRecord
        fields = ['id', 'partner', 'warehouse', 'partner_sku', 'price_currency', 'price_excl_tax', 'price_incl_tax', 'num_in_stock', 'num_allocated', 'low_stock_threshold']

class ProductReadOnlySerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model. Read-only fields.
    """
    product_class = serializers.StringRelatedField()
    attributes = ProductAttributeSerializer(many=True, read_only=True, source = 'attribute_values')
    categories = CategorySerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True, source='images')
    stockrecords = StockRecorReadOnlydSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = [
            'id', 'url'
            'upc', 'title', 'slug', 'description',
            'product_class', 'attributes', 'categories',
            'images', 'stockrecords', 'is_public', 'date_created'
        ]

#---- Serializers for writing
class StockRecordWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for the StockRecord model. Write-only fields.
    """
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.filter(is_active=True),
                                                   allow_null=True,
                                                   required=False)
    price_excl_tax = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    num_in_stock = serializers.IntegerField(required=True, min_value=0)
    partner_sku = serializers.CharField(max_length=128, required=False, allow_blank=True)
    price_currency = serializers.CharField(max_length = 12, read_only=True)

    class Meta:
        model = StockRecord
        fields = [
            'warehouse', 'partner_sku', 'price_excl_tax',
            'num_in_stock', 'price_currency',
           
        ]
    def validate_warehouse(self, value):
        """
        Validate the warehouse field.
        """
        partner = self.context.get('partner')
        if partner and value and value.partner != partner:
            raise serializers.ValidationError(_("The warehouse does not belong to the specified partner."))
        return value
    
class AttributeValueWriteSerializer(serializers.Serializer):
    """
    
    """
    code = serializers.SlugField(max_length=128, required=True, help_text= _("Attribute code (e.g. 'manufacturer', 'weight')."))
    value = serializers.JSONField(required=True, help_text=_("Attribute value (e.g. 'Sony', '1kg')."))

class ProductImageWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, help_text=_("ID of the image to update."))
    original = serializers.ImageField(required=False, allow_null=True, help_text=_("Upload a new image file."))
    display_order = serializers.IntegerField(required=False, default=0 ,help_text=_("Display order of the image."))
    caption = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text=_("Caption for the image."))

    class Meta:
        model = ProductImage
        fields = ['id', 'original', 'display_order', 'caption']
        

class ProductWriteSerializer(WritableNestedModelSerializer): # <<< Naudojam WritableNested
    """
    Serializeris produkto kūrimui ir atnaujinimui (POST, PUT, PATCH).
    Naudoja įdėtinius serializer'ius StockRecord, atributams ir paveikslėliams.
    """
    # --- Susiję objektai (rašymui) ---
    # Leidžiame perduoti TIK VIENĄ stockrecord kūrimo/atnaujinimo metu per API.
    # Jei reikėtų kelių, struktūra būtų sudėtingesnė (galbūt atskiras endpoint'as).
    stockrecord = StockRecordWriteSerializer(required=True, allow_null=False, help_text=_("Stock record data (price, quantity, warehouse, sku)"))
    # Atributus priimsime kaip sąrašą žodynų
    attributes = AttributeValueWriteSerializer(many=True, required=False, help_text=_("List of product attributes [{'code': 'attr_code', 'value': 'attr_value'}]"))
    # Paveikslėlius priimsime kaip sąrašą objektų/failų
    images = ProductImageWriteSerializer(many=True, required=False, help_text=_("List of product images"))
    # Kategorijas priimsime kaip sąrašą jų ID
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        required=False, # Ar produktas privalo turėti kategoriją?
        help_text=_("List of category IDs this product belongs to")
    )
    # Produkto klasę priimsime pagal ID arba slug
    product_class = serializers.SlugRelatedField(
        slug_field='slug', # Galima naudoti ir 'pk'
        queryset=ProductClass.objects.all(),
        required=True, # Produktas privalo turėti klasę
        help_text=_("Slug or ID of the product class (product type)")
    )

    class Meta:
        model = Product
        # Pagrindiniai produkto laukai, kuriuos leidžiame nustatyti/keisti
        fields = [
            'id', # Skaitymui
            'product_class',
            'title',
            'description',
            'upc',
            'structure', # Standalone, parent, or child
            # 'parent', # Jei naudojate child produktus (PrimaryKeyRelatedField)
            'categories',
            'attributes',
            'stockrecord',
            'images',
            # Mūsų pridėti laukai (jei jie yra Product modelyje)
            'condition',
            # Lokacijos laukai yra StockRecord/Warehouse/Partner
            'is_public', # Galima leisti tiekėjui nustatyti
        ]
        read_only_fields = ['id'] # ID tik skaitomas

    @transaction.atomic
    def create(self, validated_data):
        """
        Perrašome create metodą, kad teisingai sukurtume Product,
        StockRecord, AttributeValues ir Images.
        """
        # Išimame susijusių modelių duomenis iš validated_data
        stockrecord_data = validated_data.pop('stockrecord')
        attributes_data = validated_data.pop('attributes', [])
        images_data = validated_data.pop('images', [])
        categories_data = validated_data.pop('categories', [])

        # --- Produkto Paieška pagal UPC (kad išvengtume dublikatų) ---
        upc = validated_data.get('upc')
        product = None
        if upc:
            product = Product.objects.filter(upc=upc).first()

        # --- Partnerio gavimas iš konteksto ---
        partner = self.context['partner'] # Tikimės, kad ViewSet perduos partnerį

        if product:
            # --- Produktas RASTAS - Kuriam tik StockRecord (jei dar nėra) ---
            logger.info(f"Product with UPC {upc} found (ID: {product.pk}). Checking/Creating stock record for partner {partner.pk}.")
            stockrecord, created = StockRecord.objects.get_or_create(
                product=product,
                partner=partner,
                # Galima pridėti warehouse prie raktų, jei vienas partneris
                # gali turėti TĄ PATĮ produktą KELIUOSE sandėliuose
                # warehouse=stockrecord_data.get('warehouse'),
                defaults={
                    'partner_sku': stockrecord_data.get('partner_sku', product.upc or f'SKU-{product.pk}'),
                    'price_excl_tax': stockrecord_data['price_excl_tax'],
                    'num_in_stock': stockrecord_data['num_in_stock'],
                    'price_currency': settings.OSCAR_DEFAULT_CURRENCY,
                    'warehouse': stockrecord_data.get('warehouse') # Priskiriam sandėlį
                }
            )
            if not created:
                # Jei StockRecord jau egzistavo, galbūt atnaujinti kainą/kiekį?
                # Arba mesti klaidą? Kol kas paliekam kaip yra.
                 logger.warning(f"StockRecord for product {product.pk} and partner {partner.pk} already exists. Not updating.")
                 # Arba galite mesti klaidą:
                 # raise serializers.ValidationError(f"You already have stock for product UPC {upc}.")

            # Atributus ir paveikslėlius galime praleisti, nes produktas jau egzistuoja
            # Kategorijas galime pridėti, jei jų trūksta
            if categories_data:
                 product.categories.add(*categories_data)

        else:
            # --- Produktas NERASTAS - Kuriam naują Product ir StockRecord ---
            logger.info(f"Product with UPC {upc} not found. Creating new product for partner {partner.pk}.")
            # Sukuriame Product objektą (be susijusių M2M ir kt.)
            # WritableNestedModelSerializer pats kvies super().create()
            product = super().create(validated_data)

            # --- Sukuriame StockRecord ---
            StockRecord.objects.create(
                product=product,
                partner=partner,
                partner_sku=stockrecord_data.get('partner_sku', product.upc or f'SKU-{product.pk}'),
                price_excl_tax=stockrecord_data['price_excl_tax'],
                num_in_stock=stockrecord_data['num_in_stock'],
                price_currency=settings.OSCAR_DEFAULT_CURRENCY,
                warehouse=stockrecord_data.get('warehouse')
            )

            # --- Sukuriame/Atnaujiname Atributus ---
            self._save_attributes(product, attributes_data)

            # --- Pridedame Kategorijas ---
            if categories_data:
                 product.categories.set(categories_data)

            # --- Sukuriame Paveikslėlius ---
            self._save_images(product, images_data)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Perrašome update metodą, kad atnaujintume Product, StockRecord,
        AttributeValues ir Images.
        """
        # Išimame susijusių modelių duomenis
        # Svarbu: Naudojam .get() su numatytąja reikšme None, nes PUT/PATCH gali neatiduoti visko
        stockrecord_data = validated_data.pop('stockrecord', None)
        attributes_data = validated_data.pop('attributes', None)
        images_data = validated_data.pop('images', None)
        categories_data = validated_data.pop('categories', None)

        # --- Partnerio gavimas ---
        partner = self.context['partner']

        # --- Atnaujiname Product objektą ---
        # WritableNestedModelSerializer pats kvies super().update()
        product = super().update(instance, validated_data)

        # --- Atnaujiname StockRecord ---
        # Randame TIK ŠIO partnerio stockrecord šiam produktui
        # Jei partneris gali turėti kelis SR tam pačiam produktui (skirtinguose sandėliuose),
        # reikės perduoti ir stockrecord ID per API, kad žinotume, kurį atnaujinti.
        # Kol kas darome prielaidą, kad partneris turi tik VIENĄ SR per produktą.
        stockrecord = StockRecord.objects.filter(product=product, partner=partner).first()
        if stockrecord and stockrecord_data:
             # Atnaujiname laukus, jei jie pateikti
             stockrecord.partner_sku = stockrecord_data.get('partner_sku', stockrecord.partner_sku)
             stockrecord.price_excl_tax = stockrecord_data.get('price_excl_tax', stockrecord.price_excl_tax)
             stockrecord.num_in_stock = stockrecord_data.get('num_in_stock', stockrecord.num_in_stock)
             # Atnaujiname sandėlį (reikia validuoti, kad priklauso partneriui)
             new_warehouse = stockrecord_data.get('warehouse')
             if new_warehouse is not None: # Jei perduotas (gali būti None)
                 if new_warehouse and new_warehouse.partner != partner:
                     raise serializers.ValidationError({'stockrecord': {'warehouse': 'Invalid warehouse selected.'}})
                 stockrecord.warehouse = new_warehouse
             stockrecord.save()
        elif stockrecord_data:
             # Jei SR nėra, o duomenys pateikti - galbūt sukurti naują? Arba klaida?
             logger.warning(f"StockRecord data provided for product {product.pk} / partner {partner.pk}, but no existing StockRecord found.")

        # --- Atnaujiname Atributus ---
        if attributes_data is not None: # Tik jei atributai buvo perduoti
             self._save_attributes(product, attributes_data)

        # --- Atnaujiname Kategorijas ---
        if categories_data is not None: # Tik jei kategorijos buvo perduotos
             product.categories.set(categories_data) # set() pakeičia visas kategorijas

        # --- Atnaujiname Paveikslėlius ---
        if images_data is not None: # Tik jei paveikslėliai buvo perduoti
             self._save_images(product, images_data)

        return product


    def _save_attributes(self, product, attributes_data):
        """ Pagalbinis metodas atributams išsaugoti. """
        # Ištrinam senas reikšmes, kad būtų paprasčiau (galima daryti ir update)
        # product.attribute_values.all().delete() # <<< Atsargiai!
        # Arba darom update/create:
        valid_attributes = ProductAttribute.objects.filter(
            product_class=product.product_class
        ).values_list('code', flat=True)

        for attr_data in attributes_data:
            code = attr_data.get('code')
            value = attr_data.get('value')
            if not code or value is None: continue # Praleidžiam neteisingus duomenis

            if code not in valid_attributes:
                logger.warning(f"Attribute with code '{code}' not valid for product class '{product.product_class}'. Skipping.")
                continue

            try:
                attribute = ProductAttribute.objects.get(code=code, product_class=product.product_class)
                # Randam arba sukuriam ProductAttributeValue
                # Naudojam update_or_create, jei norim atnaujinti esamas
                attr_value_obj, created = product.attribute_values.update_or_create(
                    attribute=attribute,
                    defaults={'value': attribute.validate_value(value)} # Naudojam validavimo metodą
                )
            except ProductAttribute.DoesNotExist:
                 logger.error(f"Attribute with code '{code}' not found, although it should be valid.")
            except (ValidationError, TypeError) as e:
                 logger.error(f"Invalid value '{value}' for attribute '{code}': {e}")
            except Exception as e:
                 logger.error(f"Error saving attribute '{code}' for product {product.pk}: {e}", exc_info=True)

    def _save_images(self, product, images_data):
        """ Pagalbinis metodas paveikslėliams išsaugoti/atnaujinti. """
        # Paprasta logika: ištrinam senus, sukuriam naujus (galima daryti sudėtingiau)
        # existing_ids = {img.get('id') for img in images_data if img.get('id')}
        # product.images.exclude(id__in=existing_ids).delete() # Trinam nebeatiduotus

        for img_data in images_data:
            image_id = img_data.get('id')
            original_file = img_data.get('original')
            caption = img_data.get('caption', '')
            display_order = img_data.get('display_order', 0)

            if image_id:
                # --- Atnaujinam esamą ---
                try:
                    img_obj = product.images.get(pk=image_id)
                    if original_file: # Jei įkeltas naujas failas
                         img_obj.original = original_file
                    img_obj.caption = caption
                    img_obj.display_order = display_order
                    img_obj.save()
                except ProductImage.DoesNotExist:
                     logger.warning(f"Image with ID {image_id} not found for product {product.pk}. Skipping update.")
            elif original_file:
                 # --- Kuriam naują ---
                 product.images.create(
                     original=original_file,
                     caption=caption,
                     display_order=display_order
                 )