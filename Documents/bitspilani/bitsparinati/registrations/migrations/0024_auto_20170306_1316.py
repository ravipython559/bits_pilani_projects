# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-03-06 07:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0023_auto_20170306_1214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='program',
            name='admit_sem_des',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Admit Semester Description'),
        ),
    ]