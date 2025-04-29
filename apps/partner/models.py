from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from oscar.apps.partner.abstract_models import AbstractStockRecord, AbstractPartner
from django.contrib.gis.db import models


class Partner(AbstractPartner):
    """
    Extending Partner model
    """
    # Add status constants
    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_REJECTED = 'rejected'
    
    VERIFICATION_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_VERIFIED, _('Verified')),
        (STATUS_REJECTED, _('Rejected')),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='partner_profile',
        null=True,
        help_text=_('User associated with this partner.'),
        blank=True
    )
    logo = models.ImageField(
        _('Logo'),
        upload_to='partner_logos/',
        blank=True,
        null=True,
        help_text=_('Upload a logo for the partner.')
    )
    website = models.URLField(
        _('Website'),
        blank=True,
        null=True,
        help_text=_('Partner website URL.')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        null=True,
        help_text=_('Partner description.')
    )

    return_policy = models.TextField(
        _('Return Policy'),
        blank=True,
        null=True,
        help_text=_('Partner return policy.')
    )

    default_location = models.PointField(
        _('Default Location'),
        null=True,
        blank=True,
        help_text=_('Default location of the partner.'),
        srid=4326,
    )

    verification_status = models.CharField(
        _('Verification Status'),
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default=STATUS_PENDING,
        help_text=_('Status of partner verification.')
    )

    joined_date = models.DateTimeField(
        _('Joined Date'),
        auto_now_add=True,
        help_text=_('Date when the partner joined.'),
        #default=timezone.now,
        null=True,
        
    )
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text=_('Date when the partner profile was last updated.')
    )

    class Meta:
        app_label = 'partner'
        ordering = ['name']
        verbose_name = _('Partner')
        verbose_name_plural = _('Partners')
        
    def __str__(self):
        if self.user and hasattr(self.user, 'company_profile'):
            return self.user.company_profile.company_name
        if self.user:
            return f"{self.user.get_full_name() or self.user.email}"
        return self.name or "Unknown Partner"
    
    def get_display_name(self):
        return str(self)
    
    @property
    def is_verified(self):
        return self.verification_status == self.STATUS_VERIFIED
    


class StockRecord(AbstractStockRecord):
    """
    Custom StockRecord model that extends Oscar's AbstractStockRecord
    """
    warehouse = models.ForeignKey(
        'locations.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_records',
        verbose_name=_('Warehouse')
    )

    class Meta:
        app_label = 'partner'
        verbose_name = _('Partner Stock Record')
        verbose_name_plural = _('Partner Stock Records')

# Import all the models from Oscar's partner app - THIS MUST COME LAST
from oscar.apps.partner.models import *  # noqa isort:skip