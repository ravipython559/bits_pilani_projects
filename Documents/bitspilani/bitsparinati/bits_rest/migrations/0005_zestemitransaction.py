# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-06-20 08:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0080_applicationdocument_program_document_map'),
        ('bits_rest', '0004_auto_20180417_1314'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZestEmiTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.TextField()),
                ('customer_id', models.TextField()),
                ('requested_on', models.DateTimeField()),
                ('is_application_complete', models.BooleanField(default=False)),
                ('approved_or_rejected_on', models.DateTimeField(blank=True, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('is_terms_and_condition_accepted', models.BooleanField(default=False)),
                ('number_of_months', models.PositiveIntegerField(blank=True, null=True)),
                ('total_monthly_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('interest_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('interest_free_months', models.PositiveIntegerField(blank=True, null=True)),
                ('loan_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('down_payment_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('processing_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('processing_fee_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('down_payment_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('interest_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zestemitransaction_1', to='registrations.StudentCandidateApplication')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zestemitransaction_2', to='registrations.Program')),
            ],
        ),
    ]
