from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from master.models import *
from master.utils.extra_models.querysets import get_instance_or_none, get_date_day_or_empty
from django.core.exceptions import ValidationError
from django.core.validators import (_lazy_re_compile, EmailValidator)
import re
from django.db.models import Q, Value, When, Case
from master.forms.form_fields import *
from django.db.models import IntegerField
from ema import default_settings as S  
from django.utils.translation import ugettext_lazy as _

class ExamVenueForm(forms.ModelForm):
	is_active=forms.BooleanField(initial=True, required=False,)
	location = LocationChoiceField(empty_label=None, 
	queryset=Location.objects.all()
	)

	def clean_location(self):
		location = self.cleaned_data.get('location')
		if location.location_name == S.LOCATION:
			raise forms.ValidationError(_('This field is required'),)
		return location
	

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['is_active'].help_text = "The center is deactivated. It will now not be available for assigning any exam slot" if (self.instance.pk and not (self.instance.is_active)) else " "

	class Meta(object):
		model = ExamVenue
		fields = '__all__'

class LocationCoordinatorForm(forms.ModelForm):
	location = LocationChoiceField(empty_label=None, 
	queryset=Location.objects.all()
	)

	def clean_location(self):
		location = self.cleaned_data.get('location')
		if location.location_name == S.LOCATION:
			raise forms.ValidationError(_('This field is required'),)
		return location

	def clean_coordinator_email_id(self):
		coordinator_email_id = self.cleaned_data.get('coordinator_email_id')
		class BitsEmailValidator(EmailValidator):
		 	domain_regex= _lazy_re_compile(settings.BITS_EMAIL_DOMAIN, re.IGNORECASE)
		BitsEmailValidator()(coordinator_email_id.strip())
		return coordinator_email_id

	class Meta(object):
		model=LocationCoordinator
		fields='__all__'


class CourseExamSheduleForm(forms.ModelForm):
	semester = SemesterModelChoiceField(empty_label=None, 
		queryset=Semester.objects.filter(
			Q(currentexam_sem__is_active=True)|Q(semester_name=S.SEMESTER_NAME)
			).distinct()
		)
	batch = BatchModelChoiceField(empty_label=None, queryset=Batch.objects.all())
	exam_slot = ExamSlotChoiceField(empty_label=None, queryset=ExamSlot.objects.all())
	
	def clean_exam_slot(self):
		exam_slot = self.cleaned_data['exam_slot']
		if exam_slot.slot_name  == S.EXAM_SLOT_NAME:
			raise forms.ValidationError(_('This field is required'),)
		return exam_slot

	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.fields['exam_type'].queryset = ExamType.objects.filter(currentexam_et__is_active=True).distinct()

	class Meta(object):
		model=CourseExamShedule
		exclude = ('exam_venue_slot_maps','inserted_on','last_update_on', )


class ExamVenueSlotMapAjaxForm(forms.ModelForm):
	class Meta(object):
		model = ExamVenueSlotMap
		fields = ('exam_venue',)

class ExamVenueSlotMapForm(forms.ModelForm):
	location = LocationChoiceField(empty_label=None, queryset=Location.objects.all(),)
	address = forms.CharField(disabled=True, required=False,widget=forms.Textarea)
	pincode = forms.DecimalField(disabled=True, required=False)
	exam_type = ExamTypeChoiceField(empty_label=None, queryset=ExamType.objects.all())
	exam_slot = ExamSlotChoiceField(empty_label=None, queryset=ExamSlot.objects.all())

	def clean_exam_slot(self):
		exam_slot = self.cleaned_data['exam_slot']
		if exam_slot.slot_name==S.EXAM_SLOT_NAME:
			raise forms.ValidationError("Exam Slot is mandatory", code='invalid')
		return exam_slot

	def clean_exam_type(self):
		exam_type = self.cleaned_data['exam_type']
		if exam_type.exam_type==S.EXAM_TYPE:
			raise forms.ValidationError("Exam Type is mandatory", code='invalid')	
		return exam_type

	def clean_location(self):
		location = self.cleaned_data['location']
		if location.location_name==S.LOCATION:
			raise forms.ValidationError("Location is mandatory", code='invalid')	
		return location

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		if self.instance.pk:
			self.fields['address'].initial = self.instance.exam_venue.venue_address
			self.fields['pincode'].initial = self.instance.exam_venue.pin_code
			self.fields['location'].initial = self.instance.exam_venue.location
			ActiveExamVenue = ExamVenue.objects.filter(location=self.instance.exam_venue.location ,is_active=True)
			self.fields['exam_venue'].queryset = ActiveExamVenue

	class Meta(object):
		model = ExamVenueSlotMap
		fields = ('location', 'exam_venue', 'address', 'pincode', 'exam_type', 'exam_slot', 'student_count_limit')


