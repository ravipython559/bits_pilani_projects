# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2021-01-27 02:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adhoc', '0012_adhocpropelldapplication'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adhoceduvanzapplication',
            name='status_code',
            field=models.CharField(choices=[(None, '-'), ('New Loan Application', 'New Loan Application'), ('ELS101', 'LAF Pending'), ('ELS102', 'Documents Pending'), ('ELS201', 'Under Approval'), ('ELS202', 'Approved'), ('ELS203', 'Processing Fee Paid'), ('ELS204', '1st EMI Paid'), ('ELS205', 'Both Processing Fee & 1st EMI Paid'), ('ELS206', 'Agreement Signed'), ('ELS207', 'NACH Received'), ('ELS208', 'NACH Under Activation Process'), ('ELS209', 'NACH Activated'), ('ELS210', 'Disbursal Initiated'), ('ELS211', 'Down Payment Paid'), ('ELS301', 'Disbursed'), ('ELS401', 'Rejected'), ('ELS402', 'Dropped'), ('FAILED', 'Applicant Cancelled')], default='New Loan Application', max_length=25),
        ),
    ]
