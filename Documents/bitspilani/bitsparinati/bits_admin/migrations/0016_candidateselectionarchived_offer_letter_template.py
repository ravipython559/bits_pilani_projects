# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-03-23 10:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0015_auto_20180315_1722'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidateselectionarchived',
            name='offer_letter_template',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
