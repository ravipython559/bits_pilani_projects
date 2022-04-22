# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-09-03 12:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0002_auto_20170427_1202'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicantExceptionsArchived',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applicant_email', models.EmailField(max_length=254, verbose_name='Applicant email ID / user ID')),
                ('program', models.CharField(blank=True, max_length=50, null=True)),
                ('work_ex_waiver', models.BooleanField(default=False, verbose_name='Work Experience waiver required?')),
                ('employment_waiver', models.BooleanField(default=False, verbose_name='Employment waiver required (candidate can be unemployed while applying)?')),
                ('mentor_waiver', models.BooleanField(default=False, verbose_name='Mentor details not required to be provided?')),
                ('offer_letter', models.CharField(blank=True, max_length=50, null=True)),
                ('hr_contact_waiver', models.BooleanField(default=False, verbose_name='HR contact details not required to be provided?')),
                ('org', models.CharField(blank=True, max_length=50, null=True)),
                ('created_on_datetime', models.DateTimeField(auto_now_add=True)),
                ('transfer_program', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
    ]
