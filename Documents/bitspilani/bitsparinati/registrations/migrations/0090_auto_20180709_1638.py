# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-07-09 11:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0089_auto_20180709_1314'),
    ]

    operations = [
        migrations.RenameField(
            model_name='otherfeepayment',
            old_name='application_id',
            new_name='student_application_id',
        ),
    ]