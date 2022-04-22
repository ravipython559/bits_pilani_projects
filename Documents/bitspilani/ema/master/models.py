from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import uuid
from itertools import chain 
from django.core.validators import RegexValidator
from django.db.models import Case, Value, Q, When
from ema import default_settings as S
from easy_thumbnails.fields import ThumbnailerImageField
import os
import datetime
from django.core.exceptions import ValidationError


def extract_photo_path(instance, filename):
	date = timezone.now()
	return 'documents/photo/{0}/{1}/{2}/{3}/{4}/'.format(
		date.year,
		date.strftime('%B'),
		date.day,
		uuid.uuid4().hex,
		filename
	)

# Create your models here.
@python_2_unicode_compatible
class RemoteUserRole(models.Model):
	user_role = models.CharField(max_length=80, unique=True)
	description = models.TextField(blank=True, null=True,)
	user_remote_code = models.CharField(max_length=80, unique=True)
	is_superuser = models.BooleanField(default=False)
	is_staff = models.BooleanField(default=False)

	def __str__(self):
		return self.user_role

@python_2_unicode_compatible
class RemoteUser(models.Model):
	login_user = models.OneToOneField(User, on_delete=models.CASCADE)
	user_type = models.ForeignKey(RemoteUserRole, on_delete=models.PROTECT)

	def __str__(self):
		return self.user_type.user_role

@python_2_unicode_compatible
class Batch(models.Model):

	SEMESTER_1 = '1'
	SEMESTER_2 = '2'

	SEMNUMBER_CHOICES = (
		(None,'Choose Semester Number'),
		(SEMESTER_1, '1'),
		(SEMESTER_2, '2'),
	)
	batch_name = models.CharField(max_length=30, unique=True)
	year = models.PositiveIntegerField()
	sem_number = models.CharField(max_length=2,choices=SEMNUMBER_CHOICES,)
	application_center_batch = models.CharField(max_length=7, blank=True, null=True,)

	class BatchManager(models.Manager):
		def get_queryset(self):
			return super().get_queryset().annotate(
				order=Case(
					When(Q(batch_name=S.BATCH_NAME), then=Value('1')),
					default=Value('2'),
					output_field=models.IntegerField()
					)
				).order_by('order')

	objects = BatchManager()

	def save(self, *args, **kwargs):
		self.batch_name = self.batch_name.upper()
		return super(Batch, self).save(*args, **kwargs)

	def __str__(self):
		return self.batch_name

	class Meta:
		verbose_name_plural = "Batches"

@python_2_unicode_compatible
class Semester(models.Model):

	semester_name = models.CharField(max_length=45, unique=True)
	taxila_sem_name = models.CharField(max_length=45, unique=True, blank=True, null=True,)
	canvas_sem_name = models.CharField(max_length=45, unique=True, blank=True, null=True,)

	class SemesterManager(models.Manager):
		def get_queryset(self):
			return super().get_queryset().annotate(
			order=Case(
				When(Q(semester_name=S.SEMESTER_NAME), then=Value('1')),
				default=Value('2'),
				output_field=models.IntegerField()
				)
			).order_by('order')
	objects = SemesterManager()

	def save(self, *args, **kwargs):
		self.semester_name = self.semester_name.upper()
		return super(Semester, self).save(*args, **kwargs)

	def __str__(self):
		return self.semester_name

@python_2_unicode_compatible
class Location(models.Model):
	location_name = models.CharField(max_length=50, unique=True,)

	def __str__(self):
		return self.location_name

@python_2_unicode_compatible
class Program(models.Model):
	SPECIFIC = 'specific'
	NON_SPECIFIC = 'non-specific'
	CLUSTER = 'cluster'
	CERTIFICATION = 'certification'
	OTHERS = 'others'

	PROGRAM_TYPE_CHOICES = (
		(None,'Choose Program Type'),
		(SPECIFIC, 'SPECIFIC'),
		(NON_SPECIFIC, 'NON-SPECIFIC'),
		(CLUSTER,'CLUSTER'),
		(CERTIFICATION,'CERTIFICATION'),
		(OTHERS,'OTHERS'),
	)
	program_code = models.CharField(max_length=6, unique=True,
		validators=[ RegexValidator(regex='^[a-zA-Z0-9]{4}$',
			message=_('program code must be Alphanumeric'), 
			code=_('invalid_program_code')),
		]
	)
	program_name = models.CharField(max_length=60)
	program_type = models.CharField(max_length=30, choices=PROGRAM_TYPE_CHOICES,)
	organization = models.CharField(max_length=50, blank=True, null=True,)

	def __str__(self):
		return "{0} - {1} ({2})".format(self.program_code, 
			self.program_name, 
			self.program_type.upper()
		)


