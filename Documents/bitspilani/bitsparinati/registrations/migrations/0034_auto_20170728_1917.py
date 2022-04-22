# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-07-28 13:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0033_auto_20170609_1142'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='program',
            options={'ordering': ['program_code']},
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='acad_contact_person',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='acad_contact_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='eg +918326974266', max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='adm_fees',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='admin_contact_person',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='admin_contact_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, help_text='eg +918326974266', max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='doc_resubmission_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='fee_payment_deadline_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='lecture_start_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='lecture_venue',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='offer_letter_generated_flag',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='offer_letter_regenerated_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='orientation_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidateselection',
            name='orientation_venue',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='exceptionlistorgapplicants',
            name='application',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exceptionlistorgapplicants_app', to='registrations.StudentCandidateApplication'),
        ),
    ]
