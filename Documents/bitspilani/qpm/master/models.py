from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime
import os


class RemoteUserRole(models.Model):
    user_role = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True, null=True,)
    user_remote_code = models.CharField(max_length=80, unique=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    def __str__(self):
        return self.user_role


class RemoteUser(models.Model):
    login_user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.ForeignKey(RemoteUserRole, on_delete=models.PROTECT)

    def __str__(self):
        return self.user_type.user_role


class StaffUserAccessList(models.Model):
    user_id = models.EmailField(max_length=60)
    created_datetime = models.DateTimeField(auto_now_add=True, blank=True)
    created_by_user_id = models.EmailField(max_length=60)
    coordinator_flag = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user_id

    class Meta:
        unique_together = ('user_id',)
        verbose_name_plural = "Staff user access list"


class Batch(models.Model):
    SEMNUMBER_CHOICES = (
        (None,'Choose Semester Number'),
        ('1', '1'),
        ('2', '2'),
    )

    batch_name = models.CharField(max_length=45, unique=True)  # Field name made lowercase.
    year = models.PositiveIntegerField(null=True)
    sem_number = models.CharField(max_length=2,choices=SEMNUMBER_CHOICES,null=True)

    def __str__(self):
        return self.batch_name

    def save(self, *args, **kwargs):
        self.batch_name = self.batch_name.upper()
        return super(Batch, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Batch"

class ExamSlot(models.Model):
    slot_name = models.CharField(max_length=45, unique=True)  # Field name made lowercase.
    slot_date = models.DateField()  # Field name made lowercase.
    slot_day = models.CharField(max_length=10)  # Field name made lowercase.
    slot_start_time = models.TimeField(verbose_name="Slot Exam Start Time", default=datetime.time(00, 00))

    def __str__(self):
        return f"{self.slot_day} {self.slot_date} {self.slot_name}"

    def save(self, *args, **kwargs):
        self.slot_name = self.slot_name.upper()
        return super(ExamSlot, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('slot_name', 'slot_day', 'slot_date',)
        verbose_name_plural = "Exam Slot"

    def clean(self):
        if self.slot_start_time == datetime.time(0, 0):
            raise ValidationError("The Field Slot Exam Start Time is Mandatory")


class ExamType(models.Model):

    EVALUATION_TYPE_CHOICES = (
        (None,'Choose Evaluation Type'),
        ('EC2', 'EC2'),
        ('EC3', 'EC3'),
        ('CERTIFICATION','CERTIFICATION'),
    )
    exam_type = models.CharField(max_length=45)  # Field name made lowercase.
    evaluation_type = models.CharField(max_length=14,choices=EVALUATION_TYPE_CHOICES,null=True)

    def __str__(self):
        return f"{self.evaluation_type} {self.exam_type}"

    def save(self, *args, **kwargs):
        self.exam_type = self.exam_type.upper()
        return super(ExamType, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('exam_type', 'evaluation_type',)
        verbose_name_plural = "Exam Type"


class SetQpSubmissionsLock(models.Model):
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)  # Field name made lowercase.
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)  # Field name made lowercase.
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)  # Field name made lowercase.
    lock_flag = models.BooleanField(default=False)  # Field name made lowercase.
    lock_all_submissions_flag = models.BooleanField('Lock all Submissions(This is disable any QP upload in the system)',default=False)  # Field name made lowercase.

    def __str__(self):
        return f'{self.semester}{self.batch}'

    class Meta:
        verbose_name_plural = "Set QP Submission Locks"

def get_file_name(instance,filename):
    file_name = ""
    if instance.semester.semester_name =='-':
        pass
    else:
        if '/' in instance.semester.semester_name:
            filename = filename + ' '.join(instance.semester.semester_name.split('/'))
        else:
            file_name = file_name+instance.semester.semester_name

    if instance.batch.batch_name =='-':
        pass
    else:
        if '/' in instance.batch.batch_name:
            batch_name = ' '.join(instance.batch.batch_name.split('/'))
        else:
            batch_name = instance.batch.batch_name

        if instance.semester.semester_name =='-':
            file_name = file_name+batch_name
        else:
            file_name = file_name+'_'+batch_name

    if '/' in instance.course_code:
        course_code = ' '.join(instance.course_code.split('/'))
    else:
        course_code = instance.course_code

    if '/' in instance.course_name:
        course_name = ' '.join(instance.course_name.split('/'))
    else:
        course_name = instance.course_name

    if '/' in instance.exam_type.exam_type:
        exam_type = ' '.join(instance.exam_type.exam_type.split('/'))
    else:
        exam_type = instance.exam_type.exam_type

    if '/' in instance.exam_slot.slot_name:
        exam_slot = ' '.join(instance.exam_slot.slot_name.split('/'))
    else:
        exam_slot = instance.exam_slot.slot_name

    file_name = file_name+'_'+course_code+'_'+course_name+'_'+exam_type+'_'+exam_slot
    return file_name

def uploaded_document_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    file_name=''
    file_name+=get_file_name(instance,filename)+ext
    file_name = 'documents/{0}'.format(file_name)
    return file_name

def alternate_qp_document_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    file_name=''
    file_name+=get_file_name(instance,filename)+'_INSTR'+ext
    file_name = 'documents/{0}'.format(file_name)
    return file_name

PROGRAM_CHOICES = (
        (None,'Choose Program Type'),
        ('SPECIFIC', 'SPECIFIC'),
        ('NON-SPECIFIC', 'NON-SPECIFIC'),
        ('CLUSTER', 'CLUSTER'),
        ('CERTIFICATION', 'CERTIFICATION'),
    )

def get_batch_name():
    try:
        batch = Batch.objects.get(batch_name="-")
    except:
        batch = Batch.objects.create(batch_name="-")
    return batch

class QpSubmission(models.Model):
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)  # Field name made lowercase.
    course_code = models.CharField(max_length=20)  # Field name made lowercase.
    course_name = models.CharField(max_length=50)  # Field name made lowercase.
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)  # Field name made lowercase.
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, blank=True, default=get_batch_name)  # Field name made lowercase.
    program_type = models.CharField(max_length=15,choices=PROGRAM_CHOICES,)  # Field name made lowercase.
    exam_slot = models.ForeignKey(ExamSlot, on_delete=models.CASCADE)  # Field name made lowercase.
    faculty_email_id = models.EmailField(max_length=60) # Field name made lowercase.
    email_access_id_1 = models.EmailField(max_length=60,blank=True, null=True)
    email_access_id_2 = models.EmailField(max_length=60,blank=True, null=True)
    coordinator_email_id_1 = models.EmailField(max_length=60,blank=True, null=True)
    coordinator_email_id_2 = models.EmailField(max_length=60,blank=True, null=True)
    submitted_by_faculty = models.EmailField(max_length=60,blank=True, null=True)
    qp_path = models.FileField(max_length=500,verbose_name='Document Path', upload_to=uploaded_document_path, blank=True, null=True)
    alternate_qp_path = models.FileField(max_length=500,verbose_name='Alternate Document Path', upload_to=alternate_qp_document_path, blank=True, null=True)
    alternate_qp_submit_datetime = models.DateTimeField( blank=True, null=True)
    first_submitted_datetime = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    last_submitted_datetime = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    submission_locked_flag = models.BooleanField(default=False)  # Field name made lowercase.
    last_download_datetime = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    downloaded_by = models.CharField( max_length=50, blank=True, null=True)  # Field name made lowercase.
    active_flag = models.BooleanField(default=True, verbose_name='Exam Active Flag / QP Upload Active Flag',help_text="""To enable faculty to resubmit a question paper after acceptance or download 
                                                        by Instruction cell team, please uncheck BOTH the lock and accept flags and 
                                                        save the record""")  # Field name made lowercase.
    qp_guidelines_flag = models.BooleanField(blank=True, null=True)  # Field name made lowercase.
    qp_correct_flag = models.BooleanField( blank=True, null=True)  # Field name made lowercase.
    last_reminder_email_datetime = models.DateTimeField( blank=True, null=True)  # Field name made lowercase.
    acceptance_flag = models.BooleanField(default=False) # Field name made lowercase.
    accepted_datetime = models.DateTimeField( blank=True, null=True)  # Field name made lowercase.
    rejected_flag = models.BooleanField(default=False)  # Field name made lowercase.
    rejected_datetime = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    rejection_comments = models.CharField(max_length=300, blank=True, null=True)  # Field name made lowercase.

    def save(self, *args, **kwargs):
        self.course_code = self.course_code.upper()
        self.course_name = self.course_name.upper()
        return super(QpSubmission, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('semester', 'course_code', 'exam_type', 'batch')
        verbose_name_plural = "QP Submissions"


class Semester(models.Model):
    semester_name = models.CharField(max_length=45, unique=True)  # Field name made lowercase.

    def __str__(self):
        return self.semester_name

    def save(self, *args, **kwargs):
        self.semester_name = self.semester_name.upper()
        return super(Semester, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Semester"
