# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-04-17 07:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_rest', '0003_metaadhocpayment_adhoc_error'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metaadhocpayment',
            name='email',
            field=models.EmailField(max_length=254),
        ),
    ]