# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2021-08-23 08:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0152_auto_20210820_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicantexceptions',
            name='offer_letter',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/non-specific-sem2-2018-19.html', 'Non-Specific 2018-19'), ('offer_pdf/non-specific-2019-2020.html', 'Non-Specific 2019-20'), ('offer_pdf/mahindra_vehicles2019_20.html', 'Offer letter Mahindra Vehicles - 2019-20'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/spc-pgm-2018-19.html', 'Specific 2018-19'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro-SIM'), ('offer_pdf/wipro_wims.html', 'Wipro-WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro-WASE'), ('offer_pdf/cluster.html', 'Cluster Offer Letter'), ('offer_pdf/cluster1.html', 'Cluster Offer Letter 1'), ('offer_pdf/cluster_pg_2018.html', 'Cluster Program Offer Letter - 2018'), ('offer_pdf/cluster_pg_2018_2019.html', 'Cluster 2018-19'), ('offer_pdf/cluster_pg_mtech_dt_sc_2018_19.html', 'Cluster Offer Letter - MTech Data Science 2018-19'), ('offer_pdf/bosch_man.html', 'Bosch Offer Letter Manufacturing'), ('offer_pdf/bosch_pg_man.html', 'Bosch Offer Letter PG Diploma Manufacturing'), ('offer_pdf/mtech_pom_mum_hyd.html', 'M.Tech POM Offer Letter-Mumbai-Hyd'), ('offer_pdf/mtech_pom_ahmd.html', 'M.Tech POM Offer Letter-Ahmedabad'), ('offer_pdf/embedded_sys_cluster.html', 'Embedded System Cluster Offer Letter 2017-18 Sem1'), ('offer_pdf/iot_certificate.html', 'IOT Certification Offer Letter'), ('offer_pdf/iot_certificate_cohort_2.html', 'IOT Certification Offer Letter Cohort - 2'), ('offer_pdf/iot_certificate_cohort_3.html', 'CIOT Offer Letter 2018 Cohort 1'), ('offer_pdf/iot_certificate_revised.html', 'IOT Offer Letter Revised'), ('offer_pdf/wipro_wase_2017-18_sem2.html', 'Wipro-WASE-2017-18-Sem2'), ('offer_pdf/wipro_wims_2017-18_sem2.html', 'Wipro-WIMS-2017-18-Sem2'), ('offer_pdf/wipro_wims_2018-19_sem2.html', 'Wipro-WIMS-2018-19-Sem2'), ('offer_pdf/wipro_wims_2019-20_sem2.html', 'Wipro-WIMS-2019-20-Sem2'), ('offer_pdf/wipro_wims_2020-21_sem1.html', 'Wipro-WIMS-2020-21'), ('offer_pdf/wipro_wase_2020-21_sem1.html', 'Wipro-WASE-2020-21'), ('offer_pdf/sap_offer_hs70_2018-1_sem.html', 'SAP Offer Letter HS70 2018-1 Sem'), ('offer_pdf/sap_offer_sp93_2018-1_sem.html', 'SAP Offer Letter SP93 2018-1 Sem'), ('offer_pdf/vmware_offer_letter.html', 'VMWare Offer Letter'), ('offer_pdf/mtech_dt_sc_engg_2018_19.html', 'Cluster Offer Letter - MTech in Data Science - with readiness exam 2018-19'), ('offer_pdf/clstr_design_engg_pune_2018_19.html', 'Cluster Design Engineering Pune 2018-19.html'), ('offer_pdf/bosch_diploma_manf_2020_21.html', 'Certificate Programme in Manufacturing Practice for Diploma 2020-21 Bosch'), ('offer_pdf/bosch_iti.html', 'Certificate Programme in Manufacturing Practice for ITI 2020-21 Bosch'), ('offer_pdf/bosch_pg_manf_2020_21.html', 'Post Graduate Certificate in Manufacturing Practice 2020-21 Bosch'), ('offer_pdf/bosch_iti_manf_2018_19.html', 'Certificate Programme in Manufacturing Practice for ITI-2018-19-Bosch'), ('offer_pdf/hcl_offer_letter.html', 'HCL Offer Letter'), ('offer_pdf/aiml_offer_letter.html', 'AIML Offer Letter'), ('offer_pdf/sap_offer_hs70_2019-1_sem.html', 'SAP Offer Letter HS70 2019-1 Sem'), ('offer_pdf/sap_offer_sp93_2019-1_sem.html', 'SAP Offer Letter SP93 2019-1 Sem'), ('offer_pdf/aiml_offer_letter_2019.html', 'AIML-2019'), ('offer_pdf/iot_certificate_cohort_2019.html', 'CIOT-2019'), ('offer_pdf/aiml_offer_letter_20192.html', 'AIML 20192'), ('offer_pdf/cluster_pg_mtech_dse_2019_20.html', 'Cluster Offer Letter - MTech in Data Science 2019-20'), ('offer_pdf/nsp_offer_letter_2020_21.html', 'NSP Offer Letter 2020-21'), ('offer_pdf/hcl_bsc_offer_2020.html', 'HCL BSc Offer letter - 2020'), ('offer_pdf/sap_offer_2020_21sem.html', 'SAP Offer letter 2020-21'), ('offer_pdf/aiml_offer_letter_2020_21-sem1.html', 'AIML 2020-21 Sem1'), ('offer_pdf/aiml_offer_letter_2020_21-sem2.html', 'AIML 2020-21 Sem2'), ('offer_pdf/ciot_offer_letter_2020_21-sem1.html', 'CIOT 2020-21 Sem1'), ('offer_pdf/DSE-Offer-Letter-2020-21.html', 'DSE Offer Letter 2020-21'), ('offer_pdf/DSE-OffLet-2-sem-2020-21.html', 'DSE Offer Letter Second Sem 2020-21'), ('offer_pdf/PGD_cluster_offer_letter_2020.html', 'PGD cluster Offer Letter 2020-21'), ('offer_pdf/PGD_cluster_offer_letter_2020_21_sem2.html', 'PGD cluster Offer Letter 2020-21 Sem2'), ('offer_pdf/FSE_offer_letter_2020.html', 'FSE Offer Letter 2020'), ('offer_pdf/nsp_offer_letter_2021_22.html', 'NSP Offer Letter 2021-22'), ('offer_pdf/offer_letter_comcast_2021.html', 'Offer letter Mahindra Vehicles - 2019-20'), ('offer_pdf/sap_offer_letter_2021_22.html', 'SAP Offer letter 2021-22'), ('offer_pdf/DSE-Offer-Letter-2021-22.html', 'DSE Offer Letter 2021-22'), ('offer_pdf/PGD_cluster_offer_letter_2021_22.html', 'PGD Cluster Offer Letter 2021-22'), ('offer_pdf/iot_offer_letter_2021_22.html', 'IOT Offer Letter 2021-22'), ('offer_pdf/FSE_offer_letter_2021_2022.html', 'FSE Offer Letter 2021-22')], help_text='If an offer letter template is chosen, the applicant will get their offer letter generated using this template. It will override offer letter templates set at program level in the program table', max_length=100, null=True, verbose_name='Choose custom offer letter template, if applicable'),
        ),
        migrations.AlterField(
            model_name='candidateselection',
            name='offer_letter_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/non-specific-sem2-2018-19.html', 'Non-Specific 2018-19'), ('offer_pdf/non-specific-2019-2020.html', 'Non-Specific 2019-20'), ('offer_pdf/mahindra_vehicles2019_20.html', 'Offer letter Mahindra Vehicles - 2019-20'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/spc-pgm-2018-19.html', 'Specific 2018-19'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro-SIM'), ('offer_pdf/wipro_wims.html', 'Wipro-WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro-WASE'), ('offer_pdf/cluster.html', 'Cluster Offer Letter'), ('offer_pdf/cluster1.html', 'Cluster Offer Letter 1'), ('offer_pdf/cluster_pg_2018.html', 'Cluster Program Offer Letter - 2018'), ('offer_pdf/cluster_pg_2018_2019.html', 'Cluster 2018-19'), ('offer_pdf/cluster_pg_mtech_dt_sc_2018_19.html', 'Cluster Offer Letter - MTech Data Science 2018-19'), ('offer_pdf/bosch_man.html', 'Bosch Offer Letter Manufacturing'), ('offer_pdf/bosch_pg_man.html', 'Bosch Offer Letter PG Diploma Manufacturing'), ('offer_pdf/mtech_pom_mum_hyd.html', 'M.Tech POM Offer Letter-Mumbai-Hyd'), ('offer_pdf/mtech_pom_ahmd.html', 'M.Tech POM Offer Letter-Ahmedabad'), ('offer_pdf/embedded_sys_cluster.html', 'Embedded System Cluster Offer Letter 2017-18 Sem1'), ('offer_pdf/iot_certificate.html', 'IOT Certification Offer Letter'), ('offer_pdf/iot_certificate_cohort_2.html', 'IOT Certification Offer Letter Cohort - 2'), ('offer_pdf/iot_certificate_cohort_3.html', 'CIOT Offer Letter 2018 Cohort 1'), ('offer_pdf/iot_certificate_revised.html', 'IOT Offer Letter Revised'), ('offer_pdf/wipro_wase_2017-18_sem2.html', 'Wipro-WASE-2017-18-Sem2'), ('offer_pdf/wipro_wims_2017-18_sem2.html', 'Wipro-WIMS-2017-18-Sem2'), ('offer_pdf/wipro_wims_2018-19_sem2.html', 'Wipro-WIMS-2018-19-Sem2'), ('offer_pdf/wipro_wims_2019-20_sem2.html', 'Wipro-WIMS-2019-20-Sem2'), ('offer_pdf/wipro_wims_2020-21_sem1.html', 'Wipro-WIMS-2020-21'), ('offer_pdf/wipro_wase_2020-21_sem1.html', 'Wipro-WASE-2020-21'), ('offer_pdf/sap_offer_hs70_2018-1_sem.html', 'SAP Offer Letter HS70 2018-1 Sem'), ('offer_pdf/sap_offer_sp93_2018-1_sem.html', 'SAP Offer Letter SP93 2018-1 Sem'), ('offer_pdf/vmware_offer_letter.html', 'VMWare Offer Letter'), ('offer_pdf/mtech_dt_sc_engg_2018_19.html', 'Cluster Offer Letter - MTech in Data Science - with readiness exam 2018-19'), ('offer_pdf/clstr_design_engg_pune_2018_19.html', 'Cluster Design Engineering Pune 2018-19.html'), ('offer_pdf/bosch_diploma_manf_2020_21.html', 'Certificate Programme in Manufacturing Practice for Diploma 2020-21 Bosch'), ('offer_pdf/bosch_iti.html', 'Certificate Programme in Manufacturing Practice for ITI 2020-21 Bosch'), ('offer_pdf/bosch_pg_manf_2020_21.html', 'Post Graduate Certificate in Manufacturing Practice 2020-21 Bosch'), ('offer_pdf/bosch_iti_manf_2018_19.html', 'Certificate Programme in Manufacturing Practice for ITI-2018-19-Bosch'), ('offer_pdf/hcl_offer_letter.html', 'HCL Offer Letter'), ('offer_pdf/aiml_offer_letter.html', 'AIML Offer Letter'), ('offer_pdf/sap_offer_hs70_2019-1_sem.html', 'SAP Offer Letter HS70 2019-1 Sem'), ('offer_pdf/sap_offer_sp93_2019-1_sem.html', 'SAP Offer Letter SP93 2019-1 Sem'), ('offer_pdf/aiml_offer_letter_2019.html', 'AIML-2019'), ('offer_pdf/iot_certificate_cohort_2019.html', 'CIOT-2019'), ('offer_pdf/aiml_offer_letter_20192.html', 'AIML 20192'), ('offer_pdf/cluster_pg_mtech_dse_2019_20.html', 'Cluster Offer Letter - MTech in Data Science 2019-20'), ('offer_pdf/nsp_offer_letter_2020_21.html', 'NSP Offer Letter 2020-21'), ('offer_pdf/hcl_bsc_offer_2020.html', 'HCL BSc Offer letter - 2020'), ('offer_pdf/sap_offer_2020_21sem.html', 'SAP Offer letter 2020-21'), ('offer_pdf/aiml_offer_letter_2020_21-sem1.html', 'AIML 2020-21 Sem1'), ('offer_pdf/aiml_offer_letter_2020_21-sem2.html', 'AIML 2020-21 Sem2'), ('offer_pdf/ciot_offer_letter_2020_21-sem1.html', 'CIOT 2020-21 Sem1'), ('offer_pdf/DSE-Offer-Letter-2020-21.html', 'DSE Offer Letter 2020-21'), ('offer_pdf/DSE-OffLet-2-sem-2020-21.html', 'DSE Offer Letter Second Sem 2020-21'), ('offer_pdf/PGD_cluster_offer_letter_2020.html', 'PGD cluster Offer Letter 2020-21'), ('offer_pdf/PGD_cluster_offer_letter_2020_21_sem2.html', 'PGD cluster Offer Letter 2020-21 Sem2'), ('offer_pdf/FSE_offer_letter_2020.html', 'FSE Offer Letter 2020'), ('offer_pdf/nsp_offer_letter_2021_22.html', 'NSP Offer Letter 2021-22'), ('offer_pdf/offer_letter_comcast_2021.html', 'Offer letter Mahindra Vehicles - 2019-20'), ('offer_pdf/sap_offer_letter_2021_22.html', 'SAP Offer letter 2021-22'), ('offer_pdf/DSE-Offer-Letter-2021-22.html', 'DSE Offer Letter 2021-22'), ('offer_pdf/PGD_cluster_offer_letter_2021_22.html', 'PGD Cluster Offer Letter 2021-22'), ('offer_pdf/iot_offer_letter_2021_22.html', 'IOT Offer Letter 2021-22'), ('offer_pdf/FSE_offer_letter_2021_2022.html', 'FSE Offer Letter 2021-22')], max_length=45, null=True),
        ),
        migrations.AlterField(
            model_name='program',
            name='offer_letter_template',
            field=models.CharField(blank=True, choices=[(None, 'Choose'), ('offer_pdf/oracle.html', 'oracle'), ('offer_pdf/non-specific-sem2.html', 'Non Specific 2016 2nd Sem'), ('offer_pdf/non-specific-sem2-2018-19.html', 'Non-Specific 2018-19'), ('offer_pdf/non-specific-2019-2020.html', 'Non-Specific 2019-20'), ('offer_pdf/mahindra_vehicles2019_20.html', 'Offer letter Mahindra Vehicles - 2019-20'), ('offer_pdf/Specific-program-template.html', 'Specific-program template'), ('offer_pdf/spc-pgm-2018-19.html', 'Specific 2018-19'), ('offer_pdf/wipro.html', 'Wipro Offer letter'), ('offer_pdf/wipro_sim.html', 'Wipro-SIM'), ('offer_pdf/wipro_wims.html', 'Wipro-WIMS'), ('offer_pdf/wipro_wase.html', 'Wipro-WASE'), ('offer_pdf/cluster.html', 'Cluster Offer Letter'), ('offer_pdf/cluster1.html', 'Cluster Offer Letter 1'), ('offer_pdf/cluster_pg_2018.html', 'Cluster Program Offer Letter - 2018'), ('offer_pdf/cluster_pg_2018_2019.html', 'Cluster 2018-19'), ('offer_pdf/cluster_pg_mtech_dt_sc_2018_19.html', 'Cluster Offer Letter - MTech Data Science 2018-19'), ('offer_pdf/bosch_man.html', 'Bosch Offer Letter Manufacturing'), ('offer_pdf/bosch_pg_man.html', 'Bosch Offer Letter PG Diploma Manufacturing'), ('offer_pdf/mtech_pom_mum_hyd.html', 'M.Tech POM Offer Letter-Mumbai-Hyd'), ('offer_pdf/mtech_pom_ahmd.html', 'M.Tech POM Offer Letter-Ahmedabad'), ('offer_pdf/embedded_sys_cluster.html', 'Embedded System Cluster Offer Letter 2017-18 Sem1'), ('offer_pdf/iot_certificate.html', 'IOT Certification Offer Letter'), ('offer_pdf/iot_certificate_cohort_2.html', 'IOT Certification Offer Letter Cohort - 2'), ('offer_pdf/iot_certificate_cohort_3.html', 'CIOT Offer Letter 2018 Cohort 1'), ('offer_pdf/iot_certificate_revised.html', 'IOT Offer Letter Revised'), ('offer_pdf/wipro_wase_2017-18_sem2.html', 'Wipro-WASE-2017-18-Sem2'), ('offer_pdf/wipro_wims_2017-18_sem2.html', 'Wipro-WIMS-2017-18-Sem2'), ('offer_pdf/wipro_wims_2018-19_sem2.html', 'Wipro-WIMS-2018-19-Sem2'), ('offer_pdf/wipro_wims_2019-20_sem2.html', 'Wipro-WIMS-2019-20-Sem2'), ('offer_pdf/wipro_wims_2020-21_sem1.html', 'Wipro-WIMS-2020-21'), ('offer_pdf/wipro_wase_2020-21_sem1.html', 'Wipro-WASE-2020-21'), ('offer_pdf/sap_offer_hs70_2018-1_sem.html', 'SAP Offer Letter HS70 2018-1 Sem'), ('offer_pdf/sap_offer_sp93_2018-1_sem.html', 'SAP Offer Letter SP93 2018-1 Sem'), ('offer_pdf/vmware_offer_letter.html', 'VMWare Offer Letter'), ('offer_pdf/mtech_dt_sc_engg_2018_19.html', 'Cluster Offer Letter - MTech in Data Science - with readiness exam 2018-19'), ('offer_pdf/clstr_design_engg_pune_2018_19.html', 'Cluster Design Engineering Pune 2018-19.html'), ('offer_pdf/bosch_diploma_manf_2020_21.html', 'Certificate Programme in Manufacturing Practice for Diploma 2020-21 Bosch'), ('offer_pdf/bosch_iti.html', 'Certificate Programme in Manufacturing Practice for ITI 2020-21 Bosch'), ('offer_pdf/bosch_pg_manf_2020_21.html', 'Post Graduate Certificate in Manufacturing Practice 2020-21 Bosch'), ('offer_pdf/bosch_iti_manf_2018_19.html', 'Certificate Programme in Manufacturing Practice for ITI-2018-19-Bosch'), ('offer_pdf/hcl_offer_letter.html', 'HCL Offer Letter'), ('offer_pdf/aiml_offer_letter.html', 'AIML Offer Letter'), ('offer_pdf/sap_offer_hs70_2019-1_sem.html', 'SAP Offer Letter HS70 2019-1 Sem'), ('offer_pdf/sap_offer_sp93_2019-1_sem.html', 'SAP Offer Letter SP93 2019-1 Sem'), ('offer_pdf/aiml_offer_letter_2019.html', 'AIML-2019'), ('offer_pdf/iot_certificate_cohort_2019.html', 'CIOT-2019'), ('offer_pdf/aiml_offer_letter_20192.html', 'AIML 20192'), ('offer_pdf/cluster_pg_mtech_dse_2019_20.html', 'Cluster Offer Letter - MTech in Data Science 2019-20'), ('offer_pdf/nsp_offer_letter_2020_21.html', 'NSP Offer Letter 2020-21'), ('offer_pdf/hcl_bsc_offer_2020.html', 'HCL BSc Offer letter - 2020'), ('offer_pdf/sap_offer_2020_21sem.html', 'SAP Offer letter 2020-21'), ('offer_pdf/aiml_offer_letter_2020_21-sem1.html', 'AIML 2020-21 Sem1'), ('offer_pdf/aiml_offer_letter_2020_21-sem2.html', 'AIML 2020-21 Sem2'), ('offer_pdf/ciot_offer_letter_2020_21-sem1.html', 'CIOT 2020-21 Sem1'), ('offer_pdf/DSE-Offer-Letter-2020-21.html', 'DSE Offer Letter 2020-21'), ('offer_pdf/DSE-OffLet-2-sem-2020-21.html', 'DSE Offer Letter Second Sem 2020-21'), ('offer_pdf/PGD_cluster_offer_letter_2020.html', 'PGD cluster Offer Letter 2020-21'), ('offer_pdf/PGD_cluster_offer_letter_2020_21_sem2.html', 'PGD cluster Offer Letter 2020-21 Sem2'), ('offer_pdf/FSE_offer_letter_2020.html', 'FSE Offer Letter 2020'), ('offer_pdf/nsp_offer_letter_2021_22.html', 'NSP Offer Letter 2021-22'), ('offer_pdf/offer_letter_comcast_2021.html', 'Offer letter Mahindra Vehicles - 2019-20'), ('offer_pdf/sap_offer_letter_2021_22.html', 'SAP Offer letter 2021-22'), ('offer_pdf/DSE-Offer-Letter-2021-22.html', 'DSE Offer Letter 2021-22'), ('offer_pdf/PGD_cluster_offer_letter_2021_22.html', 'PGD Cluster Offer Letter 2021-22'), ('offer_pdf/iot_offer_letter_2021_22.html', 'IOT Offer Letter 2021-22'), ('offer_pdf/FSE_offer_letter_2021_2022.html', 'FSE Offer Letter 2021-22')], max_length=60, null=True),
        ),
    ]
