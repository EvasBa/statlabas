from django.db import models
# from django.utils.translation import gettext_lazy as _
# from oscar.apps.catalogue.abstract_models import AbstractProduct, AbstractCategory

# class Product(AbstractProduct):
#     """
#     Custom Product model that extends the default Oscar Product model.
#     """
#     vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='products')

#     class Meta(AbstractProduct.Meta):
#         verbose_name = _('product')
#         verbose_name_plural = _('products')


# # Import all the models from Oscar's catalogue app
from oscar.apps.catalogue.models import *  # noqa isort:skip