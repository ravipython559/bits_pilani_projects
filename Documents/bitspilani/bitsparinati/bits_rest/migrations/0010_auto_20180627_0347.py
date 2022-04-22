# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-06-26 22:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_rest', '0009_auto_20180627_0151'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zestemitransaction',
            name='status',
            field=models.CharField(blank=True, choices=[(None, b'No status'), (b'RiskPending', b'RiskPending'), (b'RiskApproved', b'RiskApproved'), (b'OutOfStock', b'OutOfStock'), (b'BankAccountDetailsComplete', b'BankAccountDetailsComplete'), (b'ApplicationInProgress', b'ApplicationInProgress'), (b'CustomerCancelled', b'CustomerCancelled'), (b'InArrears', b'InArrears'), (b'WrittenOff', b'WrittenOff'), (b'Closed', b'Closed'), (b'Cancelled', b'Cancelled'), (b'Approved', b'Approved'), (b'Referred', b'Referred'), (b'DocumentsComplete', b'DocumentsComplete'), (b'DepositPaid', b'DepositPaid'), (b'LoanAgreementAccepted', b'LoanAgreementAccepted'), (b'Declined', b'Declined'), (b'PreAccepted', b'PreAccepted'), (b'TimeoutCancelled', b'TimeoutCancelled'), (b'MerchantCancelled', b'MerchantCancelled')], max_length=50, null=True),
        ),
    ]
