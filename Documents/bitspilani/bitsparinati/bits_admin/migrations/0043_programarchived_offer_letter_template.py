# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2019-05-16 11:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0042_auto_20190509_1426'),
    ]

    operations = [
        migrations.AddField(
            model_name='programarchived',
            name='offer_letter_template',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
    ]
