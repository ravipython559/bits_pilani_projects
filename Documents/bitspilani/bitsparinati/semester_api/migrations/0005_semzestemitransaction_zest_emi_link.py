# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2021-05-08 06:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('semester_api', '0004_sempaytmtransactions'),
    ]

    operations = [
        migrations.AddField(
            model_name='semzestemitransaction',
            name='zest_emi_link',
            field=models.TextField(blank=True, null=True),
        ),
    ]