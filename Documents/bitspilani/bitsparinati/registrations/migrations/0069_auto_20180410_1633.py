# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-04-10 11:03
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0068_auto_20180406_1710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otherfeepayment',
            name='fee_amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]),
        ),
    ]
