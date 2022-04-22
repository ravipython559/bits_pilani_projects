# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-09-15 11:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0047_auto_20170908_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicantexceptions',
            name='offer_letter',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro-SIM'), ('offer_pdf/wipro_wims.html', 'Wipro-WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro-WASE'), ('offer_pdf/cluster.html', 'Cluster Offer Letter'), ('offer_pdf/cluster1.html', 'Cluster Offer Letter 1')], max_length=100, null=True, verbose_name='Choose custom offer letter template, if applicable'),
        ),
        migrations.AlterField(
            model_name='program',
            name='offer_letter_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro-SIM'), ('offer_pdf/wipro_wims.html', 'Wipro-WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro-WASE'), ('offer_pdf/cluster.html', 'Cluster Offer Letter'), ('offer_pdf/cluster1.html', 'Cluster Offer Letter 1')], max_length=45, null=True),
        ),
    ]