from django import forms
from functools import partial
from registrations.models import *
from bits_admin.models import StudentCandidateApplicationArchived,ProgramArchived
from bits_rest import zest_statuses as ZS
from django.conf import settings
from datetimewidget.widgets import DateTimeWidget
from django.core.exceptions import ValidationError
from datetime import datetime
from bits_rest.models import EduvanzApplication
import re
from registrations.extra_forms import get_sca_admit_batch_choices

DateInput = partial(forms.DateInput, {'class': 'datepicker'})

class ToAndFromDate(forms.Form):

	def showStatusChoice():

		st = [(None,'Choose Status')]
		status = [(x[0],x[0]) for x in settings.APP_STATUS]
		status.sort()
		st.extend(status)
		return  st

	BANK = [(None,'Choose Bank'),('PAYTM','Paytm'),('EDUVANZ','Eduvanz'),('TPSL','TPSL'),('ZEST','Zest'),('PROPELLD', 'Propelld'),('EZCRED','Ezcred'),]

	from_date = forms.DateField(widget=DateInput(format = '%d-%m-%Y'),input_formats=('%d-%m-%Y',))
	to_date = forms.DateField(widget=DateInput(format = '%d-%m-%Y'),input_formats=('%d-%m-%Y',))
	programs = forms.ModelChoiceField(
		widget=forms.Select,
		empty_label='Choose Program',
		queryset=Program.objects.none(),
		required=False)
	status = forms.ChoiceField(choices=showStatusChoice(), required=False)
	pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)
	bank_type = forms.ChoiceField(choices=BANK,required=False,widget=forms.Select(attrs={'style':'width:75%'}),)
	def __init__(self, *args, **kwargs):
		super(ToAndFromDate, self).__init__(*args, **kwargs)
		self.fields['admit_batch'] = forms.ChoiceField(choices=[(None,'Choose Admit Batch')] + [
				(x,x) for x in StudentCandidateApplication.objects.values_list('admit_batch', 
				flat=True).distinct().order_by('admit_batch') if x is not None and x != ''],
				required=False,)

def filter_form(data = None):
	form = ToAndFromDate(data)
	pg_type = data.get('pg_type')
	queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.none()
	form.fields['programs'].queryset = queryset
	return form

def filter_form_arch(data = None):
	form = ToAndFromDateArch(data)
	pg_type = data.get('pg_type')
	queryset = ProgramArchived.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else ProgramArchived.objects.none()
	form.fields['programs'].queryset = queryset
	return form

class ToAndFromDateArch(ToAndFromDate):
	programs = forms.ModelChoiceField(
		widget=forms.Select,
		empty_label='Choose Program',
		queryset=ProgramArchived.objects.none(),
		required=False)
	def __init__(self, *args, **kwargs):
		super(ToAndFromDateArch, self).__init__(*args, **kwargs)
		self.fields['admit_batch'] = forms.ChoiceField(choices=[(None,'Choose Admit Batch')] + [
				(x,x) for x in StudentCandidateApplicationArchived.objects.values_list('admit_batch', 
				flat=True).distinct().order_by('admit_batch') if x is not None and x != ''],
				required=False,)
		

class ZipProgram(forms.Form):
	program = forms.ModelChoiceField(
			widget=forms.Select(attrs={'required':'true','oninvalid':'setCustomValidity("Please Choose Program ")','onchange':'setCustomValidity("")'}),
			queryset=Program.objects.all().order_by('program_code'),
			required=True,empty_label='Choose Program')

class StatusReportForm(forms.Form):
	from_date = forms.DateTimeField(required = False,
		widget = DateTimeWidget(
			usel10n = True,
			bootstrap_version=3)
		)
	to_date = forms.DateTimeField(required = False,
		widget = DateTimeWidget(
			usel10n = True,
			bootstrap_version=3)
		)


class ArchiveForm(forms.Form):

	def __init__(self, *args, **kwargs):
		super(ArchiveForm, self).__init__(*args, **kwargs)
		self.fields['admit_batch'] = forms.ChoiceField(choices=[(None,'Choose Admit Batch')] + [
				(x,x) for x in StudentCandidateApplication.objects.values_list('admit_batch', 
				flat=True).distinct().order_by('admit_batch') if x is not None and x != ''],
				required=False,)

	from_date = forms.DateField(
		widget=DateInput(format = '%d-%m-%Y'),
		input_formats=('%d-%m-%Y',),
		required=False)

	to_date = forms.DateField(
		widget=DateInput(format = '%d-%m-%Y'),
		input_formats=('%d-%m-%Y',),
		required=False)
	
	programs = forms.ModelMultipleChoiceField(
		queryset=Program.objects.filter(active_for_applicaton_flag=False).order_by('program_code'),
		required=False
		)

	

	def clean(self):
		if any(self.errors):return
		if not Program.objects.filter(active_for_applicaton_flag=False).exists():
			raise ValidationError('there are no program to choose')

		from_date = self.cleaned_data.get('from_date',None)
		to_date = self.cleaned_data.get('to_date',None)
		programs = self.cleaned_data['programs']
		admit_batch = self.cleaned_data.get('admit_batch', None)

		if not programs.exists() and not from_date and not to_date and not admit_batch:
			raise ValidationError('Choose either or all of the inputs')
		sca = StudentCandidateApplication.objects.filter(
				program__active_for_applicaton_flag = False
				)

		if from_date: sca = sca.filter( 
			created_on_datetime__gte = datetime(
				from_date.year,from_date.month,from_date.day,00,00,00
				)
			)
		if to_date: sca = sca.filter( 
			created_on_datetime__lte = datetime(
				to_date.year,to_date.month,to_date.day,23,59,59
				) 
			)
		if programs: sca = sca.filter( program__in = programs )

		if admit_batch: sca = sca.filter(admit_batch = admit_batch)

		if not sca.exists():
			raise ValidationError('No applications found for archival')

