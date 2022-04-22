from django import forms
from django.contrib.auth.models import User
from .models import *
from django.core.urlresolvers import reverse_lazy
from bits_admin.models import StudentCandidateApplicationArchived,ExceptionListOrgApplicantsArchived
from django.conf import settings
from django.db.models import Q
from phonenumber_field.widgets import (PhoneNumberPrefixWidget,
	PhoneNumberInternationalFallbackWidget)
from django.template.loader import render_to_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from import_export import resources, fields as i_e_fields, widgets as widg
import dns.resolver, dns.exception
import phonenumbers
from datetime import datetime as dt
import re
from validate_email import validate_email as v_e
from dateutil.tz import gettz
from dateutil.parser import parse
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from .resources_widgets import *
import cPickle
from itertools import chain


class FileURLWidget(forms.Widget):
	def render(self, name, value, attrs=None):
		display_text = 'Doc Link'
		html_tag = '<a{}>{}</a>'
		if value is None: 
			value = '#'
			html_tag = '<span{}>{}</span>'
			display_text = 'To Be Submitted'
		final_attrs = self.build_attrs(attrs, name=name, 
			href=value, target='_blank')
		return format_html(html_tag, flatatt(final_attrs), force_text(display_text))

class PlainTextWidget(forms.Widget):
	def render(self, name, value, attrs=None):
		if value is None:
			value = '-'
		final_attrs = self.build_attrs(attrs, name=name)
		return format_html('<span{}>{}</span>',
					flatatt(final_attrs),
					force_text(value))

class ExtraForm(forms.Form):

	programs = forms.ModelChoiceField(
		widget=forms.Select(attrs={'style':'width:70%'}),
		queryset=Program.objects.all().order_by('program_code'),
		required=False,
		empty_label='Choose Program')
	locations = forms.ModelChoiceField(
		widget=forms.Select(attrs={'style':'width:70%'}),
		queryset=Location.objects.all(),
		required=False,
		empty_label='Choose Location')
	admit_batch = forms.ChoiceField(choices=[(None,'Choose Admit Batch')] + [
				(x,x) for x in StudentCandidateApplication.objects.values_list('admit_batch', 
				flat=True).distinct().order_by('admit_batch') if x is not None and x != ''],
				required=False,)
	hidden_id = forms.CharField(max_length=1024, required=False,
		widget=forms.HiddenInput())
	page = forms.IntegerField(widget=forms.HiddenInput(),required=False)
	search = forms.CharField(widget=forms.HiddenInput(),required=False)

class ShortRejForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(ShortRejForm, self).__init__(*args, **kwargs)
		self.fields['application'].widget = forms.HiddenInput()

	class Meta(object):
		model = CandidateSelection
		fields = ('es_to_su_rev','application')


class EscCommentForm(forms.Form):
	es_comments = forms.CharField(label='Escalation to Super Reviewer Comments', 
		widget=forms.Textarea(attrs={'cols': 50, 'rows': 2,'required':'true'}))


class ProgramRejEscForm(forms.Form):

	program = forms.CharField(max_length=254, required=False,
							   widget=forms.HiddenInput())
	app_id = forms.CharField(max_length=254, required=False,
							   widget=forms.HiddenInput())

class ProgramsAndLocationAndSearch(forms.Form):

	programs = forms.ModelChoiceField(
		widget=forms.Select,
		queryset=Program.objects.all(),
		required=False,
		)
	locations = forms.ModelChoiceField(
		widget=forms.Select,
		queryset=Location.objects.all(),
		required=False)
	search = forms.CharField(max_length=254, required=False,
							   widget=forms.HiddenInput())


class ProgramStatusForm(forms.Form):
	def showStatusChoice():
		status = [(None,'Choose Status'),
		(settings.APP_STATUS[2][0],settings.APP_STATUS[2][0]),
		(settings.APP_STATUS[3][0],settings.APP_STATUS[3][0]),
		(settings.APP_STATUS[4][0],settings.APP_STATUS[4][0])]
		status.sort()
		return status

	programs = forms.ModelChoiceField(
		widget=forms.Select(attrs={'style':'width:70%'}),
		empty_label='Choose Program',
		queryset=Program.objects.all().order_by('program_code'),
		required=False)
	status = forms.ChoiceField(choices=showStatusChoice(), 
		widget=forms.Select(attrs={'style':'width:70%'}),
		required=False)