class ExamVenueAddressAjaxForm(forms.ModelForm):
	venue_address = forms.CharField(disabled=True, widget=forms.Textarea)
	pin_code = forms.DecimalField(disabled=True)
	student_count_limit = forms.IntegerField()

	class Meta(object):
		model = ExamVenue
		fields = ('venue_address', 'pin_code','student_count_limit')

class CurrentExamForm(forms.ModelForm):
	semester = SemesterModelChoiceField(empty_label=None, queryset=Semester.objects.all())
	batch = BatchModelChoiceField(empty_label=None, queryset=Batch.objects.all())
	exam_type = ExamTypeChoiceField(empty_label=None, queryset=ExamType.objects.all())
	exm_slot_fn = forms.CharField(required=False,widget=forms.TextInput(attrs={'size': '50'}),label='Exam Slot Time Text (Forenoon)',help_text='The text entered here shows as the forenoon time slot detail on the first page of the hall tkt just below the course exam schedule. If not entered the default text “Forenoon (FN) Session: 10:00 AM to 12:15 PM IST” will show. Please enter carefully as the text will show as-is on the hall ticket')
	exm_slot_an = forms.CharField(required=False,widget=forms.TextInput(attrs={'size': '50'}),label='Exam Slot Time Text (Afternoon)',help_text='The text entered here shows as the afternoon time slot detail on the first page of the hall tkt just below the course exam schedule. If not entered the default text “Afternoon (AN) Session: 2:00 PM to 4:15 PM IST” will show. Please enter carefully as the text will show as-is on the hall ticket')


	def clean_exam_type(self):
		exam_type = self.cleaned_data['exam_type']
		if exam_type.exam_type  == S.EXAM_TYPE:
			raise forms.ValidationError(_('This field is required'),)
		return exam_type

	def clean_hall_tkt_template(self):
		hall_tkt_template = self.cleaned_data['hall_tkt_template']
		if not self.cleaned_data['hall_tkt_template']:
			raise forms.ValidationError(_('This field is required'), )
		return hall_tkt_template

	def clean(self, *args, **kwargs):
		if any(self.errors): return

		program = self.cleaned_data['program']
		batch = self.cleaned_data['batch']
		semester = self.cleaned_data['semester']
		exam_type = self.cleaned_data['exam_type']
		eval_typ=exam_type.evaluation_type
		is_active= self.cleaned_data['is_active']
		exm_slot_fn = self.cleaned_data['exm_slot_fn'].upper()
		self.cleaned_data['exm_slot_fn']=exm_slot_fn
		exm_slot_an = self.cleaned_data['exm_slot_an'].upper()
		self.cleaned_data['exm_slot_an']=exm_slot_an


		if ( not(program.program_type == Program.CERTIFICATION) and semester.semester_name == S.SEMESTER_NAME):
			raise forms.ValidationError(
				_('Semester Manadatory for %(value)s program'),
				params={'value': program.program_type }
				)



		current_exam_object = CurrentExam.objects.filter(program=program, semester=semester, batch=batch, is_active=True).exclude(hall_tkt_template=None)

		#Check conditions only if exam is active
		if is_active:
			#Check for the same entry with program semester batch and active true
			if current_exam_object:
				current_exam_object_ids = []
				for i in current_exam_object:
					current_exam_object_ids.append(i.id)
				#Check while editing we are not comparing the template of the same entry
				if self.initial:
					currently_editing_current_exam_object = CurrentExam.objects.filter(program__id=self.initial['program'],
																					   semester__id=self.initial['semester'], batch__id=self.initial['batch'],
																					   exam_type__id=self.initial['exam_type'])
					if currently_editing_current_exam_object[0].id in current_exam_object_ids:
						current_exam_object_ids.remove(currently_editing_current_exam_object[0].id)
					if current_exam_object_ids:
						if currently_editing_current_exam_object[0].id != current_exam_object_ids[0]:
							current_exam_object = CurrentExam.objects.filter(id=current_exam_object_ids[0])
							if current_exam_object[0].hall_tkt_template != self.cleaned_data['hall_tkt_template']:
								raise ValidationError("There is another active exam entry for the same program, semester and batch with different slot and / or template details. This is currently NOT allowed. Please ensure that slot and template details are the same")
				else:
					if current_exam_object[0].hall_tkt_template != self.cleaned_data['hall_tkt_template']:
						raise ValidationError(
							"There is another active exam entry for the same program, semester and batch with different slot and / or template details. This is currently NOT allowed. Please ensure that slot and template details are the same")

		#if (not (program.program_type == Program.NON_SPECIFIC) and batch.batch_name == S.BATCH_NAME):
		#	raise forms.ValidationError(
		#		_('Batch Manadatory for %(value)s program'),
		#		params={'value': program.program_type }
		#		)

		if is_active:
			current_exam_info = CurrentExam.objects.filter(program=program, batch=batch, semester=semester, is_active=is_active).last()

			if(current_exam_info and current_exam_info.exam_type.evaluation_type != exam_type.evaluation_type):
				raise forms.ValidationError(_('You cannot have active exams with different evaluation types for the same program, semester and batch'))
		else:
			if self.cleaned_data['hall_tkt_change_flag'] or self.cleaned_data['missing_tkt_exception_flag']:
				raise forms.ValidationError(_(
					'Hall ticket generation cannot be done for inactive exams. Please uncheck the checkboxes for hall ticket generation and save the entry'))

		val = CurrentExam.objects.filter(program=self.cleaned_data['program'],batch=batch, semester=semester,is_active=True)
		if val:
			if val.count()>1:# if more than one exam is active
				regular=val[0] if "Reg" in val[0].exam_type.exam_type else val[1]
				makeup=val[0] if "Makeup" in val[0].exam_type.exam_type or "Mkp" in val[0].exam_type.exam_type else val[1]

				if (regular.exm_slot_fn=="") and (regular.exm_slot_an=="") and (makeup.exm_slot_fn=="") and (makeup.exm_slot_an==""):
					return super().clean(*args, **kwargs)
				

				if is_active:
					if regular:
						if "Regular" in exam_type.exam_type or "Reg" in exam_type.exam_type:
							if (makeup.exm_slot_fn=="") or (makeup.exm_slot_an==""):
								return super().clean(*args, **kwargs)
							elif (makeup.exm_slot_fn==exm_slot_fn) and (makeup.exm_slot_an==exm_slot_an):
								return super().clean(*args, **kwargs)	
							elif (exm_slot_fn!=makeup.exm_slot_fn ) or (exm_slot_an!=makeup.exm_slot_an):
								raise forms.ValidationError(_('There is another active exam entry for the same program, semester and batch with different slot and / or template details. This is currently NOT allowed. Please ensure that slot and template details are the same'))

					if makeup:
						if "Makeup" in exam_type.exam_type or "Mkp" in exam_type.exam_type:
							if (regular.exm_slot_fn=="") or (regular.exm_slot_an==""):
								return super().clean(*args, **kwargs)
							elif (regular.exm_slot_fn==exm_slot_fn) and (regular.exm_slot_an==exm_slot_an):
								return super().clean(*args, **kwargs)
							elif (exm_slot_fn!=regular.exm_slot_fn) or (exm_slot_an!=regular.exm_slot_an ):
								raise forms.ValidationError(_('There is another active exam entry for the same program, semester and batch with different slot and / or template details. This is currently NOT allowed. Please ensure that slot and template details are the same'))

			else:
				invalid = CurrentExam.objects.filter(program=self.cleaned_data['program'],batch=batch, semester=semester,exam_type__evaluation_type=eval_typ)
				if invalid.count()>1:
					regular=invalid[0] if "Reg" in invalid[0].exam_type.exam_type else invalid[1]
					makeup=invalid[0] if "Makeup" in invalid[0].exam_type.exam_type or "Mkp" in invalid[0].exam_type.exam_type else invalid[1]
					
					#if only active flag enabled and no changes in record
					if self.initial['is_active'] ==False and self.cleaned_data['is_active']==True and self.initial['exm_slot_fn'] == self.cleaned_data['exm_slot_fn'] and self.initial['exm_slot_an'] == self.cleaned_data['exm_slot_an']:
						if (regular.exm_slot_fn!=makeup.exm_slot_fn) or (regular.exm_slot_an!=makeup.exm_slot_an):
					 		raise forms.ValidationError(_('There is another active exam entry for the same program, semester and batch with different slot and / or template details. This is currently NOT allowed. Please ensure that slot and template details are the same'))
					
					 #compare entered values with existing db record
					elif self.initial['is_active'] ==False and self.cleaned_data['is_active']==True and self.initial['exm_slot_fn']=="" and self.initial['exm_slot_an'] == "":
						if regular.is_active!=False:#if editing value is regular 
							if(exm_slot_fn!=regular.exm_slot_fn) or (exm_slot_an!=regular.exm_slot_an):
								raise forms.ValidationError(_('There is another active exam entry for the same program, semester and batch with different slot and / or template details. This is currently NOT allowed. Please ensure that slot and template details are the same'))
						elif makeup.is_active!=False:#if editing value is makeup
							if(exm_slot_fn!=makeup.exm_slot_fn) or (exm_slot_an!=makeup.exm_slot_an):
								raise forms.ValidationError(_('There is another active exam entry for the same program, semester and batch with different slot and / or template details. This is currently NOT allowed. Please ensure that slot and template details are the same'))
				else:
					if not self.initial:
						if (invalid[0].program==self.cleaned_data['program'] and invalid[0].batch==self.cleaned_data['batch'] and invalid[0].semester==self.cleaned_data['semester'] and invalid[0].is_active==self.cleaned_data['is_active']):

							if(exm_slot_fn!=invalid[0].exm_slot_fn) or (exm_slot_an!=invalid[0].exm_slot_an):
								raise forms.ValidationError(_('There is another active exam entry for the same program, semester and batch with different slot and / or template details. This is currently NOT allowed. Please ensure that slot and template details are the same'))

		return super().clean(*args, **kwargs)

	class Meta(object):
		model = CurrentExam
		fields = '__all__'

