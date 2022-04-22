# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-07-24 13:52
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MetaZest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=50)),
                ('errors', jsonfield.fields.JSONField(blank=True, null=True)),
                ('created_on_datetime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ZestEmiTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=50)),
                ('order_id', models.TextField()),
                ('customer_id', models.TextField()),
                ('requested_on', models.DateTimeField()),
                ('is_application_complete', models.BooleanField(default=False)),
                ('approved_or_rejected_on', models.DateTimeField(blank=True, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('is_terms_and_condition_accepted', models.BooleanField(default=False)),
                ('req_json_data', jsonfield.fields.JSONField(blank=True, null=True)),
                ('amount_requested', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('amount_approved', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('status', models.CharField(blank=True, choices=[(None, b'-'), (b'RiskPending', b'RiskPending'), (b'RiskApproved', b'RiskApproved'), (b'OutOfStock', b'OutOfStock'), (b'BankAccountDetailsComplete', b'BankAccountDetailsComplete'), (b'ApplicationInProgress', b'ApplicationInProgress'), (b'CustomerCancelled', b'CustomerCancelled'), (b'InArrears', b'InArrears'), (b'WrittenOff', b'WrittenOff'), (b'Closed', b'Closed'), (b'Cancelled', b'Cancelled'), (b'Approved', b'Approved'), (b'Referred', b'Referred'), (b'DocumentsComplete', b'DocumentsComplete'), (b'DepositPaid', b'DepositPaid'), (b'LoanAgreementAccepted', b'LoanAgreementAccepted'), (b'Declined', b'Declined'), (b'PreAccepted', b'PreAccepted'), (b'TimeoutCancelled', b'TimeoutCancelled'), (b'MerchantCancelled', b'MerchantCancelled'), (b'Active', b'Active')], max_length=50, null=True)),
            ],
        ),
    ]