def Ncl_Form(data=None):

	class NclForm(forms.Form):

		programs = forms.ModelChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}),
			queryset=Program.objects.all(),
			required=False,
			empty_label='Choose Program')

		admit_batchs = forms.ChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}),
			choices=[(None,'Choose Admit Batch'),],
			required=False, )

		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

		def __init__(self, *args, **kwargs):
			super(NclForm, self).__init__(*args, **kwargs)
			self.fields['admit_batchs'].choices = get_sca_admit_batch_choices()
			pg_type = data.get('pg_type')
			queryset = Program.objects.filter(program_type = pg_type) if pg_type else Program.objects.none()
			self.fields['programs'].queryset = queryset
	return NclForm(data)


class NameChangeForm(forms.ModelForm):

	def __init__(self,*args,**kwargs):
		super(NameChangeForm, self).__init__(*args,**kwargs)
		cs = self.instance
		self.fields['verified_student_name'].widget =forms.TextInput(attrs={
			'value': cs.verified_student_name if cs.verified_student_name else cs.application.full_name,'size':'38',
			})

	def clean_verified_student_name(self):
		name = self.cleaned_data.get('verified_student_name',None)

		if not name:
			raise forms.ValidationError('This field is required.')

		for x in name.split():
			if not re.match("^\D+$",x.strip()):
				raise forms.ValidationError('Please enter a valid name.')

		return ' '.join(name.split()).upper()
		

	class Meta:
		model = CandidateSelection
		fields = ('verified_student_name',)


class FollowupMailForm(forms.Form):

	from_date = forms.DateField(
		widget=DateInput(format = '%d-%m-%Y'),
		input_formats=('%d-%m-%Y',),
		required=False)

	to_date = forms.DateField(
		widget=DateInput(format = '%d-%m-%Y'),
		input_formats=('%d-%m-%Y',),
		required=False)

class DobForm(forms.ModelForm):
	date_of_birth = forms.DateField(widget=DateInput(format='%d-%m-%Y'),
		input_formats=('%d-%m-%Y',),required=True)

	class Meta:
		model = StudentCandidateApplication
		fields = ('date_of_birth',)

def def_filter_form(data = None):
	class ProgramAndStatusForm(forms.Form):
		def showStatusChoice():
			st = [(None,'Choose Status')]
			status = [(x[0],x[0]) for x in list(settings.APP_STATUS[0:7]) + [settings.APP_STATUS[9]] + [settings.APP_STATUS[11]] + list(settings.APP_STATUS[15:])]
			status.sort()
			st.extend(status)
			return  st

		programs = forms.ModelChoiceField(
			widget=forms.Select,
			empty_label='Choose Program',
			queryset=Program.objects.all().order_by('program_code'),
			required=False)
		status = forms.ChoiceField(choices=showStatusChoice(), required=False)

		def __init__(self, *args, **kwargs):
			super(ProgramAndStatusForm, self).__init__(*args, **kwargs)
			self.fields['admit_batch'] = forms.ChoiceField(choices=[(None,'Choose Admit Batch')] + [
					(x,x) for x in StudentCandidateApplication.objects.values_list('admit_batch', 
					flat=True).distinct().order_by('admit_batch') if x is not None and x != ''],
					required=False,)

	return ProgramAndStatusForm(data)


def emi_filter_form(data = None):
	class ProgramAndStatusForm(forms.Form):
		programs = forms.ModelChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}),
			empty_label='Choose Program',
			queryset=Program.objects.none(),
			required=False)
		
		status = forms.ChoiceField(choices=ZS.ZEST_DISPLAY_STATUS_CHOICES, required=False)

		admit_batch = forms.ChoiceField(
		widget=forms.Select(attrs={'style':'width:45%'}),
		choices=[(None,'Choose Admit Batch'),],
		required=False, )

		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

		def __init__(self, *args, **kwargs):
			super(ProgramAndStatusForm, self).__init__(*args, **kwargs)
			self.fields['admit_batch'].choices = get_sca_admit_batch_choices()
			pg_type = data.get('pg_type')
			queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.none()
			self.fields['programs'].queryset = queryset

	return ProgramAndStatusForm(data)


