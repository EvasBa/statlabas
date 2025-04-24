from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.catalogue.abstract_models import (
    AbstractProduct,
    AbstractCategory,
    AbstractProductAttribute,
    AbstractProductAttributeValue,
    AbstractAttributeOption,
    AbstractAttributeOptionGroup,
    AbstractOption
)

class Product(AbstractProduct):
    """
    Custom Product model that extends Oscar's AbstractProduct
    """
    CONDITION_NEW = 'new'
    CONDITION_USED = 'used'
    CONDITION_SLIGHTLY_DAMAGED = 'slightly_damaged'
    CONDITION_DAMAGED = 'damaged'
    CONDITION_CHOICES = [
        (CONDITION_NEW, _('New')),
        (CONDITION_USED, _('Used')),
        (CONDITION_SLIGHTLY_DAMAGED, _('Slightly Damaged')),
        (CONDITION_DAMAGED, _('Damaged')),
    ]
    
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default=CONDITION_NEW,
        verbose_name=_('Condition')
    )

class Category(AbstractCategory):
    pass

class ProductAttribute(AbstractProductAttribute):
    pass

class ProductAttributeValue(AbstractProductAttributeValue):
    pass

class AttributeOption(AbstractAttributeOption):
    pass

class AttributeOptionGroup(AbstractAttributeOptionGroup):
    pass

class Option(AbstractOption):
    pass

# Must come after model definitions
from oscar.apps.catalogue.models import *  # noqa isort:skip