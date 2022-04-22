# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-09-08 14:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0046_auto_20170908_1717'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentcandidateapplication',
            name='first_name',
            field=models.CharField(blank=True, max_length=25, null=True, verbose_name='First Name'),
        ),
        migrations.AlterField(
            model_name='studentcandidateapplication',
            name='full_name',
            field=models.CharField(max_length=100, verbose_name='Full Name'),
        ),
    ]
