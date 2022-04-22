# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2018-03-23 10:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0064_auto_20180316_1741'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicantexceptions',
            name='offer_letter',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro-SIM'), ('offer_pdf/wipro_wims.html', 'Wipro-WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro-WASE'), ('offer_pdf/cluster.html', 'Cluster Offer Letter'), ('offer_pdf/cluster1.html', 'Cluster Offer Letter 1'), ('offer_pdf/cluster_pg_2018.html', 'Cluster Program Offer Letter - 2018'), ('offer_pdf/bosch_man.html', 'Bosch Offer Letter Manufacturing'), ('offer_pdf/bosch_pg_man.html', 'Bosch Offer Letter PG Diploma Manufacturing'), ('offer_pdf/mtech_pom_mum_hyd.html', 'M.Tech POM Offer Letter-Mumbai-Hyd'), ('offer_pdf/mtech_pom_ahmd.html', 'M.Tech POM Offer Letter-Ahmedabad'), ('offer_pdf/embedded_sys_cluster.html', 'Embedded System Cluster Offer Letter 2017-18 Sem1'), ('offer_pdf/bosch_iti.html', 'Bosch Offer Letter-ITI Applicants'), ('offer_pdf/iot_certificate.html', 'IOT Certification Offer Letter'), ('offer_pdf/iot_certificate_cohort_2.html', 'IOT Certification Offer Letter Cohort - 2')], max_length=100, null=True, verbose_name='Choose custom offer letter template, if applicable'),
        ),
        migrations.AlterField(
            model_name='candidateselection',
            name='offer_letter_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro-SIM'), ('offer_pdf/wipro_wims.html', 'Wipro-WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro-WASE'), ('offer_pdf/cluster.html', 'Cluster Offer Letter'), ('offer_pdf/cluster1.html', 'Cluster Offer Letter 1'), ('offer_pdf/cluster_pg_2018.html', 'Cluster Program Offer Letter - 2018'), ('offer_pdf/bosch_man.html', 'Bosch Offer Letter Manufacturing'), ('offer_pdf/bosch_pg_man.html', 'Bosch Offer Letter PG Diploma Manufacturing'), ('offer_pdf/mtech_pom_mum_hyd.html', 'M.Tech POM Offer Letter-Mumbai-Hyd'), ('offer_pdf/mtech_pom_ahmd.html', 'M.Tech POM Offer Letter-Ahmedabad'), ('offer_pdf/embedded_sys_cluster.html', 'Embedded System Cluster Offer Letter 2017-18 Sem1'), ('offer_pdf/bosch_iti.html', 'Bosch Offer Letter-ITI Applicants'), ('offer_pdf/iot_certificate.html', 'IOT Certification Offer Letter'), ('offer_pdf/iot_certificate_cohort_2.html', 'IOT Certification Offer Letter Cohort - 2')], max_length=45, null=True),
        ),
        migrations.AlterField(
            model_name='program',
            name='offer_letter_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro-SIM'), ('offer_pdf/wipro_wims.html', 'Wipro-WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro-WASE'), ('offer_pdf/cluster.html', 'Cluster Offer Letter'), ('offer_pdf/cluster1.html', 'Cluster Offer Letter 1'), ('offer_pdf/cluster_pg_2018.html', 'Cluster Program Offer Letter - 2018'), ('offer_pdf/bosch_man.html', 'Bosch Offer Letter Manufacturing'), ('offer_pdf/bosch_pg_man.html', 'Bosch Offer Letter PG Diploma Manufacturing'), ('offer_pdf/mtech_pom_mum_hyd.html', 'M.Tech POM Offer Letter-Mumbai-Hyd'), ('offer_pdf/mtech_pom_ahmd.html', 'M.Tech POM Offer Letter-Ahmedabad'), ('offer_pdf/embedded_sys_cluster.html', 'Embedded System Cluster Offer Letter 2017-18 Sem1'), ('offer_pdf/bosch_iti.html', 'Bosch Offer Letter-ITI Applicants'), ('offer_pdf/iot_certificate.html', 'IOT Certification Offer Letter'), ('offer_pdf/iot_certificate_cohort_2.html', 'IOT Certification Offer Letter Cohort - 2')], max_length=45, null=True),
        ),
    ]
