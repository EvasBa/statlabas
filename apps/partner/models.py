from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.partner.abstract_models import AbstractStockRecord

class StockRecord(AbstractStockRecord):
    """
    Custom StockRecord model that extends Oscar's AbstractStockRecord
    """
    warehouse = models.ForeignKey(
        'warehouses.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_records',
        verbose_name=_('Warehouse')
    )

    class Meta:
        app_label = 'partner'
        verbose_name = _('Stock record')
        verbose_name_plural = _('Stock records')

# Import all the models from Oscar's partner app - THIS MUST COME LAST
from oscar.apps.partner.models import * # noqa isort:skip