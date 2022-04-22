# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-03-06 06:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0020_auto_20161226_1459'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='program',
            name='organization_name',
        ),
        migrations.AlterField(
            model_name='program',
            name='offer_letter_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/Specific-program-template.html', 'Specific-program template')], max_length=45, null=True),
        ),
    ]