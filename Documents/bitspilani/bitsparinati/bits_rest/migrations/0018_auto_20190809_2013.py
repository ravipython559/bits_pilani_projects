# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2019-08-09 14:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bits_rest', '0017_eduvanzapplication_paytmhistory'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eduvanzapplication',
            old_name='approved_on',
            new_name='approved_or_rejected_on',
        ),
    ]
