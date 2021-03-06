# Generated by Django 2.2.4 on 2019-08-19 09:55

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import master.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('master', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_name', models.CharField(max_length=30, unique=True)),
                ('year', models.PositiveIntegerField()),
                ('sem_number', models.CharField(choices=[(None, 'Choose Semester Number'), ('1', '1'), ('2', '2')], max_length=2)),
                ('application_center_batch', models.CharField(blank=True, max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DataSyncLogs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=50)),
                ('synced_on', models.DateTimeField(auto_now_add=True)),
                ('records_pulled', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(blank=True, choices=[('SUCCESS', 'SUCCESS'), ('FAILED', 'FAILED')], max_length=45, null=True)),
                ('parameters', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExamSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot_name', models.CharField(max_length=20)),
                ('slot_day', models.CharField(max_length=15)),
                ('slot_date', models.DateField()),
            ],
            options={
                'unique_together': {('slot_name', 'slot_day', 'slot_date')},
            },
        ),
        migrations.CreateModel(
            name='ExamType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam_type', models.CharField(choices=[(None, 'Choose Exam Type'), ('EC2 Regular', 'EC2 Regular'), ('EC2 Makeup', 'EC2 Makeup'), ('EC3 Regular', 'EC3 Regular'), ('EC3 Makeup', 'EC3 Makeup')], max_length=12)),
                ('evaluation_type', models.CharField(choices=[(None, 'Choose Evaluation Type'), ('EC2', 'EC2'), ('EC3', 'EC3')], max_length=4)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program_code', models.CharField(max_length=6, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_program_code', message='program code must be Alphanumeric', regex='^[a-zA-Z0-9]{4}$')])),
                ('program_name', models.CharField(max_length=60)),
                ('program_type', models.CharField(choices=[(None, 'Choose Program Type'), ('specific', 'SPECIFIC'), ('non-specific', 'NON-SPECIFIC'), ('cluster', 'CLUSTER'), ('certification', 'CERTIFICATION'), ('others', 'OTHERS')], max_length=30)),
                ('organization', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester_name', models.CharField(max_length=45, unique=True)),
                ('taxila_sem_name', models.CharField(blank=True, max_length=45, null=True, unique=True)),
                ('canvas_sem_name', models.CharField(blank=True, max_length=45, null=True, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=12, unique=True)),
                ('student_name', models.CharField(max_length=45)),
                ('photo_path', models.FileField(blank=True, max_length=1000, null=True, upload_to=master.models.extract_photo_path, verbose_name='Photo Path')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_batch', to='master.Batch')),
            ],
        ),
        migrations.CreateModel(
            name='ExamVenue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('venue_short_name', models.CharField(max_length=20, unique=True)),
                ('venue_address', models.TextField()),
                ('pin_code', models.PositiveIntegerField()),
                ('is_active', models.BooleanField(default=False)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examvenue_loc', to='master.Location')),
            ],
        ),
        migrations.CreateModel(
            name='CourseExamShedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_code', models.CharField(max_length=15)),
                ('course_name', models.CharField(max_length=50)),
                ('comp_code', models.PositiveIntegerField(blank=True, null=True)),
                ('unit', models.PositiveIntegerField(blank=True, null=True)),
                ('inserted_on', models.DateTimeField(auto_now_add=True)),
                ('last_update_on', models.DateTimeField(auto_now=True)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courseexamshedule_batch', to='master.Batch')),
                ('exam_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courseexamshedule_es', to='master.ExamSlot')),
                ('exam_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courseexamshedule_et', to='master.ExamType')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courseexamshedule_sem', to='master.Semester')),
            ],
            options={
                'unique_together': {('course_code', 'exam_type')},
            },
        ),
        migrations.CreateModel(
            name='StudentRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='studentregistration_ces', to='master.CourseExamShedule')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='studentregistration_sem', to='master.Semester')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='studentregistration_stud', to='master.Student')),
            ],
            options={
                'unique_together': {('course', 'student', 'semester')},
            },
        ),
        migrations.CreateModel(
            name='LocationCoordinator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coordinator_email_id', models.EmailField(max_length=50)),
                ('name', models.CharField(blank=True, max_length=45, null=True)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locationcoordinator_loc', to='master.Location')),
            ],
            options={
                'unique_together': {('coordinator_email_id', 'location')},
            },
        ),
        migrations.CreateModel(
            name='HallTicket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_cancel', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('cancel_on', models.DateTimeField(blank=True, null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hallticket_ces', to='master.CourseExamShedule')),
                ('exam_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hallticket_es', to='master.ExamSlot')),
                ('exam_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hallticket_et', to='master.ExamType')),
                ('exam_venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hallticket_ev', to='master.ExamVenue')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hallticket_sem', to='master.Semester')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hallticket_stud', to='master.Student')),
            ],
            options={
                'unique_together': {('student', 'semester', 'course', 'exam_type', 'exam_slot', 'exam_venue')},
            },
        ),
        migrations.CreateModel(
            name='ExamVenueSlotMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examvenueslotmap_es', to='master.ExamSlot')),
                ('exam_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examvenueslotmap_et', to='master.ExamType')),
                ('exam_venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examvenueslotmap_ev', to='master.ExamVenue')),
            ],
            options={
                'unique_together': {('exam_venue', 'exam_slot', 'exam_type')},
            },
        ),
        migrations.CreateModel(
            name='ExamAttendance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attendance_count', models.PositiveIntegerField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('last_update_on', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examattendance_ces', to='master.CourseExamShedule')),
                ('exam_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examattendance_es', to='master.ExamSlot')),
                ('exam_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examattendance_et', to='master.ExamType')),
                ('exam_venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examattendance_ev', to='master.ExamVenue')),
                ('last_update_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='examattendance_user', to=settings.AUTH_USER_MODEL)),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examattendance_sem', to='master.Semester')),
            ],
            options={
                'unique_together': {('exam_venue', 'course', 'semester', 'exam_type', 'exam_slot')},
            },
        ),
        migrations.CreateModel(
            name='CurrentExam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False)),
                ('hall_tkt_change_flag', models.BooleanField(default=False)),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='currentexam_batch', to='master.Batch')),
                ('exam_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currentexam_et', to='master.ExamType')),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='currentexam_loc', to='master.Location')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currentexam_pg', to='master.Program')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currentexam_sem', to='master.Semester')),
            ],
            options={
                'unique_together': {('program', 'semester', 'batch')},
            },
        ),
    ]
