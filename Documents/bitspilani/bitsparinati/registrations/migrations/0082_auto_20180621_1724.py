# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-06-21 11:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0081_auto_20180621_1723'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='firstsemcourselist',
            options={'ordering': ['course_id'], 'verbose_name': 'Course List', 'verbose_name_plural': 'Course List'},
        ),
        migrations.RenameField(
            model_name='firstsemcourselist',
            old_name='course',
            new_name='course_id',
        ),
    ]