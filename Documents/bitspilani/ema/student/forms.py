from django import forms
from master.models import *
from django.core.exceptions import *
from master.utils.extra_models.querysets import *
from master.forms.form_fields import *
from ema import default_settings as S
from django.db.models import Q, Sum, When, OuterRef, Subquery
from django.forms.models import BaseModelFormSet
import collections
import functools


def home_form(program, student):
	
	class HomeForm(forms.Form):
		semester = SemesterModelChoiceField(empty_label=None, 
			queryset=Semester.objects.filter(semester_name=S.SEMESTER_NAME),
			label="Choose the Semester or Batch (for certification students) and Click on the Button below",
			)

		def __init__(self, *args, **kwargs):
			super(). __init__(*args, **kwargs)
			self.fields['semester'].widget.attrs['class'] = 'form-control'
			

			if program.program_type == Program.NON_SPECIFIC:
				self.fields['semester'].queryset = Semester.objects.filter(
					Q(semester_name=S.SEMESTER_NAME)|Q(currentexam_sem__program=program, currentexam_sem__is_active=True, currentexam_sem__batch=student.batch)
					).distinct()

			elif program.program_type == Program.CERTIFICATION:
				self.fields['semester'].required = False

			elif program.program_type in [Program.SPECIFIC, Program.CLUSTER]:
				self.fields['semester'].queryset = Semester.objects.filter(
					Q(semester_name=S.SEMESTER_NAME)|Q(currentexam_sem__program=program, 
						currentexam_sem__is_active=True, currentexam_sem__batch=student.batch)
					).distinct()

		def clean_semester(self):
			semester = self.cleaned_data['semester']
			if program.program_type != Program.CERTIFICATION and semester.semester_name==S.SEMESTER_NAME:
				raise forms.ValidationError("Semester is mandatory", code='invalid')	
			return semester

	return HomeForm

