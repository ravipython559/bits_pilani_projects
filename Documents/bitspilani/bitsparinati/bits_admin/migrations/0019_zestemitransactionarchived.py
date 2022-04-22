# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-09-03 12:02
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0018_auto_20180601_1152'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZestEmiTransactionArchived',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('run', models.PositiveIntegerField()),
                ('application', models.CharField(blank=True, max_length=20, null=True)),
                ('program', models.CharField(blank=True, max_length=50, null=True)),
                ('order_id', models.TextField(blank=True, null=True)),
                ('customer_id', models.TextField(blank=True, null=True)),
                ('requested_on', models.DateTimeField(blank=True, null=True)),
                ('is_application_complete', models.BooleanField(default=False)),
                ('approved_or_rejected_on', models.DateTimeField(blank=True, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('is_terms_and_condition_accepted', models.BooleanField(default=False)),
                ('req_json_data', jsonfield.fields.JSONField(blank=True, null=True)),
                ('amount_requested', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('amount_approved', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
    ]