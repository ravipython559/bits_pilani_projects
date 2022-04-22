from import_export import resources, widgets
from import_export.fields import Field 
from import_export.formats import base_formats
from master.models import *
from django.core.exceptions import ValidationError
from . import resources_widgets as W
from .resources_headers import *

DEFAULT_FORMATS = (
		base_formats.CSV,)

class ResCourseExamSchedule(resources.ModelResource):
	class CourseCodeField(Field):
		def clean(self,data):
			return ''.join(super().clean(data).split())

	course_code = CourseCodeField(attribute='course_code', column_name=CES_HEADER['course_code'], 
		widget=W.TextWidget())
	course_name = Field(attribute='course_name', column_name=CES_HEADER['course_name'], 
		widget=W.TextWidget())
	semester = Field(attribute='semester', column_name=CES_HEADER['semester'],
		widget=W.SemesterForeignKeyWidget(Semester, 'semester_name')) # fix me: vishal we need proper testing
	batch = Field(attribute='batch', column_name=CES_HEADER['batch'],
		widget=W.BatchForeignKeyWidget(Batch, 'batch_name')) # fix me: vishal we need proper testing
	exam_slot = Field(attribute='exam_slot', column_name=CES_HEADER['exam_slot'],
		widget=W.ForeignKeyWidget(ExamSlot, 'slot_name'))
	exam_type = Field(attribute='exam_type', column_name=CES_HEADER['exam_type'],
		widget=W.ForeignKeyWidget(ExamType, 'exam_type'))
	comp_code = Field(attribute='comp_code', column_name=CES_HEADER['comp_code'],
		widget=widgets.IntegerWidget())
	unit = Field(attribute='unit', column_name=CES_HEADER['unit'],
		widget=W.NumberIntWidget())

	def before_import(self, dataset, using_transactions, dry_run, **kwargs):
		diff_col = set(self.get_diff_headers()) - set(dataset.headers)
		if diff_col:
			raise ValidationError("Column {} not found in dataset".format(diff_col))

	class Meta:
		model = CourseExamShedule		
		fields = ('course_code', 'course_name', 'semester', 'batch', 'exam_slot', 
			'exam_type', 'comp_code', 'unit',
		)
		import_id_fields = ('course_code', 'exam_type','semester','batch')


class ResStudent(resources.ModelResource):
	class StudentIdField(Field):
		def clean(self,data):
			return ''.join(super().clean(data).split())

	student_id = StudentIdField(attribute='student_id', column_name=CES_HEADER['student_id'],
		widget=W.TextWidget())
	student_name = Field(attribute='student_name', column_name=CES_HEADER['student_name'],
		widget=W.TextWidget())
	batch = Field(attribute='batch', column_name=CES_HEADER['batch'],
		widget=W.ForeignKeyWidget(Batch, 'batch_name'))

	def before_import(self, dataset, using_transactions, dry_run, **kwargs):
		diff_col = set(self.get_diff_headers()) - set(dataset.headers)
		if diff_col:
			raise ValidationError("Column {} not found in dataset".format(diff_col))

	class Meta:
		model = Student
		fields = ('student_id', 'student_name', 'batch',)
		import_id_fields = ('student_id',)


