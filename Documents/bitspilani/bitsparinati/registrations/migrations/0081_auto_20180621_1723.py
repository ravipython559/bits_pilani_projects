# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-06-21 11:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0080_applicationdocument_program_document_map'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='firstsemcourselist',
            options={'ordering': ['course'], 'verbose_name': 'Course List', 'verbose_name_plural': 'Course List'},
        ),
        migrations.RenameField(
            model_name='firstsemcourselist',
            old_name='course_id',
            new_name='course',
        ),
    ]