class ProgramRejForm(forms.ModelForm):
	es_to_su_rev = forms.BooleanField(required=False)
	program = forms.ModelChoiceField(
		widget=forms.Select(attrs={'style':'width:70%'}),
		queryset=Program.objects.filter(active_for_admission_flag = True),
		required=False,
		empty_label='Choose Program',
		)

	class Meta(object):
		model = StudentCandidateApplication
		fields = ('es_to_su_rev','program')


	def __init__(self,*args,**kwargs):
		super(ProgramRejForm, self).__init__(*args, **kwargs)
		tmp = self.fields['program'].queryset
		self.fields['program'].queryset = tmp.exclude(
			program_code = kwargs['instance'].program.program_code
			)

class FTField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name].strip() 
		if not filter(lambda x:x[1]==value,FEE_TYPE_CHOICES):
			raise ValidationError('fee type dint match') 

		return value

class PField(i_e_fields.Field):
	def clean(self, data):
		value = str(data[self.column_name]).strip()
		if not value:
			raise ValidationError('{0} is empty'.format(data[self.column_name])) 

		return value

class DField(PField):
	def clean(self, data):
		value = super(DField,self).clean(data)
		try :
			return dt.strptime(value, "%Y-%B-%dT%H:%M:%S-%H:%M").date()
		except :
			raise ValidationError('{0} format mis-match'.format(data[self.column_name]))

class ApplicationPaymentForm(resources.ModelResource):
	application = i_e_fields.Field(column_name='application',attribute='application',
		widget=widg.ForeignKeyWidget(StudentCandidateApplication,'student_application_id'))
	program = i_e_fields.Field(column_name='program',
		# attribute='program',
		widget=widg.ForeignKeyWidget(Program,'program_code'))
	fee_type = FTField(column_name='fee_type',attribute='fee_type')
	payment_id = PField(column_name='payment_id',attribute='payment_id')
	payment_date = DField(column_name='payment_date',attribute='payment_date')
	payment_bank = PField(column_name='payment_bank',attribute='payment_bank')
	payment_amount = PField(column_name='payment_amount',attribute='payment_amount')
	transaction_id = PField(column_name='transaction_id',attribute='transaction_id')
	admit_year = PField(column_name='admit_year')

	class Meta(object):
		models = ApplicationPayment
		import_id_fields = ('application','fee_type')

	def before_import(self,dataset,dry_run, **kwargs):
		for data in dataset.dict:
			try:
				sca = StudentCandidateApplication.objects.get(
					student_application_id=data['student_application_id']
					)
				ap = ApplicationPayment.objects.get(
					application = sca, fee_type = data['fee_type']
					)

				if not sca.program == data['program'] :
					raise ValidationError('program mismatch'.format(
					data['student_application_id'])
					)
				fees = PROGRAM_FEES_ADMISSION.objects.get(
					admit_year,
					program = sca.program,
					latest_fee_amount_flag = True,
					fee_type = data['fee_type'],
					)

			except StudentCandidateApplication.DoesNotExist as e:
				raise ValidationError('{0}'.format(
					data['student_application_id'])
				)

			except ApplicationPayment.DoesNotExist as e:pass 
			else:
				raise ValidationError(
					'fees payment {0},{1}'.format(
						data['student_application_id'],data['fee_type']
						)
					)

		return super(ApplicationPaymentForm,self).before_import(dataset,dry_run, **kwargs)


#Name Verification Requirement begins...
def Ncl_Form(data=None):

	class NclForm(forms.Form):

		programs = forms.ModelChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}),
			queryset=Program.objects.all(),
			required=False,
			empty_label='Choose Program')

		admit_batch = forms.ChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}),
			choices=[(None,'Choose Admit Batch'),],
			required=False, )

		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

		def __init__(self, *args, **kwargs):
			super(NclForm, self).__init__(*args, **kwargs)
			self.fields['admit_batch'].choices = get_sca_admit_batch_choices()
			pg_type = data.get('pg_type')
			queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.none()
			self.fields['programs'].queryset = queryset
	return NclForm(data)