class ExamSlotForm(forms.ModelForm):

	class Meta:
		model = ExamSlot
		fields = ('slot_name','slot_date','slot_day','slot_start_time',)
		widgets = {
            'slot_start_time': forms.TimeInput(format=('%H:%M')),
        }


class StudentForm(forms.ModelForm):
	batch = BatchModelChoiceField(empty_label=None, queryset=Batch.objects.all())

	class Meta:
		model = Student
		fields = ['student_id','student_name','batch',]


class StudentRegistrationForm(forms.ModelForm):
	semester = SemesterModelChoiceField(empty_label=None, queryset=Semester.objects.all())

	class Meta:
		model = StudentRegistration
		fields = ['course_code','student','semester',]


class HallTicketExceptionForm(forms.ModelForm):
	def clean_semester(self):
		semester = self.cleaned_data['semester']
		if self.cleaned_data.get('student_id') != None:
			student_object = Student.objects.filter(student_id=self.cleaned_data.get('student_id')).first()
			if not student_object:
				return semester
			program_object = Program.objects.filter(program_code=self.cleaned_data.get('student_id')[4:8]).first()
			if program_object.program_type != 'certification':
				if self.cleaned_data.get('semester') == None:
					raise ValidationError("Please pass the Semester Name")
				else:
					return semester
			elif program_object.program_type == 'certification':
				semester_object = Semester.objects.filter(id=1).first()
				return semester_object



	class Meta(object):
		model = HallTicketException
		fields = ['student_id', 'semester', 'exception_end_date']

	def clean(self, *args, **kwargs):
		if any(self.errors): return
		from django.core.exceptions import ValidationError
		if self.cleaned_data.get('student_id') != "":
			student_object = Student.objects.filter(student_id=self.cleaned_data.get('student_id')).first()
			if not student_object:
				raise ValidationError("Student ID not found in Student table. Please make the student entry in the Student table first")
			program_object = Program.objects.filter(program_code=self.cleaned_data.get('student_id')[4:8]).first()
			if program_object.program_type == 'certification':
				if self.has_changed():
					if self.initial:
						if len(self.changed_data) != 1:
							if self.initial.get('student_id')!=self.cleaned_data.get('student_id'):
								if HallTicketException.objects.filter(student_id=self.cleaned_data.get('student_id')).first():
									raise ValidationError("Hall ticket exception with this Student id already exists.")
							else:
								if HallTicketException.objects.filter(student_id=self.cleaned_data.get('student_id'),
																  exception_end_date=self.cleaned_data.get(
																	  'exception_end_date')).first():
									raise ValidationError("Hall ticket exception with this Student id already exists.")
					else:
							if HallTicketException.objects.filter(student_id=self.cleaned_data.get('student_id')).first():
								raise ValidationError("Hall ticket exception with this Student id already exists.")

		return super().clean(*args, **kwargs)

