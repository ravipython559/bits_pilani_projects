from django import forms
from master.models import *
from django.db.models import Q, F, Value, OuterRef, Subquery
from django.db.models.functions import Concat
from master.utils.forms.widgets import ForeignTextWidget
from master.utils.extra_models.querysets import get_all_instances, get_filter_queryset
from django.core.validators import MaxValueValidator, MinValueValidator
from master.forms.form_fields import *
from ema import default_settings as S
from django.db.models.functions import Upper


class ProgramSemesterForm(forms.Form):

	program = forms.ModelChoiceField(label = 'Select Program',
			widget = forms.Select(attrs = {'style':'width:70%','class':'form-control'}),
			empty_label = 'Choose Program',
			queryset = get_all_instances(Program),
			required=False,
			to_field_name='program_code',
	)

	semester = forms.ModelChoiceField(label = 'Select Semester',
			widget = forms.Select(attrs = {'style':'width:70%','class':'form-control'}),
			empty_label = 'Choose Semester',
			queryset = get_all_instances(Semester),
			required=False,
	)

	search = forms.CharField(required=False, widget=forms.HiddenInput())


class LocationVenueForm(forms.Form):

	location = forms.ModelChoiceField(label='Choose Location',
			empty_label='Choose Location',
			queryset=Location.objects.exclude(location_name=S.LOCATION),
			required=False,
	)

	exam_venue = forms.ModelChoiceField(label='Choose Exam Venue',
			empty_label='Choose Venue',
			queryset=ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME),
			required=False,
	)

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['location'].widget.attrs = {'class':'form-control',}
		self.fields['exam_venue'].widget.attrs = {'class':'form-control',}

def attendance_form(user,*args,**kwargs):
	class LocationVenueCourseForm(LocationVenueForm):

		course = forms.ModelChoiceField(label = 'Choose Course',
				empty_label = 'Choose Course',
				queryset = CourseExamShedule.objects.annotate(
					course_code_name=Concat('course_code',Value(':'),'course_name')).values_list("course_code_name",flat=True).distinct(),
				to_field_name = "course_code_name",

				required = False,
				)

		def __init__(self,*args,**kwargs):
			super().__init__(*args,**kwargs)
			self.fields['course'].widget.attrs = {'class':'form-control',}
			self.fields['course'].queryset = CourseExamShedule.objects.none()
			self.fields['exam_venue'].queryset = ExamVenue.objects.none()
			if not user.is_superuser:
				self.fields['location'].queryset = Location.objects.filter(locationcoordinator_loc__coordinator_email_id=user.email)
	return LocationVenueCourseForm

class AdminLocVenueCourseForm(LocationVenueForm):
	course = forms.ModelChoiceField(label='Choose Course',
		empty_label='Choose Course',
		queryset=CourseExamShedule.objects.all(),
		required=False,
	)

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['course'].widget.attrs = {'class':'form-control',}

class AdminLocVenueCourseCodeForm(AdminLocVenueCourseForm):
	course = forms.ModelChoiceField(label='Choose Course',
			empty_label='Choose Course',
			queryset=CourseExamShedule.objects.annotate(course_code_name=Concat('course_code',Value(':'),'course_name')).values_list("course_code_name",flat=True).distinct(),
			to_field_name = "course_code_name",
			required=False,
		)

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['course'].widget.attrs = {'class':'form-control',}

def student_attendance_form(user=None):

	class StudentAttendanceReportForm(forms.Form):

		exam_type = ExamTypeChoiceField(label = 'Choose Exam Type',
				empty_label = 'Choose Exam Type',
				queryset = ExamType.objects.filter(pk__in=Subquery(
					CurrentExam.objects.filter(
						exam_type=OuterRef('pk'),
						is_active=True
						).values('exam_type')),
				))

		exam_venue = forms.ModelChoiceField(label='Choose Exam Venue',
				empty_label='Choose Venue',
				queryset=ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME),
			)

		course = forms.ModelChoiceField(label = 'Choose Course',
				empty_label = 'Choose Course',
				queryset = CourseExamShedule.objects.all(),
				required = False,
			)
		exam_slot = forms.ModelChoiceField(label = 'Choose Exam Slot',
					empty_label = 'Choose Exam Slot',
					queryset = ExamSlot.objects.exclude(slot_name=S.EXAM_SLOT_NAME),
					required=False,
			)

		def __init__(self,*args,**kwargs):
			super().__init__(*args,**kwargs)
			self.fields['course'].widget.attrs = {'class':'form-control',}
			self.fields['exam_type'].widget.attrs = {'class':'form-control',}
			self.fields['exam_venue'].widget.attrs = {'class':'form-control',}
			self.fields['exam_slot'].widget.attrs = {'class':'form-control',}

	return StudentAttendanceReportForm


