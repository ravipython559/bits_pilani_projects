# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2019-08-28 13:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bits_admin', '0045_auto_20190827_1319'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AdhocMetaZestArchived',
            new_name='AdhocMetaEmiArchived',
        ),
    ]
