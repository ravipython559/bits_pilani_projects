# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-04-26 12:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0027_documenttype_n_v_flag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exceptionlistorgapplicants',
            name='employee_email',
            field=models.EmailField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='exceptionlistorgapplicants',
            name='exception_type',
            field=models.CharField(choices=[(None, 'FEE TYPE'), ('1', 'APPLICATION FEE'), ('2', 'ADMISSION FEE')], db_index=True, max_length=2),
        ),
        migrations.AlterField(
            model_name='program',
            name='application_pdf_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('app_pdf/oracle-pdf.html', 'Oracle'), ('app_pdf/wipro-pdf.html', 'Wipro')], max_length=45, null=True),
        ),
        migrations.AlterField(
            model_name='program',
            name='document_upload_page_path',
            field=models.CharField(blank=True, choices=[(None, 'Choose Document To Upload'), ('guidelines_document/oracle.html', 'Oracle'), ('guidelines_document/wipro.html', 'Wipro')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='program',
            name='offer_letter_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro - SIM'), ('offer_pdf/wipro_wims.html', 'Wipro - WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro - WASE')], max_length=45, null=True),
        ),
    ]
