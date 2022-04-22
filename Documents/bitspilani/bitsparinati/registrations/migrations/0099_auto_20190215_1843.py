# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2019-02-15 13:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0098_studentcandidateapplication_teaching_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='program',
            name='application_pdf_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('app_pdf/oracle-pdf.html', 'Oracle'), ('app_pdf/wipro-pdf.html', 'Wipro'), ('app_pdf/specific-pdf.html', 'Specific Program Application Template'), ('app_pdf/hcl_org.html', 'HCL Collaboration')], max_length=60, null=True),
        ),
        migrations.AlterField(
            model_name='program',
            name='document_upload_page_path',
            field=models.CharField(blank=True, choices=[(None, 'Choose Document To Upload'), ('guidelines_document/oracle.html', 'Oracle'), ('guidelines_document/wipro.html', 'Wipro'), ('guidelines_document/certification_programs.html', 'Certification Programs'), ('guidelines_document/hcl_org.html', 'HCL Collaboration')], max_length=100, null=True),
        ),
    ]