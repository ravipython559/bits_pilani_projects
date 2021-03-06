# Generated by Django 2.2.7 on 2020-02-10 09:50

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0022_courseexamshedule_exam_venue_slot_maps'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='batch',
            options={'verbose_name_plural': 'Batches'},
        ),
        migrations.AlterModelManagers(
            name='hallticket',
            managers=[
                ('filter_hallticket', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterField(
            model_name='examtype',
            name='evaluation_type',
            field=models.CharField(choices=[(None, 'Choose Evaluation Type'), ('EC2', 'EC2'), ('EC3', 'EC3'), ('CERTIFICATION', 'CERTIFICATION')], max_length=14),
        ),
        migrations.AlterField(
            model_name='examtype',
            name='exam_type',
            field=models.CharField(max_length=20),
        ),
    ]