##vishal: need a over look 
@python_2_unicode_compatible
class ExamSlot(models.Model):

	slot_name = models.CharField(max_length=20, unique=True)
	slot_date = models.DateField()
	slot_day = models.CharField(max_length=15)
	slot_start_time = models.TimeField(verbose_name="Slot Exam Start Time", default=datetime.time(00, 00))

	class ExamSlotManager(models.Manager):
		def get_queryset(self):
			return super().get_queryset().annotate(
				order=Case(
					When(Q(slot_name=Value('-')), then=Value('1')),
					default=Value('2'),
					output_field=models.IntegerField()
					)
				).order_by('order')

	objects = ExamSlotManager()

	def save(self, *args, **kwargs):
		self.slot_name = self.slot_name.upper()
		return super(ExamSlot, self).save(*args, **kwargs)

	def __str__(self):
		return f"{self.slot_day} {self.slot_date} {self.slot_name}"

	class Meta:
		unique_together = ('slot_name', 'slot_day', 'slot_date',)

	def clean(self):
		if self.slot_start_time == datetime.time(0, 0):
			raise ValidationError("The Field Slot Exam Start Time is Mandatory")


@python_2_unicode_compatible
class ExamVenue(models.Model):
	location = models.ForeignKey(Location, related_name='%(class)s_loc', 
		on_delete=models.CASCADE,)
	venue_short_name = models.CharField(max_length=20, unique=True,)
	venue_address = models.TextField(max_length=150)
	pin_code = models.CharField(max_length=6, null=True,
    validators=[RegexValidator(
        regex=r'^\d{6}$',
        message=_(u'should be a 6 digit integer'),
    )],
	)
	is_active = models.BooleanField(default=False)
	student_count_limit = models.PositiveIntegerField(null=False, verbose_name="Seating Limit")

	def __str__(self):
		return self.venue_short_name


@python_2_unicode_compatible
class ExamType(models.Model):

	EXAM_TYPE_CHOICES = (
		(None,'Choose Exam Type'),
		('EC2 Regular', 'EC2 Regular'),
		('EC2 Makeup', 'EC2 Makeup'),
		('EC3 Regular', 'EC3 Regular'),
		('EC3 Makeup', 'EC3 Makeup'),
	)

	EVALUATION_TYPE_CHOICES = (
		(None,'Choose Evaluation Type'),
		('EC2', 'EC2'),
		('EC3', 'EC3'),
		('CERTIFICATION','CERTIFICATION'),
	)	
			
	exam_type = models.CharField(max_length=20,)
	evaluation_type = models.CharField(max_length=14,choices=EVALUATION_TYPE_CHOICES,)

	class ExamTypeManager(models.Manager):
		def get_queryset(self):
			return super().get_queryset().annotate(
			order=Case(
				When(
					Q(exam_type=Value('-')), 
					then=Value('1')
					),
				default=Value('2'),
				output_field=models.IntegerField()
				)
			).order_by('order')
	objects = ExamTypeManager()

	def save(self, *args, **kwargs):
		self.exam_type = self.exam_type.upper()
		return super(ExamType, self).save(*args, **kwargs)

	class Meta:
		unique_together = ('exam_type', 'evaluation_type',)

	def __str__(self):
		return f"{self.evaluation_type} {self.exam_type}"

@python_2_unicode_compatible
class LocationCoordinator(models.Model):
	coordinator_email_id = models.EmailField(max_length=50)
	location = models.ForeignKey(Location, related_name='%(class)s_loc', on_delete=models.CASCADE,)
	name = models.CharField(max_length=45, blank=True, null=True,)
	
	def __str__(self):
		return self.coordinator_email_id

	class Meta:
		unique_together = ('coordinator_email_id', 'location',)

