# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2019-04-02 13:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0102_auto_20190402_1904'),
        ('adhoc', '0002_auto_20190322_1622'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adhoczestemitransaction',
            name='cancelled_on',
        ),
        migrations.RemoveField(
            model_name='adhoczestemitransaction',
            name='is_cancelled',
        ),
        migrations.AddField(
            model_name='adhoczestemitransaction',
            name='fee_type',
            field=models.CharField(default='x', max_length=45),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='adhoczestemitransaction',
            name='program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='adhoczestemitransaction_prog', to='registrations.Program'),
        ),
    ]
