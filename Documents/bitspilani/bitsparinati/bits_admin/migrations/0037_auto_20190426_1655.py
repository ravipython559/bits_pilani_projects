# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2019-04-26 11:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0036_exceptionlistorgapplicantsarchived_application'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studentcandidatequalificationarchived',
            old_name='degree',
            new_name='degree_pk',
        ),
    ]