def exam_attendance_summary_report_form(user=None):
	class ExamAttendanceReportForm(forms.Form):

		exam_type = ExamTypeChoiceField(label = 'Choose Exam Type',
				empty_label = 'Choose Exam Type',
				queryset = ExamType.objects.filter(pk__in=Subquery(
					CurrentExam.objects.filter(
						exam_type=OuterRef('pk'),
						is_active=True
						).values('exam_type')),
				))
		exam_slot = forms.ModelChoiceField(label = 'Choose Exam Slot',
					empty_label = 'Choose Exam Slot',
					queryset = ExamSlot.objects.exclude(slot_name=S.EXAM_SLOT_NAME),
			)

		def __init__(self,*args,**kwargs):
			super().__init__(*args,**kwargs)
			self.fields['exam_type'].widget.attrs = {'class':'form-control',}
			self.fields['exam_slot'].widget.attrs = {'class':'form-control',}

	return ExamAttendanceReportForm


def student_attendance_count_form(user=None):
	class StudentAttendanceCountForm(forms.Form):

		exam_type = ExamTypeChoiceField(label = 'Choose Exam Type',
				empty_label = 'Choose Exam Type',
				queryset = ExamType.objects.filter(pk__in=Subquery(
					CurrentExam.objects.filter(
						exam_type=OuterRef('pk'),
						is_active=True
						).values('exam_type')),
				))

		exam_slot = forms.ModelChoiceField(label = 'Choose Exam Slot',
					empty_label = 'Choose Exam Slot',
					queryset = ExamSlot.objects.exclude(slot_name=S.EXAM_SLOT_NAME),
			)

		def __init__(self,*args,**kwargs):
			super().__init__(*args,**kwargs)
			self.fields['exam_type'].widget.attrs = {'class':'form-control',}

	return StudentAttendanceCountForm



class ProgramLocationVenueForm(LocationVenueForm):

	program = forms.ModelMultipleChoiceField(label="Choose Program",
		queryset=Program.objects.all().order_by('program_code'),
		required=False,
        
	)

	date = forms.DateField(input_formats=['%Y-%m-%d %H:%M'],label="Enter Date",required=False)
	
	exam_slot = forms.ModelChoiceField(label='Choose Exam Slot',
			empty_label='Choose Exam Slot',
			queryset = ExamSlot.objects.none(),
			required=False,
	)
	exam_type = forms.ModelChoiceField(label='Choose Exam Type',
			empty_label='Choose Exam Type',
			queryset = ExamType.objects.filter(pk__in=Subquery(
					CurrentExam.objects.filter(
						exam_type=OuterRef('pk'),
						is_active=True
						).values('exam_type'))),
			required=False,)
	# photo_missing = forms.BooleanField(label="View Students with Missing Photos", required=False,)
	hidden_search = forms.CharField(required=False, widget=forms.HiddenInput() )

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['exam_venue'].help_text = "Select the Location First"
		# self.fields['checkbox'].widget.attrs = {'class':'form-control',}
		self.fields['program'].widget.attrs = {'class':'form-control',}
		self.fields['exam_slot'].widget.attrs = {'class':'form-control',}
		self.fields['exam_type'].widget.attrs = {'class':'form-control',}
		self.fields['date'].widget.attrs = {'class':'form-control',}
		exam_type_name = CurrentExam.objects.filter(is_active=True).distinct().values_list('exam_type',flat=True)
		exam = ExamVenueSlotMap.objects.filter(exam_type__in=exam_type_name).distinct().values_list('exam_slot',flat=True)
		exam_list = ExamVenueSlotMap.objects.filter(exam_slot__in=exam).distinct().values_list('exam_slot',flat=True)
		self.fields['exam_slot'].queryset = ExamSlot.objects.filter(id__in=exam_list,slot_date__gte=datetime.date.today()-datetime.timedelta(days=30)).exclude(id=1).order_by('slot_date')


class SyncSDMSEmailandPhoneForm(forms.Form):
	program = forms.ModelChoiceField(label="Choose Program",
				queryset=Program.objects.all().order_by('program_code'),
				required=False,)

	program_type = forms.ModelChoiceField(label="Choose Program Type",
				   queryset=Program.objects.all().distinct().values_list('program_type',flat=True).order_by('program_type'),
				   required=False,)

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['program'].widget.attrs = {'class':'form-control',}
		self.fields['program_type'].widget.attrs = {'class':'form-control',}