class OnlineExamAttendanceResource(resources.ModelResource):

	class StudentIdField(Field):
		def clean(self,data):
			return ''.join(super().clean(data).split())

	class CourseCodeField(Field):
		def clean(self,data):
			return ''.join(super().clean(data).split())

	student_id = StudentIdField(attribute='student_id', column_name='student_id',
		widget=W.TextWidget())

	exam_type = Field(attribute='exam_type', column_name='exam_type',
		widget=W.ForeignKeyWidget(ExamType, 'exam_type'))

	semester = Field(attribute='semester', column_name='semester',
			widget=W.ForeignKeyWidget(Semester, 'semester_name'))

	course_code = CourseCodeField(attribute='course_code', column_name='course_code', 
		widget=widgets.CharWidget())

	makeup_allowed =  Field(attribute='makeup_allowed', column_name='makeup_allowed',
		widget=W.BooleanWidgetForNull())

	course_name = Field(attribute='course_name', column_name='course_name', 
		widget=widgets.CharWidget())

	exam_date = Field(attribute='exam_date', column_name='exam_date', 
		widget=widgets.DateWidget())

	total_questions = Field(attribute='total_questions', column_name='total_questions',
		widget=widgets.IntegerWidget())

	total_attempted = Field(attribute='total_attempted', column_name='total_attempted',
		widget=widgets.IntegerWidget())

	total_blank = Field(attribute='total_blank', column_name='total_blank',
		widget=widgets.IntegerWidget())

	image_uploaded = Field(attribute='image_uploaded', column_name='image_uploaded',
		widget=widgets.IntegerWidget())


	test_start_time = Field(attribute='test_start_time', column_name='test_start_time', 
		widget=widgets.CharWidget())

	test_end_time = Field(attribute='test_end_time', column_name='test_end_time', 
		widget=widgets.CharWidget())

	submission_type = Field(attribute='submission_type', column_name='submission_type', 
		widget=widgets.CharWidget())


	def before_import(self, dataset, using_transactions, dry_run, **kwargs):
		remove_white_space_from_header = []
		for i in dataset.headers:
			remove_white_space_from_header.append(i.strip())

		dataset.headers = remove_white_space_from_header
		diff_col = set(self.get_diff_headers()) - set(dataset.headers)
		if diff_col:
			raise ValidationError("Column {} not found in dataset".format(diff_col))

		for row in dataset:
			#check if maditory fields provided with null or empty value.

			if row[0]=='' or row[0] is None:
				raise ValidationError("student_id is mandatory {}".format(row))
			if row[1]=='' or row[1] is None:
				raise ValidationError("exam_type is mandatory {}".format(row))
			if row[2]=='' or row[2] is None:
				raise ValidationError("course_code is mandatory {}".format(row))

	class Meta:
		model = OnlineExamAttendance
		fields = ('student_id', 'exam_type', 'semester', 'course_code','makeup_allowed', 
			'course_name', 'exam_date', 'total_questions','total_attempted','total_blank','image_uploaded',
			'test_start_time','test_end_time','submission_type',
		)
		import_id_fields = ('student_id','exam_type','semester','course_code',)


class ExamVenueLockResource(resources.ModelResource):
	class StudentIdField(Field):
		def clean(self, data):
			return ''.join(super().clean(data).split())

	student_id = StudentIdField(attribute='student_id', column_name=EXAM_VENUE_LOCK_HEADER['student_id'],
								widget=W.TextWidget())
	exam_venue = Field(attribute='exam_venue', column_name=EXAM_VENUE_LOCK_HEADER['exam_venue_id'],
				  widget=W.ExamVenueLockForeignKeyWidget(ExamVenue, 'venue_short_name'))
	semester = Field(attribute='semester', column_name=EXAM_VENUE_LOCK_HEADER['semester_id'],
					 widget=W.SemesterForeignKeyWidget(Semester,
													   'semester_name'))

	def before_import(self, dataset, using_transactions, dry_run, **kwargs):
		remove_white_space_from_header = []
		for i in dataset.headers:
			remove_white_space_from_header.append(i.strip())
		dataset.headers = remove_white_space_from_header
		diff_col = set(self.get_diff_headers()) - set(dataset.headers)
		if diff_col:
			raise ValidationError("Column {} not found in dataset".format(diff_col))

		check_semester_name = Semester.objects.all().values_list('semester_name', flat=True)
		check_exam_venue_name = ExamVenue.objects.all().values_list('venue_short_name', flat=True)

		for row in dataset:
			#check if maditory fields provided with null or empty value.
			if row[0]=='' or row[0] is None:
				raise ValidationError("student_id is mandatory {}".format(row))
			if row[2]=='' or row[2] is None:
				raise ValidationError("semester is mandatory {}".format(row))
			if row[1]=='' or row[1] is None:
				raise ValidationError("exam_venue is mandatory {}".format(row))

			#check semester and exam venue entered correctly from DB.
			#row[2] is semester name
			#row[1] is exam venue

			#if row[2] not in check_semester_name:
				#raise ValidationError("semester name is not matching correctly please check {} this are semester names {}".format(row[2],list(check_semester_name)))
			#if row[1] not in check_exam_venue_name:
				#raise ValidationError("exam venue is not matching correctly please check {} this are exam venue {}".format(row[1],list(check_exam_venue_name)))

	class Meta:
		model = ExamVenueLock
		skip_unchanged = True
		report_skipped = True
		exclude = ('id',)
		import_id_fields = ('student_id','exam_venue','semester',)