class NameChangeForm(forms.ModelForm):

	def __init__(self,*args,**kwargs):
		super(NameChangeForm, self).__init__(*args,**kwargs)
		cs = self.instance
		self.fields['verified_student_name'].widget =forms.TextInput(attrs={
			'value': cs.verified_student_name if cs.verified_student_name else cs.application.full_name,
			'size':'38',
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


#Name Verification Requirement ends...

class EEField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name].strip()
		try:
			validate_email( value.strip() )
			if len(value.strip())>50:
				raise ValidationError('Email string length more than 50')
		except ValidationError as e:
			raise ValidationError('Email type error')
		return value

class PField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name].strip()
		try:
			pg = Program.objects.get(program_code = str(value))
		except Program.DoesNotExist as e:
			raise ValidationError('{}'.format(e))
		else :
			if not pg.program_type == 'specific':
				raise ValidationError('program is not specific')
		return pg

class ProgramDomainMappingResource(resources.ModelResource):
	program = PField(column_name='program',attribute='program',
		widget=widg.ForeignKeyWidget(Program,'program_code'))
	email = EEField(column_name='email', attribute='email',)

	class Meta(object):
		model = ProgramDomainMapping
		fields = ('program','email')
		export_order = fields
		import_id_fields = ('program','email')

class ApplicantExceptionsResource(resources.ModelResource):

	class OFLField(i_e_fields.Field):
		def clean(self, data):
			off_letter = data[self.column_name].strip()
			if not off_letter:return None
			
			for k,v in OFFER_LETTER_TEMPLATE_CHOICES:
				if v.lower() == off_letter.lower():
					return k
			else:
				raise ValidationError("Invalid offer letter name.")

	class OField(i_e_fields.Field):
		def clean(self, data):
			value = data[self.column_name].strip()
			if not value: return None
			try:
				org = CollaboratingOrganization.objects.get(org_name = str(value))
			except CollaboratingOrganization.DoesNotExist as e:
				raise ValidationError('{}'.format(e))
			return org

	class PField(i_e_fields.Field):
		def clean(self, data):
			value = data[self.column_name].strip()
			try:
				pg = Program.objects.get(program_code = str(value))
			except Program.DoesNotExist as e:
				raise ValidationError('{}'.format(e))
			return pg

	class TField(i_e_fields.Field):
		def clean(self, data):
			value = data[self.column_name].strip()
			if not value: return None
			try:
				pg = Program.objects.get(program_code = str(value))
			except Program.DoesNotExist as e:
				raise ValidationError('{}'.format(e))
			return pg

	class FlagField(i_e_fields.Field):
		def clean(self, data):
			flag_list = { 'true':True, 'false':False, 0:False, 1:True, '0':False, '1':True ,'':False}
			flag_value = data[self.column_name].strip().lower()
			if not flag_value in flag_list:
				raise ValidationError("Invalid flag value.")
			return flag_list[flag_value]
			
	applicant_email = EEField(column_name='applicant_email', attribute='applicant_email')
	program = PField(column_name='program_id',attribute='program',
		widget=widg.ForeignKeyWidget(Program,'program_code'))
	org = OField(column_name='org_name', attribute='org',
		widget=widg.ForeignKeyWidget(CollaboratingOrganization,'org_name'))
	offer_letter = OFLField(column_name='offer_letter_name', attribute='offer_letter')
	work_ex_waiver = FlagField(column_name='work_ex_waiver', attribute='work_ex_waiver')
	employment_waiver = FlagField(column_name='employment_waiver', attribute='employment_waiver')
	hr_contact_waiver = FlagField(column_name='hr_contact_waiver', attribute='hr_contact_waiver')
	mentor_waiver = FlagField(column_name='mentor_waiver', attribute='mentor_waiver')
	transfer_program = TField(column_name='transfer_program',attribute='transfer_program',
		widget=widg.ForeignKeyWidget(Program,'program_code'))

	class Meta(object):
		model = ApplicantExceptions
		fields = ('applicant_email','program',)
		export_order = fields
		import_id_fields = ('applicant_email','program')

