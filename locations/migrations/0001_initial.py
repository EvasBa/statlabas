# Generated by Django 4.2.20 on 2025-04-23 09:43

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('partner', '0006_auto_20200724_0909'),
    ]

    operations = [
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text="A name for this location, e.g., 'Main Warehouse', 'Kaunas Pickup Point'.", max_length=150, verbose_name='Warehouse/Location Name')),
                ('address_line', models.CharField(help_text='Street address and number.', max_length=255, verbose_name='Address Line')),
                ('city', models.CharField(db_index=True, max_length=100, verbose_name='City')),
                ('zip_code', models.CharField(blank=True, max_length=20, verbose_name='Zip/Post Code')),
                ('country', models.CharField(help_text='Country name.', max_length=100, verbose_name='Country')),
                ('location', django.contrib.gis.db.models.fields.PointField(blank=True, db_index=True, editable=False, help_text='Geographic coordinates (longitude, latitude), set automatically from address.', null=True, srid=4326, verbose_name='Location Coordinates')),
                ('phone', models.CharField(blank=True, max_length=30, verbose_name='Warehouse Phone')),
                ('is_pickup_available', models.BooleanField(default=True, verbose_name='Pickup Available From Here?')),
                ('operating_hours', models.TextField(blank=True, verbose_name='Operating Hours')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Is Active?')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('partner', models.ForeignKey(help_text='The partner that owns this warehouse.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='warehouses', to='partner.partner', verbose_name='Partner/Vendor')),
            ],
            options={
                'verbose_name': 'Warehouse',
                'verbose_name_plural': 'Warehouses',
                'ordering': ['name'],
            },
        ),
    ]
