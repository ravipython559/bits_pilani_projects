# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-06-15 06:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0074_applicationdocument_program_document_map'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentelectiveselection',
            name='course_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='studentelectiveselection_6', to='registrations.ElectiveCourseList'),
        ),
    ]
