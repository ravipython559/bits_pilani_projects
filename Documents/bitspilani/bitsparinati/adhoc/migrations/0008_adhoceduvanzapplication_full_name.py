# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2019-09-06 06:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adhoc', '0007_auto_20190828_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='adhoceduvanzapplication',
            name='full_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
