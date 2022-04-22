# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2020-08-03 08:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0128_auto_20200721_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='program',
            name='application_pdf_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('app_pdf/oracle-pdf.html', 'Oracle'), ('app_pdf/wipro-pdf.html', 'Wipro'), ('app_pdf/specific-pdf.html', 'Specific Program Application Template'), ('app_pdf/hcl_org.html', 'HCL Collaboration - BSc Program'), ('app_pdf/delloitte1-pdf.html', 'Delloitte Application Form Template-1'), ('app_pdf/SAP_Application_form2020-21.html', 'SAP Application form 2020-21')], max_length=60, null=True),
        ),
    ]