# def get_hall_ticket_detail_form(exam_type, semester, program, stud_reg, student):
def get_hall_ticket_detail_form(semester, program, stud_reg, student, ce_details, ces_details):
# 	ce = CurrentExam.objects.filter(is_active=True, batch=student.batch,
# 		program=program, semester=semester, 
# 		# exam_type=exam_type,
# 	)
# # -----------code to check for reduce operator if ce record not present-----------
# 	if ce:
# 		ces = CourseExamShedule.objects.filter(
# 			functools.reduce(operator.or_,(
# 				Q(
# 					exam_type=q.exam_type, 
# 					batch=q.batch, 
# 					semester=q.semester
# 					) for q in ce.iterator()
# 				)
# 			),
# 			course_code__in=Subquery(stud_reg.values('course_code'))
# 		)
# 	else:
# 		ces = CourseExamShedule.objects.none()
#-----------------------------------------------------------------------------------------------------
	
	class HallTicketDetailForm(forms.ModelForm):
		course_code = forms.CharField(required=False, widget=forms.HiddenInput())
		course_name = forms.CharField(required=False, widget=forms.HiddenInput())
		exam_type = forms.ModelChoiceField(empty_label = 'Choose Exam Type', queryset = ExamType.objects.filter(pk__in=ce_details.values('exam_type')))
		exam_slot = ExamSlotChoiceField(empty_label='Choose Exam Slot', queryset=ExamSlot.objects.all())
		location = forms.ModelChoiceField(empty_label='Choose Exam Location', queryset=Location.objects.all(),)
		exam_venue = forms.ModelChoiceField(empty_label='Choose Exam Venue', queryset=ExamVenue.objects.all(),)

		def __init__(self, *args, **kwargs):
			super(HallTicketDetailForm, self).__init__(*args, **kwargs)

			self.fields['exam_type'].widget.attrs['class'] = 'form-control'
			self.fields['exam_slot'].widget.attrs['class'] = 'form-control'
			self.fields['location'].widget.attrs['class'] = 'form-control'
			self.fields['exam_venue'].widget.attrs['class'] = 'form-control'
			self.empty_permitted = False


			if self.initial:
				if 'exam_type' in self.initial:
					self.fields['exam_type'].initial = self.initial['exam_type']

					# self.fields['exam_slot'].queryset = ExamSlot.objects.filter(
					# Q(slot_name=S.EXAM_SLOT_NAME)|
					# Q(pk__in=Subquery(
					# 	ces_details.filter(course_code=self.initial['course_code'], 
					# 		exam_type = self.initial['exam_type'],
					# 		semester=semester).values('exam_slot')
					# 	)
					# )
					# )

					self.fields['exam_slot'].initial = self.initial['exam_slot']

					evsm = ExamVenueSlotMap.objects.filter(exam_slot=self.initial['exam_slot'], 
						exam_type=self.initial['exam_type'], 
						exam_venue__location=self.initial['location'])

					# self.fields['location'].queryset = Location.objects.filter(pk__in=evsm.values('exam_venue__location'))
					self.fields['location'].initial = self.initial['location']

					# self.fields['exam_venue'].queryset = ExamVenue.objects.filter(pk__in=evsm.values('exam_venue'))
					self.fields['exam_venue'].initial = self.initial['exam_venue']

		class Meta:
			model = HallTicket
			exclude = ('is_cancel','created_on','cancel_on',)
			widgets = {
				'student':forms.HiddenInput(),
				'semester':forms.HiddenInput(),
				'course':forms.HiddenInput(),
				# 'exam_type':forms.HiddenInput(),
				'exam_slot':forms.HiddenInput(),
				'exam_venue':forms.HiddenInput(),
			}

		def clean_exam_slot(self):
			exam_slot = self.cleaned_data['exam_slot']
			if exam_slot.slot_name==S.EXAM_SLOT_NAME:
				raise forms.ValidationError("Exam Slot is mandatory", code='invalid')
			return exam_slot

		def clean_exam_venue(self):
			if self.has_changed():
				evsm = get_instance_or_none(ExamVenueSlotMap,**{'exam_venue':self.cleaned_data["exam_venue"],
					'exam_slot':self.cleaned_data["exam_slot"],
					'exam_type':self.cleaned_data["exam_type"]})
				total_count=HallTicket.objects.filter(
									exam_type=self.cleaned_data["exam_type"],
									exam_slot=self.cleaned_data["exam_slot"],
									exam_venue=self.cleaned_data["exam_venue"],
									is_cancel=False).count()
				if evsm.student_count_limit <= total_count:
					raise forms.ValidationError("You have chosen a venue that has no seating capacity left. Please choose a different Exam Venue", code='invalid')
			return self.cleaned_data["exam_venue"]


	return HallTicketDetailForm

def get_hall_ticket_location_form(exam_type, exam_slot, location_id, exam_venue_id, student_id=None, semester=None):
	if exam_slot:
		evsm = ExamVenueSlotMap.objects.filter(exam_slot=exam_slot, exam_type=exam_type,)
		location_queryset = Location.objects.filter(pk__in=evsm.values('exam_venue__location'))
		exam_venue_lock = ExamVenueLock.objects.filter(student_id=student_id, semester_id=semester, lock_flag=1)
		if exam_venue_lock:
			location_queryset = location_queryset.filter(pk__in=exam_venue_lock.values('exam_venue_id__location'))
	else:
		location_queryset = Location.objects.none()

	class LocationForm(forms.Form):
		location = forms.ModelChoiceField(empty_label='Choose Exam Location', 
			queryset=location_queryset, widget=forms.Select(attrs={'id':location_id})
			)
		exam_venue = forms.ModelChoiceField(empty_label='Choose Exam Venue', 
			queryset=ExamVenue.objects.none(), widget=forms.Select(attrs={'id':exam_venue_id})
			)

	return LocationForm

def get_hall_ticket_exam_venue_form(exam_type, exam_slot, location, exam_venue_id, student_id=None, semester=None):
	if location:
		evsm = ExamVenueSlotMap.objects.filter(exam_venue__location=location, exam_type=exam_type, exam_slot=exam_slot)
		exam_venue_queryset = ExamVenue.objects.filter(pk__in=evsm.values('exam_venue'))
		exam_venue_lock = ExamVenueLock.objects.filter(student_id=student_id, semester_id=semester, lock_flag=1).values_list('exam_venue', flat=True)
		if exam_venue_lock:
			exam_venue_queryset = exam_venue_queryset.filter(pk__in=exam_venue_lock)
	else:
		exam_venue_queryset = ExamVenue.objects.none()

	class ExamVenueForm(forms.Form):
		exam_venue = forms.ModelChoiceField(empty_label='Choose Exam Venue', 
			queryset=exam_venue_queryset, widget=forms.Select(attrs={'id':exam_venue_id})
			)

	return ExamVenueForm