@python_2_unicode_compatible
class CourseExamShedule(models.Model):
	course_code = models.CharField(max_length = 15,
		validators=[ RegexValidator(regex='^[a-zA-Z0-9]+$',
			message=_('Course code should not have spaces. Course code must be Alphanumeric'),
			code=_('invalid_course_code'),),
		])
	course_name = models.CharField(max_length = 50,) 
	semester = models.ForeignKey(Semester, 
		related_name='%(class)s_sem',on_delete=models.CASCADE,
		help_text="Only Semesters With Active Exam Entries Are Allowed")
	batch = models.ForeignKey(Batch, related_name='%(class)s_batch', on_delete=models.CASCADE)
	exam_slot = models.ForeignKey(ExamSlot,
		related_name='%(class)s_es', on_delete=models.CASCADE,)
	exam_type = models.ForeignKey(ExamType,
		related_name='%(class)s_et', on_delete=models.CASCADE, 
		help_text="Only Active Exam Types Are Allowed To Be Chosen")
	comp_code = models.PositiveIntegerField(blank=True, null=True)
	unit = models.PositiveIntegerField(null=False)
	inserted_on = models.DateTimeField(auto_now_add=True)
	last_update_on = models.DateTimeField(auto_now=True)
	exam_venue_slot_maps = models.ManyToManyField('ExamVenueSlotMap', 
		through='ExamVenueSlotMap_course_exam_schedule', blank=True)

	def save(self, *args, **kwargs):
		self.course_code = self.course_code.upper()
		self.course_name = self.course_name.upper()
		return super(CourseExamShedule, self).save(*args, **kwargs)

	def __str__(self):
		return f'{self.course_code} : {self.course_name}'

	class Meta:
		unique_together = ('course_code', 'exam_type','semester', 'batch')
		verbose_name = "Course Exam Schedule"


@python_2_unicode_compatible
class CurrentExam(models.Model):
	TEMPLATE_CHOICES = (
		('hall_ticket.html', 'Std Hall Tkt Template'),
	)

	exam_type = models.ForeignKey(ExamType,
		related_name='%(class)s_et', on_delete=models.CASCADE,)
	program = models.ForeignKey(Program, related_name='%(class)s_pg', 
		on_delete=models.CASCADE)
	semester = models.ForeignKey(Semester, related_name='%(class)s_sem', on_delete=models.CASCADE)
	batch = models.ForeignKey(Batch, related_name='%(class)s_batch', on_delete=models.CASCADE)
	is_active = models.BooleanField(default=False, verbose_name="Exam Active Flag", 
		help_text="If the flag is unchecked, student will not be allowed to view and download hall tickets",)
	hall_tkt_change_flag = models.BooleanField(default=False, verbose_name="Hall Ticket Changes Allowed?", 
		help_text="If this is unchecked, modifications in hall ticket will not be allowed for students",)
	missing_tkt_exception_flag = models.BooleanField(default=False, verbose_name="Allow Hall Ticket Generation for Students without Hall Tickets during Freeze Window",
		help_text="Checking this checkbox will enable student who haven’t generated their hall ticket yet to generate the same even after the hall ticket change window is closed")
	location = models.ForeignKey(Location, related_name='%(class)s_loc', on_delete=models.CASCADE, blank=True, null=True)
	exm_slot_fn = models.CharField(max_length = 75,blank=True,default="",verbose_name="Exam Slot Time Text (Forenoon)")
	exm_slot_an = models.CharField(max_length = 75,blank=True,default="",verbose_name="Exam Slot Time Text (Afternoon)")
	hall_tkt_template = models.CharField(max_length=45, choices=TEMPLATE_CHOICES, verbose_name="Choose Hall Ticket template", blank=True, null=True)




	def __str__(self):
		return f'{self.exam_type.exam_type} : {self.program.program_code}'

	class Meta:
		unique_together = ('exam_type','program', 'semester', 'batch')

@python_2_unicode_compatible
class DataSyncLogs(models.Model):

	SUCCESS = 'SUCCESS'
	FAILED = 'FAILED'

	SUCCESS_CHOICES = (
		(SUCCESS, 'SUCCESS'),
		(FAILED, 'FAILED'),
	)

	source = models.CharField(max_length = 50,)
	synced_on = models.DateTimeField(auto_now_add=True)
	records_pulled = models.IntegerField(blank=True, null=True)
	status = models.CharField(max_length=45, choices=SUCCESS_CHOICES ,blank=True, null=True)
	parameters = models.TextField(blank=True, null=True)

	def __str__(self):
		return str(self.synced_on)

