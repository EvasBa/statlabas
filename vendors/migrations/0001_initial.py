# Generated by Django 4.2.20 on 2025-04-10 10:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('partner', '0006_auto_20200724_0909'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('partner_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='partner.partner')),
                ('logo', models.ImageField(blank=True, help_text='Upload a logo for the vendor.', null=True, upload_to='vendor_logos/', verbose_name='Logo')),
                ('website', models.URLField(blank=True, help_text='Vendor website URL.', null=True, verbose_name='Website')),
                ('description', models.TextField(blank=True, help_text='Vendor description.', null=True, verbose_name='Description')),
                ('joined_date', models.DateTimeField(auto_now_add=True, help_text='Date when the vendor joined.', verbose_name='Joined Date')),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('verification_status', models.CharField(choices=[('pending', 'Pending'), ('verified', 'Verified'), ('rejected', 'Rejected')], default='pending', help_text='Status of vendor verification.', max_length=20, verbose_name='Verification Status')),
                ('verified_date', models.DateTimeField(blank=True, help_text='Date when the vendor was verified.', null=True, verbose_name='Verified Date')),
                ('rejection_reason', models.TextField(blank=True, help_text='Reason for vendor rejection.', null=True, verbose_name='Rejection Reason')),
                ('average_rating', models.DecimalField(decimal_places=2, default=0.0, help_text='Average rating of the vendor.', max_digits=3, verbose_name='Average Rating')),
                ('total_count', models.PositiveIntegerField(default=0, help_text='Total number of products from this vendor.', verbose_name='Total Count')),
                ('total_sales', models.DecimalField(decimal_places=2, default=0.0, help_text='Total sales amount for this vendor.', max_digits=10, verbose_name='Total Sales')),
                ('return_policy', models.TextField(blank=True, help_text='Return policy of the vendor.', null=True, verbose_name='Return Policy')),
                ('payment_terms', models.TextField(blank=True, help_text='Payment terms of the vendor.', null=True, verbose_name='Payment Terms')),
                ('update_date', models.DateTimeField(auto_now=True, help_text='Date when the vendor profile was last updated.', verbose_name='Update Date')),
                ('user', models.OneToOneField(help_text='The user account that manages this vendor profile.', on_delete=django.db.models.deletion.PROTECT, related_name='vendor_profile', to=settings.AUTH_USER_MODEL, verbose_name='Associated User Account')),
            ],
            options={
                'verbose_name': 'Vendor',
                'verbose_name_plural': 'Vendors',
                'ordering': ['name'],
            },
            bases=('partner.partner',),
        ),
        migrations.AddConstraint(
            model_name='vendor',
            constraint=models.UniqueConstraint(fields=('user',), name='unique_vendor_user_association'),
        ),
    ]
