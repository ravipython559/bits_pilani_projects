# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2020-07-07 07:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0051_candidateselectionarchived_offer_letter'),
    ]

    operations = [
        migrations.AddField(
            model_name='adhoczestemitransactionarchived',
            name='zest_emi_link',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='zestemitransactionarchived',
            name='zest_emi_link',
            field=models.TextField(blank=True, null=True),
        ),
    ]
