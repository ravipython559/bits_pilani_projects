# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-04-03 13:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0026_auto_20170403_1920'),
    ]

    operations = [
        migrations.AddField(
            model_name='documenttype',
            name='n_v_flag',
            field=models.BooleanField(default=False, verbose_name='use for name verification'),
        ),
    ]