class MentorDetails(forms.ModelForm):
	m_mob_no = forms.CharField(widget=PhoneNumberPrefixWidget(),
		required=True, initial='+91')
	m_email =forms.EmailField(required=True,)
	m_des =forms.CharField(max_length=30,required=True,)
	m_name =forms.CharField(max_length=60,required=True,)

	def clean_m_mob_no(self):
		m_mob_no = self.cleaned_data.get('m_mob_no')
		if len(m_mob_no.split('.')[0]) == 0 or len(m_mob_no.split('.')[1]) == 0:
			raise forms.ValidationError('This field is required.')
		try:
			x = phonenumbers.parse(m_mob_no,None)
		except phonenumbers.NumberParseException:
			raise forms.ValidationError('Invalid number')

		if not phonenumbers.is_valid_number(x):
			raise forms.ValidationError('Invalid number')
		return m_mob_no

	

	def clean_m_email(self):
		m_email = self.cleaned_data['m_email']
		if not v_e(m_email):
			raise forms.ValidationError('incorrect email id')
		return m_email

	class Meta(object):
		model = CandidateSelection
		fields = ('m_name','m_des','m_mob_no',
			'm_email',)


class HRDetails(forms.ModelForm):
	hr_cont_mob_no = forms.CharField(widget=PhoneNumberPrefixWidget(),
		required=True, initial='+91')
	
	hr_cont_email =forms.EmailField(required=True,)
	
	hr_cont_des =forms.CharField(max_length=30,required=True,)
	
	hr_cont_name =forms.CharField(max_length=60,required=True,)

	def clean_hr_cont_mob_no(self):
		hr_cont_mob_no = self.cleaned_data.get('hr_cont_mob_no')
		if len(hr_cont_mob_no.split('.')[0]) == 0 or len(hr_cont_mob_no.split('.')[1]) == 0:
			raise forms.ValidationError('This field is required.')
		try:
			x = phonenumbers.parse(hr_cont_mob_no,None)
		except phonenumbers.NumberParseException:
			raise forms.ValidationError('Invalid number')

		if not phonenumbers.is_valid_number(x):
			raise forms.ValidationError('Invalid number')

		return hr_cont_mob_no

	def clean_hr_cont_email(self):
		hr_cont_email = self.cleaned_data['hr_cont_email']
		if not v_e(hr_cont_email):
			raise forms.ValidationError('incorrect email id')
		return hr_cont_email

	class Meta(object):
		model = CandidateSelection
		fields = ('hr_cont_name',
			'hr_cont_des','hr_cont_mob_no',
			'hr_cont_email')

class ProgramLocationDetailsResource(resources.ModelResource):

	class PDField(i_e_fields.Field):
		def clean(self, data):
			payment_date = data[self.column_name]
			tzinfos = {"IST": gettz("Asia/Kolkata")}
			try:
				return parse('{}'.format(payment_date),tzinfos=tzinfos,dayfirst=True)
			except Exception as e:
				raise ValidationError("{0}".format(e))

	class PField(i_e_fields.Field):
		def clean(self, data):
			value = data[self.column_name].strip()
			try:
				pg = Program.objects.get(program_code = str(value))
			except Program.DoesNotExist as e:
				raise ValidationError('pg{}'.format(e))
			return pg

	class LField(i_e_fields.Field):
		def clean(self, data):
			value = data[self.column_name].strip()
			try:
				loc = Location.objects.get(location_name = str(value))
			except Location.DoesNotExist as e:
				raise ValidationError('loc{}'.format(e))
			return loc

	program = PField(column_name='program',attribute='program',
		widget=widg.ForeignKeyWidget(Program,'program_code'))
	location = LField(column_name='location',attribute='location',
		widget=widg.ForeignKeyWidget(Location,'location_name'))
	fee_payment_deadline_date = PDField(column_name='fee payment deadline date',
		attribute='fee_payment_deadline_date',)

	class Meta(object):
		model = ProgramLocationDetails
		fields = ('program','location','fee_payment_deadline_date',)
		export_order = fields
		import_id_fields = ('program','location')


class ElectiveCourseListResource(resources.ModelResource):

	program = i_e_fields.Field(column_name = 'program',attribute = 'program',
		widget=ProgramWidget(Program,'program_code'))
	course_id_slot = i_e_fields.Field(column_name = 'course_id_slot',attribute = 'course_id_slot',
		widget=CourseWidget(FirstSemCourseList,'course_id'))

	class Meta(object):
		model = ElectiveCourseList
		import_id_fields = ('course_id',)
		fields = ('program','course_id','course_name','course_units',
				  'course_id_slot')

class ProgLocReportForm(forms.ModelForm):
	class Meta(object):
		model = StudentCandidateApplication
		fields = ('program','current_location')

