# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-03-15 11:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0014_auto_20180315_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentcandidateapplicationarchived',
            name='admit_batch',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='studentcandidateapplicationarchived',
            name='admit_sem_cohort',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