def program_filter_form(data = None):
	class ProgramForm(forms.Form):
		programs = forms.ModelChoiceField(
				widget=forms.Select,
				queryset=Program.objects.filter(
					firstsemcourselist_requests_created_1__active_flag=True,
					firstsemcourselist_requests_created_1__is_elective=True
					).order_by('program_code').distinct(),
				required=False,empty_label='Choose Program')

	return ProgramForm(data)

def pre_sel_rej_filter_form(data = None):
	class ProgramAndLocForm(forms.Form):
		programs = forms.ModelChoiceField(
			widget=forms.Select,
			empty_label='Select Program',
			queryset=Program.objects.filter(enable_pre_selection_flag = True).order_by('program_code'),
			required=False)

		location = forms.ModelChoiceField(
			widget=forms.Select,
			empty_label='Select Location',
			queryset=Location.objects.all(),
			required=False)

	return ProgramAndLocForm(data)

def call_log_form(data = None):
	class CallLogDateFilterForm(forms.Form):
		from_date = forms.DateField(label='From', widget=forms.DateInput(attrs={
				'format':'%d-%m-%Y','class': 'datepicker'
			}),
			input_formats=('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'), required=False)

		to_date = forms.DateField(label='To', widget=forms.DateInput(attrs={
				'format':'%d-%m-%Y','class': 'datepicker'
			}),
			input_formats=('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'), required=False)

	return CallLogDateFilterForm(data)


def eduv_emi_filter_form(data = None):

	class ProgramAndStatusForm(forms.Form):
		programs = forms.ModelChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}),
			empty_label='Choose Program',
			queryset=Program.objects.none(),
			required=False)
		
		status = forms.ChoiceField(choices=EduvanzApplication.EDUVANZ_CHOICES, required=False)

		admit_batch = forms.ChoiceField(
		widget=forms.Select(attrs={'style':'width:45%'}),
		choices=[(None,'Choose Admit Batch'),],
		required=False, )

		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

		def __init__(self, *args, **kwargs):
			super(ProgramAndStatusForm, self).__init__(*args, **kwargs)
			self.fields['admit_batch'].choices = get_sca_admit_batch_choices()
			if data.get('programs'):
				self.fields['programs'].queryset = Program.objects.all().order_by('program_code')
				self.fields['programs'].initial =  data.get('programs')
			else:	
				pg_type = data.get('pg_type')
				queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.all()
				self.fields['programs'].queryset = queryset


	return ProgramAndStatusForm(data)
	# class ProgramAndStatusForm(forms.Form):
	# 	programs = forms.ModelChoiceField(
	# 		widget=forms.Select,
	# 		empty_label='Choose Program',
	# 		queryset=Program.objects.all().order_by('program_code'),
	# 		required=False)
	# 	status = forms.ChoiceField(choices=EduvanzApplication.EDUVANZ_CHOICES, required=False)

	# 	admit_batch = forms.ChoiceField(
	# 	widget=forms.Select(attrs={'style':'width:45%'}),
	# 	choices=[(None,'Choose Admit Batch'),],
	# 	required=False, )

	# 	pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

	# 	def __init__(self, *args, **kwargs):
	# 		super(ProgramAndStatusForm, self).__init__(*args, **kwargs)
	# 		self.fields['admit_batch'].choices = get_sca_admit_batch_choices()
	# 		pg_type = data.get('pg_type')
	# 		queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.none()
	# 		self.fields['programs'].queryset = queryset

	# return ProgramAndStatusForm(data)

def ezcred_filter_form(data = None):
	class ProgramAndStatusForm(forms.Form):
		programs = forms.ModelChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}),
			empty_label='Choose Program',
			queryset=Program.objects.none(),
			required=False)
		
		status = forms.ChoiceField(choices=ZS.EZCRED_DISPLAY_STATUS_CHOICES, required=False)

		admit_batch = forms.ChoiceField(
		widget=forms.Select(attrs={'style':'width:45%'}),
		choices=[(None,'Choose Admit Batch'),],
		required=False, )

		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

		def __init__(self, *args, **kwargs):
			super(ProgramAndStatusForm, self).__init__(*args, **kwargs)
			self.fields['admit_batch'].choices = get_sca_admit_batch_choices()
			pg_type = data.get('pg_type')
			queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.none()
			self.fields['programs'].queryset = queryset

	return ProgramAndStatusForm(data)


def propelld_filter_form(data = None):
	class ProgramAndStatusForm(forms.Form):
		programs = forms.ModelChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}),
			empty_label='Choose Program',
			queryset=Program.objects.none(),
			required=False)
		
		status = forms.ChoiceField(choices=ZS.PROPELLD_DISPLAY_STATUS_CHOICES, required=False)

		admit_batch = forms.ChoiceField(
		widget=forms.Select(attrs={'style':'width:45%'}),
		choices=[(None,'Choose Admit Batch'),],
		required=False, )

		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

		def __init__(self, *args, **kwargs):
			super(ProgramAndStatusForm, self).__init__(*args, **kwargs)
			self.fields['admit_batch'].choices = get_sca_admit_batch_choices()
			pg_type = data.get('pg_type')
			queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.none()
			self.fields['programs'].queryset = queryset

	return ProgramAndStatusForm(data)