def get_hall_ticket_exam_slot_form(exam_type, exam_slot_id, semester, course_code, course_id, student_id=None):
	if exam_type:
		ces_detail = CourseExamShedule.objects.filter(
			exam_type = exam_type,
			semester = semester,
			course_code = course_code
			)
		
		if student_id:
			stu_batch_name = Student.objects.filter(student_id=student_id).values_list('batch__batch_name',flat=True)
			if '-' not in stu_batch_name:
				ces_detail = ces_detail.filter(batch__batch_name=stu_batch_name[0])
			else:
				ces_detail = ces_detail.filter(batch__batch_name='-')

		exam_slot_queryset = ExamSlot.objects.filter(pk__in=ces_detail.values('exam_slot'))
		exam_venue_lock = ExamVenueLock.objects.filter(student_id=student_id, semester_id=semester, lock_flag=1).values_list('exam_venue', flat=True)
		if exam_venue_lock:
			evsm_lock_exam_slots = ExamVenueSlotMap.objects.filter(exam_venue__in=exam_venue_lock).values_list('exam_slot', flat=True)
			exam_slot_queryset = exam_slot_queryset.filter(pk__in=evsm_lock_exam_slots)
	else:
		exam_slot_queryset = ExamSlot.objects.none()
		ces_detail = CourseExamShedule.objects.none()

	class ExamSlotForm(forms.Form):
		exam_slot = forms.ModelChoiceField(empty_label='Choose Exam Slot', 
			queryset=exam_slot_queryset, widget=forms.Select(attrs={'id':exam_slot_id})
			)
		course = forms.ModelChoiceField(empty_label=None, 
			queryset=ces_detail, widget=forms.Select(attrs={'id':course_id})
			)

	return ExamSlotForm


class HallTicketDetailFormSet(BaseModelFormSet):

	def __iter__(self):
		
		data_form_list = []
		empty_form_list = []

		for i in self.forms:
			if i['exam_slot'].value() != None:

				data_form_list.append(i)

			else:
				empty_form_list.append(i)
		try:
			final_list = sorted(data_form_list, key=lambda form: (ExamSlot.objects.filter(id=form['exam_slot'].value())[0].slot_date, ExamSlot.objects.filter(id=form['exam_slot'].value())[0].slot_start_time, ExamSlot.objects.annotate(
									custom_order=Case(
									When(Q(slot_name__contains="FN") | Q(slot_name__contains="FORENOON"), then=Value('A')),
									When(Q(slot_name__contains="AN") | Q(slot_name__contains="AFTERNOON"), then=Value('B')),
									output_field=CharField(),
									)
									   ).filter(id=form['exam_slot'].value())[0].custom_order))

			data = final_list+empty_form_list
		except:
			data = self.forms

		return iter(data)

	def __getitem__(self, index):
		
		return list(self)[index]


	def clean(self):
		if any(self.errors):return
		super().clean()
		exam_slot = collections.Counter([ form.cleaned_data['exam_slot'].pk for form in self.forms if (form.is_valid() and form.cleaned_data)])

		if any(map(lambda x: x>1, exam_slot.values())):
			raise forms.ValidationError(
				'Same exam slot chosen for two different courses. Please choose different slots for differnt courses',
				code='invalid'
				)


	class Meta:
		model = HallTicket
		exclude = ('is_cancel','created_on','cancel_on',)


class PhotoEditForm(forms.Form):
	x = forms.FloatField(required=False, widget=forms.HiddenInput())
	y = forms.FloatField(required=False, widget=forms.HiddenInput())
	width = forms.FloatField(required=False, widget=forms.HiddenInput())
	height = forms.FloatField(required=False, widget=forms.HiddenInput())
	rotate = forms.FloatField(required=False, widget=forms.HiddenInput())