@python_2_unicode_compatible
class ExamAttendance(models.Model):
	exam_venue = models.ForeignKey(ExamVenue,
		related_name='%(class)s_ev', on_delete=models.CASCADE,)
	course = models.ForeignKey(CourseExamShedule,
		related_name='%(class)s_ces', on_delete=models.CASCADE,)
	semester = models.ForeignKey(Semester, 
		related_name='%(class)s_sem', on_delete=models.CASCADE,)	
	exam_type = models.ForeignKey(ExamType,
		related_name='%(class)s_et', on_delete=models.CASCADE,)
	exam_slot = models.ForeignKey(ExamSlot,
		related_name='%(class)s_es', on_delete=models.CASCADE,)
	attendance_count = models.PositiveIntegerField(default=0,)
	created_on = models.DateTimeField(auto_now_add=True)
	last_update_on = models.DateTimeField(auto_now=True)
	last_update_by = models.ForeignKey(User, related_name='%(class)s_user', 
		on_delete=models.PROTECT)

	def __str__(self):
		return str(self.exam_venue)

	class Meta:
		unique_together = ('exam_venue', 'course', 'semester', 'exam_type' ,'exam_slot')


@python_2_unicode_compatible
class ExamVenueSlotMap(models.Model):
	exam_venue = models.ForeignKey(ExamVenue,
		related_name='%(class)s_ev', on_delete=models.CASCADE,
		help_text="Choose Location First. Only Active Venues will be listed",
		verbose_name = 'Venue Short Name',)
	exam_slot = models.ForeignKey(ExamSlot,
		related_name='%(class)s_es', on_delete=models.CASCADE)
	exam_type = models.ForeignKey(ExamType,
		related_name='%(class)s_et', on_delete=models.CASCADE)
	student_count_limit = models.PositiveIntegerField(null=False, verbose_name="Student Count Limit",)
	course_exam_schedule = models.ManyToManyField(CourseExamShedule, blank=True)

	class ExamVenueSlotMapManager(models.Manager):
		def get_queryset(self):
			return super().get_queryset().annotate(
				order=Case(
					When(
						Q(exam_slot__slot_name=Value('-')), 
						then=Value('1')
					),
					default=Value('2'),
					output_field=models.IntegerField()
				),
			).order_by('order').distinct()

	def __str__(self):
		return f'{self.exam_venue}, {self.exam_slot}, {self.exam_type}'

	objects = ExamVenueSlotMapManager()

	class Meta:
		unique_together = ('exam_venue', 'exam_slot', 'exam_type',)

@python_2_unicode_compatible
class Student(models.Model):
	student_id = models.CharField(max_length=12, unique=True)
	student_name = models.CharField(max_length=45)
	photo = ThumbnailerImageField(verbose_name='Photo Path', upload_to=extract_photo_path, blank=True, null=True, max_length=1000)
	batch = models.ForeignKey(Batch, related_name='%(class)s_batch', on_delete=models.CASCADE ,blank=True, null=True)
	personal_email = models.CharField(max_length=60, null=True, blank=True)
	personal_phone = models.CharField(max_length=30, null=True, blank=True)
	created_on = models.DateTimeField(auto_now_add=True)

	
	def __str__(self):
		return self.student_id


@python_2_unicode_compatible
class StudentRegistration(models.Model):
	course_code = models.CharField(max_length = 15,
		validators=[ RegexValidator(regex='^[a-zA-Z0-9]+$',
			message=_('Course code should not have spaces. Course code must be Alphanumeric'),
			code=_('invalid_course_code'),),
		],
	)
	student = models.ForeignKey(Student, 
		related_name='%(class)s_stud', on_delete=models.CASCADE,)
	semester = models.ForeignKey(Semester, 
		related_name='%(class)s_sem', on_delete=models.CASCADE,)
	created_on = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		self.course_code = self.course_code.upper()
		return super(StudentRegistration, self).save(*args, **kwargs)
	
	def __str__(self):
		return self.student.student_id

	class Meta:
		unique_together = ('course_code', 'student', 'semester',)


