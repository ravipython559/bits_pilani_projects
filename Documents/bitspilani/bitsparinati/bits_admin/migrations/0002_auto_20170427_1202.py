# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-04-27 06:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidateselectionarchived',
            name='dps_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidateselectionarchived',
            name='dps_flag',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='studentcandidateapplicationarchived',
            name='address_line_1',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='studentcandidateapplicationarchived',
            name='address_line_2',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='studentcandidateapplicationarchived',
            name='address_line_3',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='studentcandidateapplicationarchived',
            name='first_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='studentcandidateapplicationarchived',
            name='last_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='studentcandidateapplicationarchived',
            name='middle_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]