# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-10-22 11:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_rest', '0015_auto_20180703_1356'),
    ]

    operations = [
        migrations.AddField(
            model_name='zestemitransaction',
            name='cancelled_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='zestemitransaction',
            name='is_cancelled',
            field=models.BooleanField(default=False),
        ),
    ]
