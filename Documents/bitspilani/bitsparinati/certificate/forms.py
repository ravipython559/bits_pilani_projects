from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from registrations.models import *
from djangoformsetjs.utils import formset_media_js
from phonenumber_field.widgets import PhoneNumberPrefixWidget,PhoneNumberInternationalFallbackWidget
from bits_admin.forms import DobForm as DF

class DobForm(DF):pass

def studentApplication(pg_code=None, login_email=None):

	pg=Program.objects.get(program_code=pg_code)

	def showExamLocationChoice1(pg):
		exam = [(None,'-- Choose Exam location --')]
		exam += [(x.id,x.location_name)for x in pg.available_in_cities.all()]
		return  exam

	def showExamLocationChoice():
		exam = [(None,'Choose Location')]
		exam += [(x.id,x.location_name)for x in Location.objects.filter(is_exam_location=True)]
		return  exam

	class StudentForm(forms.ModelForm):

		date_of_birth = forms.DateField(widget=forms.DateInput(
			attrs={'format':'%d-%m-%Y','class': 'datepicker'}),
			input_formats=('%Y-%m-%d','%d-%m-%Y','%d/%m/%Y','%Y/%m/%d'))
		phone = forms.CharField(widget=PhoneNumberPrefixWidget(),required=False)
		mobile = forms.CharField(widget=PhoneNumberPrefixWidget(),required=False)
		current_location = forms.ChoiceField(choices=showExamLocationChoice1(pg))
		exam_location = forms.CharField(required=False,widget=forms.HiddenInput())
		math_proficiency_level = forms.CharField(required=False,widget=forms.HiddenInput(
			attrs={'value':'N/A'}))
		parallel_studies_flag = forms.CharField(required=False,widget=forms.HiddenInput(
			attrs={'value':'N/A'}))
		email_id = forms.EmailField(required=True, widget=forms.TextInput(
			attrs={'value':login_email}) )

		total_work_experience_in_months = forms.CharField(required=True, 
			widget=forms.TextInput(
				attrs={
				'pattern':'^\d+(\.(\d|0\d|1(0|1)))?$',
				'value':'0.0',
				}
				))

		program = forms.CharField(widget=forms.HiddenInput(attrs={'value':pg.id}))
		program_display = forms.CharField(widget=forms.TextInput(attrs={
			'value':pg.program_name,
			'readonly':'true'}
			))

		def fee_payment_owner_choice(self):
			choice = [(x,y)for x,y in FEEPAYMENT_CHOICES if x != '4' ]
			return  choice

		def emp_status_choice(self):
			choice = [(x,y)for x,y in EMPLOYMENTSTATUS_CHOICES if x != '4' ]
			return  choice

		def clean_current_location(self):
			if not self.cleaned_data['current_location']:
				raise forms.ValidationError('error in current location')
			return Location.objects.get(id=int(self.cleaned_data['current_location']))

		def clean_program(self):
			if not self.cleaned_data['program']:
				raise forms.ValidationError('error in program')
			return Program.objects.get(id=int(self.cleaned_data['program']))

		def __init__(self, *args, **kwargs):
			super(StudentForm, self).__init__(*args, **kwargs)
			self.fields['current_location'] = forms.ChoiceField(choices=showExamLocationChoice1(pg))
			self.fields['fee_payment_owner'] = forms.ChoiceField(choices=self.fee_payment_owner_choice())
			self.fields['current_employment_status'] = forms.ChoiceField(choices=self.emp_status_choice())
			self.fields['programming_flag'].widget=forms.RadioSelect()
			programming_flag_widget = self.fields['programming_flag'].widget
			self.fields['programming_flag'].widget = forms.HiddenInput()
			self.fields['programming_flag'].label = ''

			programming_flag_selected_attributes = FormFieldPopulationSpecific.objects.filter(
					program=pg,
					show_on_form=True,
					field_name='programming_flag',
				)

			if programming_flag_selected_attributes.exists():
				self.fields['programming_flag'].widget = programming_flag_widget
				self.fields['programming_flag'].label = 'Do you have working knowledge of ANY programming language'
				self.fields['programming_flag'].choices = StudentCandidateApplication.PROGRAMMING_FLAG_CHOICES					

			

		class Meta(object):
			"""Student Candidate model form meta class."""

			model = StudentCandidateApplication
			exclude = ('application_status', 'admit_year', 'created_on_datetime',
					   'last_updated_on_datetime','employer_consent_flag',
					   'employer_mentor_flag','current_org_employee_number','login_email',
					   'current_org_employment_date', )

	return StudentForm


def StudentEducation(pg_code=None):
	class EducationForm(forms.ModelForm):
		other_degree = forms.CharField(required=False,widget=forms.HiddenInput())
		other_discipline = forms.CharField(required=False,widget=forms.HiddenInput())
		degree = forms.ModelChoiceField(
			widget=forms.Select,
			queryset=Degree.objects.filter(
				qualification_category__category_name__iexact='Graduation or equivalent'
				),
			required=True)

		class Meta(object):

			model = StudentCandidateQualification
			exclude = ('application',)

		class Media(object):
			"""Education model form media class."""
			js = formset_media_js

	return EducationForm