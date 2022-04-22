# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-09-12 13:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0009_auto_20170912_1837'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationpaymentarchived',
            name='inserted_from_gateway_file',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='applicationpaymentarchived',
            name='insertion_approved_by',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='applicationpaymentarchived',
            name='insertion_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='applicationpaymentarchived',
            name='manual_upload_flag',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='applicationpaymentarchived',
            name='matched_with_payment_gateway',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='applicationpaymentarchived',
            name='missing_from_gateway_file',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='applicationpaymentarchived',
            name='tpsl_transaction',
            field=models.CharField(blank=True, max_length=45, null=True),
        ),
    ]