# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2019-10-09 07:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0046_auto_20190828_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentcandidateapplicationarchived',
            name='alternate_email_id',
            field=models.EmailField(blank=True, max_length=50, null=True),
        ),
    ]