class ResStudentRegistration(resources.ModelResource):

	class CourseCodeField(Field):
		def clean(self,data):
			course_code_upper=''.join(super().clean(data).split())
			return course_code_upper.upper()

	class StudentIdField(Field):
		def clean(self,data):
			return ''.join(super().clean(data).split())

	Student_id = Field(attribute='student', column_name='Student_id',
			widget=W.ForeignKeyWidget(Student, 'student_id'))
	course_code = CourseCodeField(attribute='course_code', column_name='course_code', 
		widget=W.TextWidget())


	semester = Field(attribute='semester', column_name='semester',
		widget=W.SemesterForeignKeyWidget(Semester, 'semester_name'))


	def before_import(self, dataset, using_transactions, dry_run, **kwargs):
		remove_white_space_from_header = []
		for row in dataset:
			student_object = Student.objects.filter(student_id=row[0]).first()
			if not student_object:
				Student.objects.create(student_id=row[0], student_name='-')
		for i in dataset.headers:
			remove_white_space_from_header.append(i.strip())
		dataset.headers = remove_white_space_from_header
		diff_col = set(self.get_diff_headers()) - set(dataset.headers)
		if diff_col:
			raise ValidationError("Column {} not found in dataset".format(diff_col))

	class Meta:
		model = StudentRegistration
		fields = ['Student_id','course_code','semester']
		import_id_fields = ('Student_id','course_code','semester',)


class ResHallTicketException(resources.ModelResource):
	
	student_id = Field(attribute='student_id', column_name=CES_HEADER['student_id'],
		widget=W.TextWidget())
	semester = Field(attribute='semester', column_name=CES_HEADER['semester'],
		widget=W.SemesterWidget()) # fix me: vishal we need proper testing
	exception_end_date = Field(attribute='exception_end_date', column_name=CES_HEADER['exception_end_date'],
		widget=W.ExceptionEndDate())

	def before_import(self, dataset, using_transactions, dry_run, **kwargs):
		diff_col = set(self.get_diff_headers()) - set(dataset.headers)
		if diff_col:
			raise ValidationError("Column {} not found in dataset".format(diff_col))
		row_count = 0
		for row in dataset:
			row_count = row_count +1
			if row[0]:
				student_object = Student.objects.filter(student_id=row[0]).first()
				if not student_object:
					raise ValidationError("Student ID  at row {} not found in Student table. Please make the student entry in the Student table first". format(row_count))

				program_object = Program.objects.filter(program_code=row[0][4:8]).first()
				if program_object.program_type != 'certification':
					if not row[1]:
						raise ValidationError("Please pass the Semester Name at row {}".format(row_count))
					semester_object = Semester.objects.filter(semester_name=row[1].strip()).first()
					if not semester_object:
						raise ValidationError("Please pass the Correct Semester Name at row {}".format(row_count))
				if program_object.program_type == 'certification':
					if row[1]:
						raise ValidationError("Since it is a Certification Course Please remove the Semester Name at row {}".format(row_count))

	class Meta:
		model = HallTicketException		
		fields = ('student_id', 'semester', 'exception_end_date',
		)
		import_id_fields = ('student_id','semester',)