@python_2_unicode_compatible
class HallTicket(models.Model):
	student = models.ForeignKey(Student, 
		related_name='%(class)s_stud', on_delete=models.CASCADE,)
	semester = models.ForeignKey(Semester, 
		related_name='%(class)s_sem', on_delete=models.CASCADE,)
	course = models.ForeignKey(CourseExamShedule,
		related_name='%(class)s_ces', on_delete=models.CASCADE,)
	exam_type = models.ForeignKey(ExamType,
		related_name='%(class)s_et', on_delete=models.CASCADE,)
	exam_slot = models.ForeignKey(ExamSlot,
		related_name='%(class)s_es', on_delete=models.CASCADE,)
	exam_venue = models.ForeignKey(ExamVenue,
		related_name='%(class)s_ev', on_delete=models.CASCADE,)
	is_cancel = models.BooleanField(default=False)
	created_on = models.DateTimeField(auto_now_add=True)
	cancel_on = models.DateTimeField(blank=True, null=True)

	class HallTicketManager(models.Manager):
		def get_queryset(self):
			return super().get_queryset().exclude(exam_venue__venue_short_name=S.VENUE_SHORT_NAME)

	def __str__(self):
		return f'{self.exam_venue}, {self.exam_slot}, {self.exam_type}'

	filter_hallticket = HallTicketManager()
	objects = models.Manager()

	def __str__(self):
		return str(self.student)

class OnlineExamAttendance(models.Model):
	student_id = models.CharField(max_length=12)
	exam_type = models.ForeignKey(ExamType,
		related_name='%(class)s_oea', on_delete=models.CASCADE,)
	course_code = models.CharField(max_length=15)
	semester = models.ForeignKey(Semester, 
		related_name='%(class)s_sem', on_delete=models.CASCADE, null=True, blank=True)
	makeup_allowed = models.BooleanField(default=False)
	course_name = models.CharField(max_length=50,blank=True,null=True)
	exam_date = models.DateTimeField(blank=True,null=True)
	total_questions = models.IntegerField(blank=True,null=True)
	total_attempted = models.IntegerField(blank=True,null=True)
	total_blank = models.IntegerField(blank=True,null=True)
	image_uploaded = models.IntegerField(blank=True,null=True)
	test_start_time = models.CharField(max_length=45,blank=True,null=True)
	test_end_time = models.CharField(max_length=45,blank=True,null=True)
	submission_type = models.CharField(max_length=20,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.course_code = self.course_code.upper()
		if self.course_name:
			self.course_name = self.course_name.upper()
		return super(OnlineExamAttendance, self).save(*args, **kwargs)

	def __str__(self):
		return str(self.student_id)

	class Meta:
		unique_together = ('student_id','exam_type', 'course_code','semester',)


class ExamVenueLock(models.Model):

	student_id = models.CharField(max_length=12)
	semester = models.ForeignKey(Semester, related_name='%(class)s_sem', on_delete=models.CASCADE,
									verbose_name="Semester Name")
	exam_venue = models.ForeignKey(ExamVenue,related_name='%(class)s_ev', on_delete=models.CASCADE,
									  verbose_name="Exam Venue Name")
	lock_flag = models.BooleanField(default=1)

	def __str__(self):
		return str(self.student_id)


class HallTicketException(models.Model):

	student_id = models.CharField(max_length=12)
	semester = models.ForeignKey(Semester, related_name='%(class)s_sem', on_delete=models.CASCADE,
									verbose_name="Semester Name", null=True, blank=True)
	exception_end_date = models.DateField(blank=True, null=True)

	class Meta:
		unique_together = ('student_id','semester',)


	def __str__(self):
		return str(self.student_id)


def path_and_rename(instance, filename):
	upload_to = ''
	ext = filename.split('.')[-1]
	filename = '{}.{}'.format(instance.student_id, ext)
	return os.path.join(upload_to, filename)


class UploadStudentPhoto(models.Model):

	student_id = models.CharField(max_length=12)
	student_photo = models.ImageField(upload_to=path_and_rename)

	def __str__(self):
		return str(self.student_id)

	def clean(self):
		from django.core.exceptions import ValidationError
		photo = self.student_photo
		if not photo:
			raise ValidationError("Please select a Student Photo")
		fileName, fileExtension = os.path.splitext(str(photo))
		extensions = set(['.jpg', '.png'])
		if self.student_id and not Student.objects.filter(student_id=self.student_id).first():
			raise ValidationError("Invalid student ID")

		if fileExtension != '' and fileExtension.lower() not in extensions:
			raise ValidationError("Invalid File Format")