class OFPImportResource(resources.ModelResource):

	email = i_e_fields.Field(column_name='email', attribute='email', widget=EmailWidget())

	program = i_e_fields.Field(column_name='program', attribute='program',
		widget=ProgramWidget(Program, 'program_code'))

	fee_type = i_e_fields.Field(column_name='fee_type', attribute='fee_type', widget=FTWidget())

	fee_amount = i_e_fields.Field(column_name='fee_amount', attribute='fee_amount',widget=FAWidget())

	enable_zest_flag = i_e_fields.Field(column_name='enable_zest_flag', attribute='enable_zest_flag', widget=EZFWidget())

	enable_eduvenz_flag = i_e_fields.Field(column_name='enable_eduvanz_flag', attribute='enable_eduvenz_flag', widget=EEFWidget())

	enable_ABFL_flag = i_e_fields.Field(column_name='enable_ABFL_flag', attribute='enable_ABFL_flag', widget=EAFWidget())

	def after_save_instance(self, instance, dry_run):
		if not dry_run:
			instance.uploaded_on = dt.now()       
			instance.save()

	class Meta(object):
		model = OtherFeePayment
		import_id_fields = ('email', 'fee_type', 'program')
		fields = ('email', 'program', 'fee_type', 'fee_amount', 'enable_eduvenz_flag', 'enable_ABFL_flag',  'enable_zest_flag')
		export_order = fields


class OFPExportResource(resources.ModelResource):

	created_on = i_e_fields.Field(column_name='created_on', attribute='created_on', widget = UDFieldWidget())

	paid_on = i_e_fields.Field(column_name='paid_on', attribute='paid_on', widget = UDFieldWidget())
	
	uploaded_on = i_e_fields.Field(column_name='uploaded_on', attribute='uploaded_on', widget = UDFieldWidget())
	
	program = i_e_fields.Field(column_name='program', attribute='program',
		widget=widg.ForeignKeyWidget(Program, 'program_code'))

	class Meta(object):
		model = OtherFeePayment
		fields = ('email','program','fee_type','fee_amount','created_on','paid_on','transaction_id',
			'payment_bank','gateway_total_amount','gateway_net_amount','uploaded_on')
		export_order = fields


