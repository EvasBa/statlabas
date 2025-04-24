# Oscar API Serializer Notes and Improvements

## 1. Performance Optimizations

### Add Select Related/Prefetch Related
```python
def to_representation(self, instance):
    instance = instance.select_related(
        'product_class',
        'parent'
    ).prefetch_related(
        'categories',
        'images',
        'attribute_values__attribute',
        'stockrecords__partner',
        'stockrecords__warehouse'
    ).get(pk=instance.pk)
    return super().to_representation(instance)
```

### Add Caching for Heavy Queries
```python
def get_cached_categories(self):
    cache_key = f'product_categories_{self.pk}'
    cached_data = cache.get(cache_key)
    if not cached_data:
        cached_data = self.categories.all()
        cache.set(cache_key, cached_data, timeout=3600)
    return cached_data
```

## 2. Data Validation

### Price Validation
```python
def validate_price_excl_tax(self, value):
    if value <= 0:
        raise serializers.ValidationError(_("Price must be greater than zero"))
    return value
```

### Stock Level Validation
```python
def validate_stockrecord(self, attrs):
    num_in_stock = attrs.get('num_in_stock', 0)
    num_allocated = attrs.get('num_allocated', 0)
    if num_allocated > num_in_stock:
        raise serializers.ValidationError("Cannot allocate more than stock level")
    return attrs
```

## 3. Security Improvements

### Owner Verification
```python
def validate(self, attrs):
    request = self.context.get('request')
    if not request.user.is_staff and request.user.partner != self.instance.partner:
        raise serializers.ValidationError("Not authorized to modify this product")
    return attrs
```

## 4. Image Handling Improvements

### Better Image Processing
```python
def _save_images(self, product, images_data):
    existing_ids = set(product.images.values_list('id', flat=True))
    submitted_ids = {img.get('id') for img in images_data if img.get('id')}
    
    # Delete removed images
    to_delete = existing_ids - submitted_ids
    if to_delete:
        product.images.filter(id__in=to_delete).delete()
        
    # Update or create images
    for img_data in images_data:
        if img_data.get('id'):
            self._update_image(product, img_data)
        else:
            self._create_image(product, img_data)
```

## 5. Future Improvements

1. Add version control for products
2. Implement soft delete
3. Add bulk operations support
4. Add product variant handling
5. Implement price history tracking
6. Add stock level notifications
7. Implement product status workflow

## 6. Testing Recommendations

1. Test price calculations
2. Test stock level management
3. Test image upload/update/delete
4. Test category relationships
5. Test attribute validation
6. Test partner permissions

## 7. Documentation TODOs

1. API endpoint documentation
2. Authentication requirements
3. Rate limiting information
4. Example requests/responses
5. Error handling documentation