class OnlineExamAttendanceForm(forms.ModelForm):
	def clean_semester(self):
		semester = self.cleaned_data['semester']
		if self.cleaned_data.get('student_id') != None:
			student_object = Student.objects.filter(student_id=self.cleaned_data.get('student_id')).first()
			if not student_object:
				return semester

			program_object = Program.objects.filter(program_code=self.cleaned_data.get('student_id')[4:8]).first()
			if program_object.program_type != 'certification':
				if self.cleaned_data.get('semester') == None:
					raise ValidationError("Please pass the Semester Name")
				student_registration_object = StudentRegistration.objects.filter(
					course_code=self.cleaned_data.get('course_code'),
					student__student_id=self.cleaned_data.get('student_id'),
					semester__semester_name=self.cleaned_data.get('semester')
				).first()
				if not student_registration_object:
					return semester
				else:
					return semester
			elif program_object.program_type == 'certification':
				student_registration_object = StudentRegistration.objects.filter(
					course_code=self.cleaned_data.get('course_code'),
					student__student_id=self.cleaned_data.get('student_id'),
				).first()
				if not student_registration_object:
					return semester
				#setting semester name as '-' in case of certification in data base
				semester_object = Semester.objects.filter(id=1).first()
				return semester_object

	class Meta(object):
		model = OnlineExamAttendance
		fields = ('student_id', 'exam_type', 'semester', 'course_code', 'makeup_allowed',
				  'course_name', 'exam_date', 'total_questions', 'total_attempted', 'total_blank', 'image_uploaded',
				  'test_start_time', 'test_end_time', 'submission_type',
				  )

	def clean(self, *args, **kwargs):
		if any(self.errors): return
		from django.core.exceptions import ValidationError
		if self.cleaned_data.get('student_id') != "":
			student_object = Student.objects.filter(student_id=self.cleaned_data.get('student_id')).first()
			if not student_object:
				raise ValidationError("Student ID not found in Student table. Please make the student entry in the Student table first")

			program_object = Program.objects.filter(program_code=self.cleaned_data.get('student_id')[4:8]).first()
			if program_object.program_type == 'certification':
				student_registration_object = StudentRegistration.objects.filter(
					course_code=self.cleaned_data.get('course_code'),
					student__student_id=self.cleaned_data.get('student_id'),
				).first()
				#Checking for a entry in student registeration table for certification student ids
				if not student_registration_object:
					raise ValidationError("Student ID and Course Code not found in Student Registration table. Please make the entry in the Student Registration table first");
				if self.has_changed():
					#while updating the added entries
					if self.initial:
						#Semester is always comes in changed data so not considering it as data changed
						if len(self.changed_data) != 1:
							#If there is a change in student id or exam type or course code check for duplication entries
							exam_type_object = ExamType.objects.filter(id=self.initial.get('exam_type'))
							if self.initial.get('student_id') != self.cleaned_data.get('student_id') or\
							   str(exam_type_object[0].evaluation_type+' '+exam_type_object[0].exam_type) != str(self.cleaned_data.get('exam_type')) or \
							   self.initial.get('course_code') != self.cleaned_data.get('course_code'):
								if OnlineExamAttendance.objects.filter(student_id=self.cleaned_data.get('student_id'),
																	  exam_type=self.cleaned_data.get('exam_type'),
																	  course_code=self.cleaned_data.get('course_code')).first():
									raise ValidationError("Online exam attendance with this Student id, Exam type and Course code already exists")
					else:
						if OnlineExamAttendance.objects.filter(student_id=self.cleaned_data.get('student_id'),
															   exam_type=self.cleaned_data.get('exam_type'),
															   course_code=self.cleaned_data.get('course_code')).first():
								raise ValidationError("Online exam attendance with this Student id, Exam type and Course code already exists")
			else:
				student_registration_object = StudentRegistration.objects.filter(
					course_code=self.cleaned_data.get('course_code'),
					student__student_id=self.cleaned_data.get('student_id'),
					semester__semester_name=self.cleaned_data.get('semester')
				).first()
				# Checking for a entry in student registeration table for other student ids
				if not student_registration_object:
					raise ValidationError("Student ID, Course Code and Semester not found in Student Registration table. Please make the entry in the Student Registration table first");


		return super().clean(*args, **kwargs)