class BulkActivateInactivateForm(forms.Form):

	program_type = forms.ModelChoiceField(label="Program Type",empty_label="Choose Program Type",
				   queryset=Program.objects.all().distinct().values_list(Upper('program_type'),flat=True).order_by('program_type'),
				   required=True,)

	program = forms.ModelMultipleChoiceField(label="Choose Program",
											 queryset=Program.objects.all().order_by('program_code'),
											 required=False,
											 )
	semester = forms.ModelChoiceField(label="Semester",empty_label="Choose Semester",
				   queryset=Semester.objects.all().distinct().values_list('semester_name',flat=True).order_by('-semester_name'),
				   required=False,help_text='Mandatory except for Certification Programs')

	exam_type = forms.ModelChoiceField(label='Exam Type', empty_label = 'Choose Exam Type',
				queryset = ExamType.objects.all(),
				required=False,help_text='(Choose Evaluation Type First)',
									   disabled=True)
	evaluation_type = forms.ModelChoiceField(label='Evaluation Type', empty_label = 'Choose Evaluation Type',
				queryset = ExamType.objects.all().distinct().values_list('evaluation_type',flat=True).order_by('-evaluation_type').exclude(id=1),
				required=True,)

	batch = forms.ModelChoiceField(label='Batch', empty_label = 'Choose Batch',
			queryset = Batch.objects.all().distinct().values_list('batch_name',flat=True).order_by('-batch_name'),
			required=False,help_text='Mandatory for Certification Programs')

	def __init__(self,*args,**kwargs):
		super(BulkActivateInactivateForm, self).__init__(*args,**kwargs)

		self.fields['program_type'].widget.attrs = {'class':'form-control','style':'width:50%',}
		self.fields['program'].widget.attrs = {'class':'form-control','style':'width:84%','disabled':'true',}
		self.fields['semester'].widget.attrs = {'class':'form-control','style':'width:60%;margin-left: 2px;'}
		self.fields['evaluation_type'].widget.attrs = {'class':'form-control','style':'width:60%;margin-left: 5px;'}
		self.fields['exam_type'].widget.attrs = {'class':'form-control','style':'width:100%',}
		self.fields['batch'].widget.attrs = {'class':'form-control','style':'width:60%',}



class ProgramForm(forms.Form):
	program = forms.ModelMultipleChoiceField(label="Choose Program",
											 queryset=Program.objects.all().order_by('program_code'),

											 required=False,
											 )

	exam_slot = forms.ModelMultipleChoiceField(label='Choose Exam Slot',
											   queryset=ExamSlot.objects.none(),
											   required=False,
											   )


	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['program'].widget.attrs = {'class':'form-control',}
		self.fields['exam_slot'].widget.attrs = {'class':'form-control',}
		exam_type_name = CurrentExam.objects.filter(is_active=True).distinct().values_list('exam_type',flat=True)
		exam = ExamVenueSlotMap.objects.filter(exam_type__in=exam_type_name).distinct().values_list('exam_slot',flat=True)
		exam_list = ExamVenueSlotMap.objects.filter(exam_slot__in=exam).distinct().values_list('exam_slot',flat=True)
		self.fields['exam_slot'].queryset = ExamSlot.objects.filter(id__in=exam_list,slot_date__gte=datetime.date.today()-datetime.timedelta(days=30)).exclude(id=1).order_by('-slot_date')

class AttendanceDataForm(forms.ModelForm):
	location = forms.CharField(required=False)
	exam_venue_name = forms.CharField(required=False)
	course_code = forms.CharField(required=False)
	course_name = forms.CharField(required=False)
	student_planned = forms.CharField(required=False)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['location'].widget = forms.HiddenInput()
		self.fields['exam_venue_name'].widget = forms.HiddenInput()
		self.fields['course_code'].widget = forms.HiddenInput()
		self.fields['course_name'].widget = forms.HiddenInput()
		self.fields['course'].widget = forms.HiddenInput()
		self.fields['exam_venue'].widget = forms.HiddenInput()
		self.fields['semester'].widget = forms.HiddenInput()
		self.fields['exam_type'].widget = forms.HiddenInput()
		self.fields['exam_slot'].widget = forms.HiddenInput()
		self.fields['student_planned'].widget = forms.HiddenInput()
		#self.fields['attendance_count'].required = True

		self.empty_permitted = False

	class Meta:
		model = ExamAttendance
		exclude = ('created_on','last_update_on','last_update_by',)


def get_examformset(ema_queryset):
	class ExamAttendanceFormSet(forms.BaseModelFormSet):
		def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
		queryset=None, initial=None, **kwargs):
			super().__init__(data=data, files=files, auto_id=auto_id, prefix=prefix,
		queryset=ema_queryset, initial=initial, **kwargs)

	return ExamAttendanceFormSet

def course_exam_schedule_form(*args,**kwargs):

	class CourseExamSheduleForm(forms.Form):

		semester = forms.ModelChoiceField(label = 'Select Semester',
				widget = forms.Select(attrs = {'class':'form-control'}),
				empty_label = '------------',
				queryset = get_all_instances(Semester),
				required=False,	
		)# fix me : vishal

		exam_type = forms.ModelChoiceField(label = 'Select Exam Type',
				widget = forms.Select(attrs = {'class':'form-control'}),
				empty_label = '------------',
				queryset = ExamType.objects.exclude(exam_type = S.EXAM_TYPE),
				required=False,
		)

		exam_slot = forms.ModelChoiceField(label = 'Select Exam Slot',
				widget = forms.Select(attrs = {'class':'form-control'}),
				empty_label = '------------',
				queryset =ExamSlot.objects.exclude(slot_name = S.EXAM_SLOT_NAME),
				required=False,
		)
	return CourseExamSheduleForm(*args, **kwargs)
