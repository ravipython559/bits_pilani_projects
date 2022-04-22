# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2021-06-09 10:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0148_auto_20210528_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='document_submission_flag',
            field=models.BooleanField(default=False, verbose_name='Allow Submission and Re-submission of Documents by Applicants'),
        ),
    ]