class UploadFileForm(forms.ModelForm):
	file = forms.FileField(required=False,
		widget=forms.FileInput(attrs={'class':'filecss'}))
	document_name = forms.CharField(max_length=254, required=False, 
		widget=forms.HiddenInput(),)
	deffered_text = forms.CharField(max_length=254, required=False,
		widget=forms.HiddenInput(),)
	exist_file = forms.CharField(max_length=254, required=False, 
		widget=forms.HiddenInput(),)
	exist_file_pk = forms.CharField(max_length=254, required=False, 
		widget=forms.HiddenInput(),)
	x = forms.FloatField(required=False,widget=forms.HiddenInput())
	y = forms.FloatField(required=False,widget=forms.HiddenInput())
	width = forms.FloatField(required=False,widget=forms.HiddenInput())
	height = forms.FloatField(required=False,widget=forms.HiddenInput())
	rotate = forms.FloatField(required=False,widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		super(UploadFileForm, self).__init__(*args, **kwargs)
		self.fields['document'].widget = forms.HiddenInput()
		self.fields['document'].required = False
		if self.initial['document_name'].split('<')[0] == 'APPLICANT PHOTOGRAPH':
			self.fields['file'].widget.attrs['accept'] = 'image/*'

	class Meta:
		model = ApplicationDocument
		fields = ('document','file', 'x', 'y', 'width', 'height','rotate')

		
class DeffDocsUploadForm(forms.ModelForm):
	file = forms.FileField(required=False, widget=forms.FileInput(attrs={'class':'filecss'}))
	document_name = forms.CharField(max_length=254, required=False, 
		widget=forms.HiddenInput(),)
	status = forms.CharField(max_length=254, required=False, 
		widget=forms.HiddenInput(),)
	exist_file = forms.CharField(max_length=254, required=False, 
		widget=forms.HiddenInput(),)
	exist_file_pk = forms.CharField(max_length=254, required=False, 
		widget=forms.HiddenInput(),)
	rej_reason = forms.CharField(max_length=254, required=False, 
		widget=forms.HiddenInput(),)
	x = forms.FloatField(required=False,widget=forms.HiddenInput())
	y = forms.FloatField(required=False,widget=forms.HiddenInput())
	width = forms.FloatField(required=False,widget=forms.HiddenInput())
	height = forms.FloatField(required=False,widget=forms.HiddenInput())
	rotate = forms.FloatField(required=False,widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		super(DeffDocsUploadForm, self).__init__(*args, **kwargs)

		self.fields['document'].widget = forms.HiddenInput()
		self.fields['document'].required = False
		if self.initial['document_name'].split('<')[0] == 'APPLICANT PHOTOGRAPH':
			self.fields['file'].widget.attrs['accept'] = 'image/*'

	class Meta:
		model = ApplicationDocument
		fields = ('document','file', 'x', 'y', 'width', 'height','rotate')

def confirm_update_file_form(app_id):
	class ConfirmUpdateFileForm(forms.Form):
		verify = forms.BooleanField(label='I certify that I have uploaded the correct documents',
			required=True)

		def clean_verify(self):
			verify = self.cleaned_data['verify']
			if verify:
				sca = StudentCandidateApplication.objects.get(pk=int(app_id))
				ad = ApplicationDocument.objects.filter(Q(Q(application=sca) & ~Q(file='')))
				pdm = ProgramDocumentMap.objects.filter(program=sca.program)
				dt = DocumentType.objects.all()
				if pdm.exists():
					pdm = pdm.filter(mandatory_flag=True).values_list('document_type__pk', flat=True)
					ad = ad.filter(document__pk__in=pdm).values_list('document__pk', flat=True)
					if bool(set(ad) ^ set(pdm)):
						raise forms.ValidationError('One or more of the Mandatory Documents required for Application Submission are missing. Please go back to the Previous Page to identify which of the Mandatory Document Submissions are Missing and Submit the same. Mandatory Documents are Highlighted with a RED asterisk')
				else:
					dt = dt.filter(mandatory_document=True).values_list('pk', flat=True)
					ad = ad.filter(document__pk__in=dt).values_list('document__pk', flat=True)
					if bool(set(ad) ^ set(dt.filter(mandatory_document=True))):
						raise forms.ValidationError('One or more of the Mandatory Documents required for Application Submission are missing. Please go back to the Previous Page to identify which of the Mandatory Document Submissions are Missing and Submit the same. Mandatory Documents are Highlighted with a RED asterisk')
			else:
				raise forms.ValidationError('Please check to verify')
			return verify

	return ConfirmUpdateFileForm

class CandidateAcceptRejectForm(forms.ModelForm):

	application_status = forms.ChoiceField(label = 'Set Application Status', choices=[
			(None, 'Select Application Status'),
			(settings.APP_STATUS[5][0], 'Shortlisted'),
			(settings.APP_STATUS[1][0], 'In review'),
			(settings.APP_STATUS[2][0], 'In review - Escalated'),
			(settings.APP_STATUS[7][0], 'Rejected'),
		], 
		widget=forms.Select,
		required=False
	) 
	bits_rejection_reason = forms.MultipleChoiceField(label = 'Rejection Reason',
		choices=[(x.pk, x.reason) for x in BitsRejectionReason.objects.iterator()],
		required=False,
		widget=forms.SelectMultiple(attrs={'style':'width:100%'}))
	selection_rejection_comments = forms.CharField(label = 'Rejection Comments', max_length=254, 
		required=False,
		widget=forms.Textarea(attrs={'cols': 30, 'rows': 5})
	)

	def __init__(self, *args, **kwargs):
		super(CandidateAcceptRejectForm, self).__init__(*args, **kwargs)
		self.fields['bits_rejection_reason'].choices = [(x.pk, x.reason) for x in BitsRejectionReason.objects.iterator()]

	class Meta(object):
		model = StudentCandidateApplication
		fields = ('application_status',)

class ZestForm(forms.Form):
	amount_requested = forms.CharField(required=False, max_length=25, widget=forms.HiddenInput())
	def __init__(self,*args, **kwargs):
		super(ZestForm, self).__init__(*args, **kwargs)
		self.fields['is_terms_and_condition_accepted'] = forms.BooleanField(
			widget=forms.CheckboxInput(attrs={'required': 'required'}),
		)


class BaseReviewerApplicationDocumentForm(forms.ModelForm):
	document_name = forms.CharField(max_length=254,required=False,
		widget=PlainTextWidget,
		)
	file_link = forms.CharField(max_length=254,required=False,
		widget=FileURLWidget,
		)
	deffered_submission_flag = forms.BooleanField(required=False,)
	exception_notes = forms.CharField(required=False, 
		widget=forms.Textarea(attrs={'cols': 30, 'rows': 3}))

	def __init__(self, *args, **kwargs):
		super(BaseReviewerApplicationDocumentForm, self).__init__(*args, **kwargs)
		self.fields['rejection_reason'].empty_label = 'Select Reason'
		self.fields['document_name'].initial = self.instance.document.document_name
		self.fields['deffered_submission_flag'].disabled = not ( self.instance.program_document_map and 
			self.instance.program_document_map.deffered_submission_flag and 
			self.instance.file)
		self.fields['deffered_submission_flag'].initial = (self.instance.program_document_map and 
			self.instance.program_document_map.deffered_submission_flag and
			self.instance.reload_flag)

		p_code = str(self.instance.application.student_application_id)[1:5]
		program_object = Program.objects.filter(program_code=p_code)
		document_submission_flag = program_object[0].document_submission_flag
		if not document_submission_flag:
			if not self.instance.program_document_map.deffered_submission_flag:
				self.fields['rejected_by_bits_flag'].disabled = True

		if self.instance.file:
			self.fields['file_link'].initial = reverse_lazy('registrationForm:document-view', kwargs={'pk': self.instance.pk})
		else:
			self.fields['file_link'].disabled = True
			self.fields['rejection_reason'].disabled = True
			self.fields['exception_notes'].disabled = True
			self.fields['rejected_by_bits_flag'].disabled = True
			self.fields['accepted_verified_by_bits_flag'].disabled = True

	def clean_rejection_reason(self):
		rejected_by_bits_flag = self.cleaned_data.get('rejected_by_bits_flag', False)
		rejection_reason = self.cleaned_data['rejection_reason']
		if rejected_by_bits_flag and not rejection_reason:
			raise forms.ValidationError("select rejected reason")
		return rejection_reason

	class Meta(object):
		model = ApplicationDocument
		fields = ('document_name','file_link','accepted_verified_by_bits_flag',
			'rejected_by_bits_flag','deffered_submission_flag','rejection_reason', 'exception_notes')		

def sub_rev_app_doc(email=None):
	class ReviewerApplicationDocumentForm(BaseReviewerApplicationDocumentForm):
		def save(self, commit=True):

			instance = super(ReviewerApplicationDocumentForm, self).save(commit=False)
			rejection_reason = self.cleaned_data.get('rejection_reason')
			accepted_verified_by_bits_flag = self.cleaned_data.get('accepted_verified_by_bits_flag')
			exception_notes = self.cleaned_data.get('exception_notes')
			file_link = self.cleaned_data.get('file_link')
			deffered_submission_flag = self.cleaned_data.get('deffered_submission_flag')

			if rejection_reason or accepted_verified_by_bits_flag or deffered_submission_flag:
				instance.inspected_on = timezone.localtime(timezone.now())
				instance.verified_rejected_by = email
				instance.reload_flag = False

			if deffered_submission_flag:
				instance.reload_flag = True
				instance.exception_notes = 'Deferred'

			if rejection_reason:
				instance.rejected_by_bits_flag = True
				instance.accepted_verified_by_bits_flag = False

			if commit:instance.save()
			return instance

		class Media(object):
			js = ('{}bits-static/js/reviewer.js'.format(settings.STATIC_URL),)

	return ReviewerApplicationDocumentForm


def def_sub_rev_app_doc(email=None):
	class DefferedApplicationDocumentForm(BaseReviewerApplicationDocumentForm):
		def save(self, commit=True):
			instance = super(DefferedApplicationDocumentForm, self).save(commit=False)
			rejection_reason = self.cleaned_data.get('rejection_reason')
			rejected_by_bits_flag = self.cleaned_data.get('rejected_by_bits_flag')
			accepted_verified_by_bits_flag = self.cleaned_data.get('accepted_verified_by_bits_flag')
			commit = False
			if rejected_by_bits_flag or accepted_verified_by_bits_flag:
				instance.inspected_on = timezone.localtime(timezone.now())
				instance.verified_rejected_by = email
				instance.reload_flag = False
				commit = True

			if rejected_by_bits_flag:
				instance.rejected_by_bits_flag = True
				instance.accepted_verified_by_bits_flag = False
				commit = True

			if commit:instance.save()

			return instance

		class Media(object):
			js = ('{}bits-static/js/deff-reviewer.js'.format(settings.STATIC_URL),)

	return DefferedApplicationDocumentForm

class ApplicantExceptionsExportResource(ApplicantExceptionsResource):

	class Meta(object):
		model = ApplicantExceptions
		fields = ('applicant_email','program','org','hr_contact_waiver','employment_waiver','mentor_waiver','offer_letter',
				'work_ex_waiver','transfer_program','created_on_datetime')
		#fields = ('applicant_email','program','transfer_program','created_on_datetime')
		export_order = fields

	def dehydrate_offer_letter(self, obj):
		return dict((x, y) for x, y in OFFER_LETTER_TEMPLATE_CHOICES).get(obj.offer_letter,None) if obj.offer_letter else None

def get_sca_admit_batch_choices():
	queryset = chain(
			StudentCandidateApplication.objects.values_list('admit_batch', flat=True).iterator(),
			StudentCandidateApplicationArchived.objects.values_list('admit_batch', flat=True).iterator()
		)

	return [(None,'Choose Admit Batch')] + map(lambda x: (x,x), filter(lambda x: x, set(queryset)))

def pgm_adm_filter_form(data=None):
	class PgmAdmReportForm(forms.Form):
		programs = forms.ModelChoiceField(
			widget=forms.Select(attrs={'style':'width:70%'}),
			empty_label='Choose Program',
			queryset=Program.objects.none(),
			required=False)
		
		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

		def __init__(self, *args, **kwargs):
			super(PgmAdmReportForm, self).__init__(*args, **kwargs)
			self.fields['admit_batch'] = forms.ChoiceField(choices=get_sca_admit_batch_choices(),
				required=False, )
			pg_type = data.get('pg_type')
			queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.none()
			self.fields['programs'].queryset = queryset

	return PgmAdmReportForm(data)



class SCA_AdmitBatchForm(forms.Form):
	admit_batch = forms.ChoiceField(
		widget=forms.Select(attrs={'style':'width:80%'}), 
		choices=[(None,'Choose Admit Batch'),],
		required=False, )

	def __init__(self, *args, **kwargs):
		super(SCA_AdmitBatchForm, self).__init__(*args, **kwargs)
		self.fields['admit_batch'].choices = get_sca_admit_batch_choices()


def get_eloa_admit_batch_choices():
	queryset = chain(
		ExceptionListOrgApplicants.objects.values_list('application__admit_batch', flat=True).iterator(), 
		ExceptionListOrgApplicantsArchived.objects.values_list('application__admit_batch', flat=True).iterator()
	)
	
	return [(None,'Choose Admit Batch')] + map(lambda x: (x,x), filter(lambda x: x, set(queryset)))

class ELOA_AdmitBatchForm(forms.Form):
	admit_batch = forms.ChoiceField(
		widget=forms.Select(attrs={'style':'width:80%'}), 
		choices=[(None,'Choose Admit Batch'),],
		required=False, 
	)

	def __init__(self, *args, **kwargs):
		super(ELOA_AdmitBatchForm, self).__init__(*args, **kwargs)
		self.fields['admit_batch'].choices = get_eloa_admit_batch_choices()

def SCA_AdmitBatchProgramForm(data=None,):

	class ScaAdmitBatchForm(forms.Form):
		admit_batch = forms.ChoiceField(
			widget=forms.Select(attrs={'style':'width:60%'}), 
			choices=[(None,'Choose Admit Batch'),],
			required=False, )

		program = forms.ModelChoiceField(
				widget=forms.Select(attrs={'style':'width:60%'}),
				empty_label='Choose Program',
				queryset=Program.objects.none(),
				required=False)

		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)


		def __init__(self, *args, **kwargs):
			super(ScaAdmitBatchForm, self).__init__(*args, **kwargs)
			self.fields['admit_batch'].choices = get_sca_admit_batch_choices()
			pg_type = data.get('pg_type')
			queryset = Program.objects.filter(program_type = pg_type).order_by('program_code') if pg_type else Program.objects.none()
			self.fields['program'].queryset = queryset

	return ScaAdmitBatchForm(data)