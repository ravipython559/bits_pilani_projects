# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-06-21 12:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_rest', '0005_zestemitransaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='down_payment_amount',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='down_payment_rate',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='interest_amount',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='interest_free_months',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='interest_rate',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='loan_amount',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='number_of_months',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='processing_fee',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='processing_fee_rate',
        ),
        migrations.RemoveField(
            model_name='zestemitransaction',
            name='total_monthly_amount',
        ),
        migrations.AddField(
            model_name='zestemitransaction',
            name='amount_approved',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='zestemitransaction',
            name='amount_requested',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
