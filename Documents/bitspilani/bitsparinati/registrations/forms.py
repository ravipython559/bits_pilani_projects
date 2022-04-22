from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from registration.forms import RegistrationFormUniqueEmail
from djangoformsetjs.utils import formset_media_js
from .models import *
from functools import partial
from phonenumber_field.widgets import PhoneNumberPrefixWidget,PhoneNumberInternationalFallbackWidget
from django.template.defaultfilters import filesizeformat
from django.forms import BaseFormSet, BaseInlineFormSet, BaseModelFormSet
from import_export import resources, fields as i_e_fields, widgets as widg
from django.core.validators import validate_email
from import_export import resources
from phonenumber_field.formfields import PhoneNumberField
from validate_email import validate_email as v_e
from django.core.files.images import get_image_dimensions
from django.db.models import Q
from django.db.models import Max
from django.conf import settings
from decimal import Decimal
from django.utils.html import format_html
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from PIL import Image
from django.core.files import File
from tempfile import NamedTemporaryFile
import dns.resolver, dns.exception
import collections
import csv
import re
import xlrd
import tempfile
import os
import codecs
import phonenumbers
import magic
import mimetypes
from django.core.urlresolvers import reverse_lazy
from django.utils.html import conditional_escape

DateInput = partial(forms.DateInput, {'class': 'datepicker'})

def unique_values(g):
	s = set()
	for x in g:
		if x in s:
			raise forms.ValidationError(_('%s is added more than once')%(
				DocumentType.objects.get(id=x).document_name
				)
			)
		s.add(x)


def getFees(fees):
	for k,v in FEE_TYPE_CHOICE:
		if v == fees.strip():
			return k
	raise ValidationError(_("exception type error"))
	return False

def getFeesName(id):
	for k,v in FEE_TYPE_CHOICE:
		if k == id.strip():
			return v

	return ''

class PaymentDataInput(forms.Form):
	"""Payment Data Uploadation in CSV format in django admin."""

	fileupload = forms.FileField()

	def save(self):
		"""Upload Payment Data form save method."""
		file_upload = self.cleaned_data['fileupload'].name.split('.')
		result = None
		if file_upload[1] == 'csv':
			result = self.csv_form()
		else:
			result = self.excel_form()
		return result

	def csv_form(self):
		"""Upload CSV file format Payment Data."""
		try:
			fd, tmp = tempfile.mkstemp()
			with os.fdopen(fd, 'wb') as out:
				out.write(self.cleaned_data['fileupload'].read())
			f = codecs.open(tmp, 'r', 'utf-8')
			records = csv.reader(f)
			for i in range(17):
				next(records, None)
			for line in records:
				if not line[13]:
					pass
				else:
					try:
						search_group = re.search('(\d{5})T', line[4])
						application_id = search_group.group(1)
						application_id_ = int(application_id)
						obj = StudentCandidateApplication.objects.get(
							id=application_id_)
						if obj.application_status != settings.APP_STATUS[13][0]:
							input_data, create = \
								ApplicationPayment.objects.get_or_create(
									application=obj)
							input_data.payment_id = line[4]
							input_data.payment_amount = line[6]
							input_data.payment_date = line[12]
							input_data.payment_bank = line[2]
							input_data.transaction_id = line[3]
							input_data.save()
							obj.application_status = settings.APP_STATUS[13][0]
							obj.save()
					except:
						pass
		except:
			return "Invalid file content."

	def excel_form(self):
		"""Upload XLS and XLSX format Payment Data."""
		fd, tmp = tempfile.mkstemp()
		with os.fdopen(fd, 'wb') as out:
			out.write(self.cleaned_data['fileupload'].read())
		workbook = xlrd.open_workbook(tmp)
		sheet = workbook.sheet_by_index(0)
		for index_ in range(17, sheet.nrows):
			try:
				if not sheet.cell_value(rowx=index_, colx=13):
					pass
				else:
					try:
						search_group = re.search(
							'(\d{5})T', sheet.cell_value(rowx=index_, colx=4))
						application_id = search_group.group(1)
						application_id_ = int(application_id)
						obj = StudentCandidateApplication.objects.get(
							id=application_id_)
						if obj.application_status != settings.APP_STATUS[13][0]:
							input_data, create = \
								ApplicationPayment.objects.get_or_create(
									application=obj)
							input_data.payment_id = sheet.cell_value(
								rowx=index_, colx=4)
							input_data.payment_amount = sheet.cell_value(
								rowx=index_, colx=6)
							input_data.payment_date = sheet.cell_value(
								rowx=index_, colx=12)
							input_data.payment_bank = sheet.cell_value(
								rowx=index_, colx=2)
							input_data.transaction_id = sheet.cell_value(
								rowx=index_, colx=3)
							input_data.save()
							obj.application_status = settings.APP_STATUS[13][0]
							obj.save()
					except:
						pass
			except:
				return "Invalid file content."

	def clean_fileupload(self):
		filetype = self.cleaned_data['fileupload']
		if filetype.name.split('.')[1] not in ['csv', 'xls', 'xlsx']:
			raise forms.ValidationError("File Type is not Supported")
		return filetype

class MyRegForm(RegistrationFormUniqueEmail):
	"""Registration form to hide the Username field in Django-Registrations."""

	username = forms.CharField(max_length=254, required=False,
							   widget=forms.HiddenInput())
	def clean_email(self):
		"""Validate Email for Exist Email."""
		email = self.cleaned_data['email']
		if  User.objects.filter(email__iexact=email,is_active=True).exists():
			raise forms.ValidationError(
				"These email address already in use")


		if not v_e(email):
			raise forms.ValidationError('incorrect email id')
		else:
			try:
				dns.resolver.query(email.split('@')[-1], 'MX')
			except dns.exception.DNSException:
				raise forms.ValidationError('incorrect email domain')

		return email



class PasswordResetRequestForm(forms.Form):
	email_or_username = forms.CharField(
		label=("Email Or Username"), max_length=254)


class MyAuthenticationForm(AuthenticationForm):
	"""AuthenticationForm for Login Form."""

	error_messages = {
		'invalid_login': _("Please enter a correct email id and password. "
						   "Note that both fields may be case-sensitive."),
		'inactive': _("This account is inactive."),
	}


class EmailValidationOnForgotPassword(PasswordResetForm):
	"""Email Validation Form for Forgot Password."""

	def clean_email(self):
		"""Validate Email for Forgot Password."""
		email = self.cleaned_data['email']
		if not User.objects.filter(email__iexact=email,
								   is_active=True).exists():
			raise ValidationError(
				"There is no user registered with the specified email address!"
			)

		return email

def StudentEducation(pg_code):
	class EducationForm(forms.ModelForm):
		other_degree =forms.CharField(max_length=254,required=False,
			widget=forms.HiddenInput(),)
		other_discipline =forms.CharField(max_length=254,required=False,
			widget=forms.HiddenInput(),)
		qual_cat = forms.ModelChoiceField(
			widget=forms.Select,
			queryset=QualificationCategory.objects.all(),
			required=True)

		def clean_other_degree(self):
			
			other_degree = self.cleaned_data.get('other_degree',False)
			return '' if not other_degree else other_degree

		def clean_other_discipline(self):
			other_discipline = self.cleaned_data.get('other_discipline',False)
			return '' if not other_discipline else other_discipline

		def clean_qual_cat(self):
			cat = self.cleaned_data['qual_cat']
			return cat

		def clean_degree(self):
			degree = self.cleaned_data['degree']
			return degree

		class Meta(object):
			"""Education model form meta class."""

			model = StudentCandidateQualification
			exclude = ('application',)

		class Media(object):
			"""Education model form media class."""

			js = formset_media_js

	return EducationForm

def StudentBaseEducationFormSet(pg_code):
	class BaseEducationFormSet(BaseModelFormSet):
		def clean(self):
			if any(self.errors):return
			p_q_r = ProgramQualificationRequirements.objects.filter(program__program_code=pg_code)
			pqr = p_q_r.values_list('qualification_category__id',flat = True)


			form_cat=[]
			for form in self.forms:
				cat = form.cleaned_data.get('qual_cat',False)
				dlt = form.cleaned_data.get('DELETE')

				if cat and not dlt :form_cat.append(cat.id)

			ex = p_q_r.exclude(qualification_category__id__in =form_cat).values_list('qualification_category__category_name',
				flat=True)

			for x in pqr:
				if not x in form_cat:
					raise forms.ValidationError("""
						Please make entry for the required qualification: {0}
						""".format(ex[0]))    


		class Meta(object):
			model = StudentCandidateQualification
			exclude = ('application',)

	return BaseEducationFormSet




def StudentBaseEducationInlineFormSet(pg_code):
	class BaseEducationFormSet(BaseInlineFormSet):
		def __init__(self,*args,**kwargs):
			super(BaseEducationFormSet, self).__init__(*args, **kwargs)
			for form in self.forms:
				if form.initial:
					degree = Degree.objects.get(id=form.initial['degree'])
					form.initial['qual_cat'] = degree.qualification_category.id
					

		def clean(self):
			

			if any(self.errors):return
			p_q_r = ProgramQualificationRequirements.objects.filter(program__program_code=pg_code)
			pqr = p_q_r.values_list('qualification_category__id',flat = True)

			form_cat=[]

			for form in self.forms:
				cat = form.cleaned_data.get('qual_cat',False)
				dlt = form.cleaned_data.get('DELETE')

				if cat and not dlt :form_cat.append(cat.id)

			ex = p_q_r.exclude(qualification_category__id__in =form_cat).values_list('qualification_category__category_name',
				flat=True)


			for x in pqr:
				if not x in form_cat:
					raise forms.ValidationError("""
						Please make entry for the required qualification: {0}
						""".format(ex[0]))

		class Meta(object):
			model = StudentCandidateQualification
			exclude = ('application',)

	return BaseEducationFormSet

def showUpFileFormChoice():
	UPCHOICE=[(None,'Choose Document Type')]
	UPCHOICE+=[(x.id,x.document_name)for x in DocumentType.objects.filter(mandatory_document=False)]
	return UPCHOICE

class UploadFileForm(forms.Form):
	file = forms.FileField(required=False,widget=forms.FileInput(attrs={'class':'filecss'}))
	document_id = forms.ChoiceField(choices=showUpFileFormChoice())

	class Media(object):
		js = formset_media_js

	def __init__(self, *args, **kwargs):
		super(UploadFileForm, self).__init__(*args, **kwargs)
		self.fields['document_id'] = forms.ChoiceField(choices=showUpFileFormChoice())

	def clean_file(self):
		prefix = self.prefix
		content = self.cleaned_data.get('file',False)
		if content:
			max_upload_size = 10485760

			if content.size > max_upload_size:
				raise forms.ValidationError(
					'''
					Please keep file size under {0}. Current file size {1}
					'''.format(
					filesizeformat(max_upload_size),filesizeformat(content.size)
					)
				)

		return content

	def clean_document_id(self):
		if not self.cleaned_data['document_id']:
			raise forms.ValidationError(_('specify document type'))
		return self.cleaned_data['document_id']

class UploadRequiredFileForm(forms.Form):
	document_name = forms.CharField(max_length=254,
		widget=forms.HiddenInput(),)
	file = forms.FileField(required=False,widget=forms.FileInput(attrs={'class':'filecss'}))
	document_id = forms.CharField(max_length=254,widget=forms.HiddenInput())

	def clean_file(self):
		content = self.cleaned_data['file']
		document_name = self.cleaned_data['document_name']
		if content:
			doc = DocumentType.objects.get(document_name='APPLICANT PHOTOGRAPH')
			max_upload_size = 10485760
			if content.size > max_upload_size:
				raise forms.ValidationError(
					'''
					Please keep file size under %s. Current file size %s
					''' % (
					filesizeformat(max_upload_size),
					filesizeformat(content.size)
					),code='invalid'
				)
				
		return content


class UploadRequiredEditFileForm(forms.Form):
	document_name = forms.CharField(max_length=254,
		widget=forms.HiddenInput(),)
	file = forms.FileField(widget=forms.FileInput({'class':'filecss'}),required=False)
	document_id = forms.CharField(max_length=254,widget=forms.HiddenInput())
	exist_file =forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)

	def clean_file(self):
		content = self.cleaned_data['file']
		prefix = self.prefix
		exist_id_file="%s-exist_file"%(prefix)
		existing_id=self.data[exist_id_file]
		doc = DocumentType.objects.get(document_name='APPLICANT PHOTOGRAPH')

		if content:
			max_upload_size = 10485760
			document_name = self.cleaned_data['document_name']
			if content.size > max_upload_size:
				raise forms.ValidationError(
					'''
					Please keep file size under %s. Current file size %s
					''' % (
					filesizeformat(max_upload_size),
					filesizeformat(content.size)
					),code='invalid'
				)

		return content

def showUpchoices():
	UPCHOICE=[(None,'Choose Document Type')]
	UPCHOICE+=[(x.id,x.document_name)for x in DocumentType.objects.filter(mandatory_document=False)]
	return UPCHOICE

class UploadEditFileForm(forms.Form):
	file = forms.FileField(required=False,widget=forms.FileInput(attrs={'class':'filecss'}))
	document_id = forms.ChoiceField(choices=showUpchoices())
	exist_file =forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)

	exist_file_id =forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)

	def __init__(self, *args, **kwargs):
		super(UploadEditFileForm, self).__init__(*args, **kwargs)
		self.fields['document_id'] = forms.ChoiceField(choices=showUpchoices())

	class Media(object):
		js = formset_media_js

	def clean_file(self):
		content = self.cleaned_data['file']
		prefix = self.prefix
		exist_id_name="%s-exist_file_id"%(prefix)
		existing_id=self.data[exist_id_name]
		if content or (existing_id and content):
			max_upload_size = 10485760
			if content.size > max_upload_size:
				raise forms.ValidationError(_('Please keep file size under %s. Current file size %s') % (
					filesizeformat(max_upload_size),filesizeformat(content.size)
					)
				)
		return content

	def clean_document_id(self):
		if not self.cleaned_data.get('document_id'):
			raise forms.ValidationError(_('specify document type'))
		return self.cleaned_data['document_id']

class BaseUploadFileEditFormSet(BaseFormSet):
	def clean(self):
		if any(self.errors):return

		a=[]
		for form in self.forms:
			content = form.cleaned_data.get('file',False)
			exist_file = form.cleaned_data.get('exist_file_id',False)
			print form.cleaned_data.get('document_id')
			if form.cleaned_data.get('document_id') and \
			not form.cleaned_data.get('DELETE') and (content or exist_file):
				a.append(form.cleaned_data.get('document_id'))

		unique_values(a)

class BaseUploadFileFormSet(BaseFormSet):
	def clean(self):
		if any(self.errors):return
		a=[]
		for form in self.forms:
			print form.cleaned_data.get('document_id')
			content = form.cleaned_data.get('file',False)
			if form.cleaned_data.get('document_id') and \
			 not form.cleaned_data.get('DELETE') and content:
				a.append(form.cleaned_data.get('document_id'))

		unique_values(a)

def studentApplication(pg_code):

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
		"""Student Candidate Application model form."""

		date_of_birth = forms.DateField(widget=DateInput(format='%d-%m-%Y'),
										input_formats=('%d-%m-%Y',))
		current_org_employment_date = forms.DateField(
			widget=DateInput(format='%d-%m-%Y'),
			input_formats=('%d-%m-%Y',),required=False)
		phone = forms.CharField(widget=PhoneNumberPrefixWidget(),required=False)
		mobile = forms.CharField(widget=PhoneNumberPrefixWidget(),required=False)
		current_location = forms.ChoiceField(choices=showExamLocationChoice1(pg))
		exam_location = forms.CharField(required=False,widget=forms.HiddenInput())
		total_work_experience_in_months = forms.IntegerField(initial=0,
			widget=forms.HiddenInput(),required=False)

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
				raise forms.ValidationError(_('error in current location'))
			return Location.objects.get(id=int(self.cleaned_data['current_location']))

		def clean_program(self):
			if not self.cleaned_data['program']:
				raise forms.ValidationError(_('error in program'))
			return Program.objects.get(id=int(self.cleaned_data['program']))
		def clean_total_work_experience_in_months(self):
			days = self.cleaned_data['total_work_experience_in_months']
			
			try:
				ap_exp = ApplicantExceptions.objects.get(applicant_email=self.instance.login_email.email,
					program__program_code = pg_code)
				if ap_exp.work_ex_waiver:return days

			except ApplicantExceptions.DoesNotExist:pass
			if pg.work_exp_check_req:
				days_in_year = days/365.0
				months_in_year = pg.min_work_exp_in_months/12.0
				a_year = pg.min_work_exp_in_months/12 #year calculation
				a_month = pg.min_work_exp_in_months%12 # left months after year calculation

				if days_in_year < months_in_year :
					raise forms.ValidationError('''
							A minimum of {0} years {1} months work experience is required for the program you are applying for.
						'''.format(a_year,a_month))
			return days

		def __init__(self, *args, **kwargs):
			super(StudentForm, self).__init__(*args, **kwargs)
			self.fields['current_location'] = forms.ChoiceField(choices=showExamLocationChoice1(pg))
			self.fields['fee_payment_owner'] = forms.ChoiceField(choices=self.fee_payment_owner_choice())
			self.fields['current_employment_status'] = forms.ChoiceField(choices=self.emp_status_choice())
			self.fields['employer_mentor_flag'].label = 'I confirm that I will be able to find a mentor before the programme begins.'
			self.fields['employer_mentor_flag'].help_text ='Having a Mentor is required. You will be required to nominate a Mentor at the time of submitting supporting documents.'
			self.fields['employer_consent_flag'].label = 'I confirm that my employing organization will give consent for me to enroll for this programme.'
			self.fields['employer_consent_flag'].help_text = 'Employer Consent is required.You will be required to take the employer consent at the time of submitting supporting documents.'
			self.fields['current_org_employee_number'].label = 'Current Employee Number'
			self.fields['current_org_employee_number'].help_text = ''
			self.fields['teaching_mode'].label = ''
			self.fields['programming_flag'].label = ''
			self.fields['alternate_email_id'].label = ''
			if pg.program_type in ['specific','cluster'] :
				teaching_mode_widget = self.fields['teaching_mode'].widget
				self.fields['teaching_mode'].widget = forms.HiddenInput()
				self.fields['teaching_mode'].label = ''
				self.fields['teaching_mode'].help_text = ''
				self.fields['programming_flag'].widget=forms.RadioSelect()
				programming_flag_widget = self.fields['programming_flag'].widget
				self.fields['programming_flag'].widget = forms.HiddenInput()
				self.fields['programming_flag'].label = ''
				alternate_email_id_widget = self.fields['alternate_email_id'].widget
				self.fields['alternate_email_id'].widget = forms.HiddenInput()
				self.fields['alternate_email_id'].label = ''
				self.fields['alternate_email_id'].help_text = ''

				rejected_attributes = FormFieldPopulationSpecific.objects.filter(
					program=pg,
					show_on_form=False,
				).values_list('field_name', flat=True)

				for x in rejected_attributes:
					hidden_field = self.fields.get(x)
					if hidden_field:
						self.fields[x].widget = forms.HiddenInput()
						self.fields[x].label = ''
						self.fields[x].help_text = ''
				
				teaching_mode_rejected_attributes = FormFieldPopulationSpecific.objects.filter(
					program=pg,
					show_on_form=True,
					field_name='teaching_mode',
				)

				programming_flag_selected_attributes = FormFieldPopulationSpecific.objects.filter(
					program=pg,
					show_on_form=True,
					field_name='programming_flag',
				)

				alternate_email_id_selected_attributes = FormFieldPopulationSpecific.objects.filter(
					program=pg,
					show_on_form=True,
					field_name='alternate_email_id',
				)					

				if teaching_mode_rejected_attributes.exists():
					self.fields['teaching_mode'].widget = teaching_mode_widget
					self.fields['teaching_mode'].label = format_html('Please choose the preferred mode of attending classes for the program<p class="required"> *</p>')
					self.fields['teaching_mode'].help_text = 'NOTE : The decision to offer the programme in a particular mode (Online sessions or Face-to-Face sessions) is at the discretion of BITS Pilani, and a decision on the same will be communicated to candidates through the Admission Offer Letter'

				if programming_flag_selected_attributes.exists():
					self.fields['programming_flag'].widget = programming_flag_widget
					self.fields['programming_flag'].label = 'Do you have working knowledge of ANY programming language'
					self.fields['programming_flag'].choices = StudentCandidateApplication.PROGRAMMING_FLAG_CHOICES

				if alternate_email_id_selected_attributes.exists():
					self.fields['alternate_email_id'].widget = alternate_email_id_widget
					self.fields['alternate_email_id'].label = 'Alternate Email Id'
					self.fields['alternate_email_id'].help_text = 'NOTE : Should be different from the main email id provided'



		class Meta(object):
			"""Student Candidate model form meta class."""

			model = StudentCandidateApplication
			exclude = ('application_status', 'admit_year', 'created_on_datetime',
					   'last_updated_on_datetime')

	return StudentForm




class ETField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name]
		value = getFees(value)
		return value

class ETFieldWidget(widg.Widget):
	def render(self, value):
		return '{}'.format(getFeesName(value))

class EEField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name].strip()
		try:
			validate_email( value.strip() )
			if len(value.strip())>50:
				raise ValidationError(_('Email string length more than 50'))
		except ValidationError as e:
			raise ValidationError(_("Email type error"))
		return value


class ENField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name].strip()
		email=data['employee_email'].strip()
		e_type = getFees(data['exception_type'])
		program = data['program']
	   
		eloa = ExceptionListOrgApplicants.objects.filter(
			employee_email=email
			).exclude(Q(program__program_code = program,exception_type=e_type))

		if len(value.strip())==0:
			raise ValidationError(_("employee name error"))

		d_e_n = eloa.values_list('employee_name',
			flat=True).distinct()
		if not value in d_e_n and d_e_n.count() >0: 
			raise ValidationError(_("employee id didn't match "))
		return value

class EIField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name].strip()
		email=data['employee_email'].strip()
		e_type = getFees(data['exception_type'])
		program = data['program']
		eloa = ExceptionListOrgApplicants.objects.filter(
			employee_email=email
			).exclude(Q(program__program_code = program,exception_type=e_type))

		try:
			value = int(value)
			value = str(value)
		except:
			value = data[self.column_name].strip()
		if len(value.strip())==0:
			raise ValidationError(_("employee id error"))

		d_e_id = eloa.values_list('employee_id',
			flat=True).distinct()
		if not value in d_e_id and d_e_id.count() >0: 
			raise ValidationError(_("employee id didn't match "))  
		return value


class OField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name].strip()
		email=data['employee_email'].strip()
		e_type = getFees(data['exception_type'])
		program = data['program']
		eloa = ExceptionListOrgApplicants.objects.filter(
			employee_email=email
			).exclude(Q(program__program_code = program,exception_type=e_type))
		d_org = eloa.values_list('org',
			flat=True).distinct()
		try :
			co = CollaboratingOrganization.objects.get(org_name = value)
		except CollaboratingOrganization.DoesNotExist:
			raise ValidationError(_("org does not exist ")) 
		if not co.id in d_org and d_org.count() >0: 
			raise ValidationError(_("org didn't match "))           
		return super(OField, self).clean( data )



class PField(i_e_fields.Field):
	def clean(self, data):
		value = data[self.column_name].strip()
		email=data['employee_email'].strip()
		e_type = getFees(data['exception_type'])

		try:    
			pg =Program.objects.get(program_code=value)
		except Program.DoesNotExist:
			raise ValidationError("program didn't match ") 
		return pg

class FAField(i_e_fields.Field):
	def clean(self, data):
		fee_amount = data[self.column_name].strip()
		if fee_amount:
			fee_amount = Decimal(fee_amount)

			if fee_amount <= 0:
				raise ValidationError("Fee amount must be greater than zero")

			pfa = PROGRAM_FEES_ADMISSION.objects.get(program__program_code=data['program'].strip(), 
				latest_fee_amount_flag=True, 
				fee_type=( '2' if getFees(data['exception_type'].strip())=='1' else '1' ))

			if fee_amount > pfa.fee_amount:
				raise ValidationError("Fee amount is greater than program fee amount")
		else:
			fee_amount = None

		return fee_amount

class ELOAForeignKeyWidget(widg.ForeignKeyWidget):
	def clean(self, value):
		return super(ELOAForeignKeyWidget, self).clean(value.strip())

class ExceptionListOrgApplicantsResource(resources.ModelResource):
	org = OField(column_name='org',attribute='org',
		widget=ELOAForeignKeyWidget(CollaboratingOrganization,'org_name'))

	program = i_e_fields.Field(column_name='program',attribute='program',
		widget=ELOAForeignKeyWidget(Program,'program_code'))

	exception_type = ETField(column_name='exception_type',
		attribute='exception_type',widget=ETFieldWidget())

	employee_email = EEField(column_name='employee_email',
		attribute='employee_email',)

	employee_name = ENField(column_name='employee_name',
		attribute='employee_name',)

	employee_id = EIField(column_name='employee_id',
		attribute='employee_id',)

	fee_amount = FAField(column_name='fee_amount',
		attribute='fee_amount',)


	def before_import(self,dataset,dry_run, **kwargs):
		data_list = filter(lambda n: n, dataset.dict)
		for x in data_list[:]:
			for y in data_list[:]:
				if x['employee_email'] == y['employee_email']:
					if x['org'] != y['org']:
						raise ValidationError("""
							org code didn't match for email {0}
							""".format(x['employee_email']))
					if x['employee_id'] != y['employee_id']:
						raise ValidationError("""
							employee id didn't match for email {0}
							""".format(x['employee_email']))
					if x['employee_name'] != y['employee_name']:
						raise ValidationError("""
							employee name didn't match for email {0}
							""".format(x['employee_email']))
					
					
		return super(ExceptionListOrgApplicantsResource,
		 self).before_import(dataset,dry_run, **kwargs)


	class Meta(object):
		model = ExceptionListOrgApplicants
		fields = ('employee_email','exception_type',
			'org','program','employee_id','employee_name','fee_amount')
		export_order = fields
		
		import_id_fields = ('employee_email','exception_type','program')

class ELOAForms(forms.ModelForm):

	def clean_org(self):
		email = self.cleaned_data.get('employee_email',None)
		org = self.cleaned_data.get('org',None)
		program = self.cleaned_data.get('program',None)
		e_t = self.cleaned_data.get('exception_type',None)
		eloa = ExceptionListOrgApplicants.objects.filter(
			employee_email=email
			).exclude(Q(program = program,exception_type=e_t))
		d_org = eloa.values_list('org',
			flat=True).distinct()
		if not org.id in d_org and d_org.count() >0: 
			raise ValidationError(_("org didn't match "))    
		return org 

	def clean_employee_id(self):
		email = self.cleaned_data.get('employee_email',None)
		program = self.cleaned_data.get('program',None)
		e_t = self.cleaned_data.get('exception_type',None)
		e_id = self.cleaned_data.get('employee_id',None)
		eloa = ExceptionListOrgApplicants.objects.filter(
			employee_email=email
			).exclude(Q(program = program,exception_type=e_t))
		d_e_id = eloa.values_list('employee_id',
			flat=True).distinct()
		if not e_id in d_e_id and d_e_id.count() >0: 
			raise ValidationError(_("employee id didn't match "))    
		return e_id

	def clean_employee_name(self):
		email = self.cleaned_data.get('employee_email',None)
		program = self.cleaned_data.get('program',None)
		e_t = self.cleaned_data.get('exception_type',None)
		e_name = self.cleaned_data.get('employee_name',None)
		eloa = ExceptionListOrgApplicants.objects.filter(
			employee_email=email
			).exclude(Q(program = program,exception_type=e_t))
		d_e_n = eloa.values_list('employee_name',
			flat=True).distinct()
		if not e_name in d_e_n and d_e_n.count() >0: 
			raise ValidationError(_("employee name didn't match "))
		return e_name

	def clean(self):
		
		if any(self.errors):return

		program = self.cleaned_data.get('program')
		exception_type = self.cleaned_data.get('exception_type')
		fee_amount = self.cleaned_data.get('fee_amount')

		pfa = PROGRAM_FEES_ADMISSION.objects.get(program=program, 
			latest_fee_amount_flag=True, fee_type=( '2' if exception_type=='1' else '1' ))

		if fee_amount > pfa.fee_amount:
				raise ValidationError("Fee amount is greater than program fee amount")

		return self.cleaned_data


	class Meta(object):
		model = ExceptionListOrgApplicants
		fields = ('employee_email','exception_type',
			'org','program','employee_id','employee_name','fee_amount')

class ReviewerRegistrationsForm(forms.ModelForm):
	email = forms.EmailField(label=_('Username'))
	password1 = forms.CharField(label=_('Password'),widget=forms.PasswordInput())
	password2 = forms.CharField(label=_('Retype Password'),widget=forms.PasswordInput())

	def clean_password1(self):
		password1 = self.cleaned_data.get('password1')
		validate_password(password1)
		return password1

	def clean_password2(self):
		password1 = self.cleaned_data.get('password1')
		password2 = self.cleaned_data.get('password2')
		if password1 and password2 and password1 != password2:
			raise forms.ValidationError(_("Passwords don't match"))
		return password2

	def clean_email(self):
		"""Validate Email for Exist Email."""
		email = self.cleaned_data['email']
		user = User.objects.filter(email__iexact=email,is_active=True,)
		validate_email(email)     
		if  user.exists():
			raise forms.ValidationError('email address already exist')    
		return email

	def clean(self):
		
		if any(self.errors):return
		user_role = self.cleaned_data['user_role']
		payment_reviewer = self.cleaned_data['payment_reviewer']

		if payment_reviewer and user_role:
			raise forms.ValidationError('select either payment or user role')

		instance = super(ReviewerRegistrationsForm, self).save(commit=False)
		r_u_e = Reviewer.objects.filter(user__email__icontains = self.cleaned_data['email'])
		if r_u_e.exists():
			raise forms.ValidationError('These email address already in use2')

	class Meta(object):
		model = Reviewer
		fields = ('email','password1','password2','payment_reviewer','user_role')

class EditReviewerRegistrationsForm(ReviewerRegistrationsForm):

	def clean(self):
		if any(self.errors):return
		user_role = self.cleaned_data['user_role']
		payment_reviewer = self.cleaned_data['payment_reviewer']
		email = self.cleaned_data.get('email',None)
		instance = super(EditReviewerRegistrationsForm, self).save(commit=False)
		r_u_e = Reviewer.objects.exclude(pk=instance.pk)

		try:
			r_u_e.get(user__email__iexact=email)
		except Reviewer.DoesNotExist:pass
		else :raise forms.ValidationError('email address taken by other user with role')

		if payment_reviewer and user_role:
			raise forms.ValidationError('select either payment or user role')


	def clean_email(self):
		"""Validate Email for Exist Email."""
		email = self.cleaned_data['email']
		validate_email(email) 
		user = User.objects.filter(email__iexact=email,is_active=True,)    
		if  user.exists():
			try:
				user.get(email__iexact=email).reviewer
			except Exception as e:
				raise forms.ValidationError('email is taken by applicant')    
		return email

class ReviewAcceptedForm(forms.Form):
	doc_type = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	status = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	rejection_reason = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	doc_link = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	doc_name = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)

class ReviewRejectedForm(forms.Form):
	doc_type = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	status = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	rejection_reason = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	doc_link = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	doc_name = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	doc_id = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	file = forms.FileField(widget=forms.FileInput(attrs={'required':'true','class':'filecss'}))
	x = forms.FloatField(required=False, widget=forms.HiddenInput())
	y = forms.FloatField(required=False, widget=forms.HiddenInput())
	width = forms.FloatField(required=False, widget=forms.HiddenInput())
	height = forms.FloatField(required=False, widget=forms.HiddenInput())
	rotate = forms.FloatField(required=False, widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		super(ReviewRejectedForm, self).__init__(*args, **kwargs)
		if self.initial and self.initial['doc_type'] == 'APPLICANT PHOTOGRAPH':
			self.fields['file'].widget.attrs['accept'] = 'image/*'
	
	def clean_file(self):
		content = self.cleaned_data['file']
		if not content:
			raise forms.ValidationError(_('file upload required'))
		return content

	
class RejectForm(forms.ModelForm):
	rejection_by_candidate_comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 30, 'rows': 5}))
	
	def clean_rejection_by_candidate_reason(self):
		rej = self.cleaned_data['rejection_by_candidate_reason'] 
		if not rej :
			raise forms.ValidationError(_('Please select a reason'))
		return rej

	class Meta(object):
		model = CandidateSelection
		fields = ('rejection_by_candidate_reason',
			'rejection_by_candidate_comments')


class ProgramsAndLocation(forms.Form):

	programs = forms.ModelChoiceField(
		widget=forms.Select,
		queryset=Program.objects.all().order_by('program_code'),
		required=False)
	locations = forms.ModelChoiceField(
		widget=forms.Select,
		queryset=Location.objects.all(),
		required=False)


class ProgramLocationDetailsForm(forms.ModelForm):
	admin_contact_phone = PhoneNumberField(required=False)
	acad_contact_phone = PhoneNumberField(required=False)

	class Meta(object):
		model = ProgramLocationDetails
		fields = ('program','location','fee_payment_deadline_date',
			'orientation_date','lecture_start_date','orientation_venue',
			'lecture_venue','admin_contact_person','acad_contact_person',
			'admin_contact_phone','acad_contact_phone',)
		



class ProgramDomainMappingForm(forms.ModelForm):

	program = forms.ModelChoiceField(
		queryset=Program.objects.filter(program_type = 'specific'),)

	def clean(self):
		if any(self.errors):return
		email = self.cleaned_data.get("email")
		email_domain = self.cleaned_data.get("email_domain")

		if (email and email_domain) or (not email and not email_domain):
				raise forms.ValidationError(
					"Fill any one field,either Email or Email_domain"
				)

	class Meta(object):
		model = ProgramDomainMapping
		fields = '__all__'


class ProgramForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		super(ProgramForm, self).__init__(*args, **kwargs)
		# self.fields['enable_pre_selection_flag'].disabled = not self.instance.program_type == 'certification'
		self.fields['enable_pre_selection_flag'].label = 'Enable Applicant Selection before payment of application / booking fees'
		self.fields['enable_pre_selection_flag'].help_text ='(if this checkbox is checked, applicants will be able to pay their application / booking fees only when they are pre-selected. Currently this checkbox can be checked for Certificate Programs Only)'
		self.fields['active_for_applicaton_flag'].label = 'Active for application flag'
		self.fields['active_for_applicaton_flag'].help_text = '(if unchecked, new application submissions for the program will not be allowed)'
		self.fields['active_for_admission_flag'].label = 'Active for Admission Flag'
		self.fields['active_for_admission_flag'].help_text = '(if unchecked, applicants will not be able to accept offers or pay admission fees for the program. No new student admission will be allowed for the program)'
		self.fields['document_submission_flag'].help_text = '(if unchecked, no submission or resubmission of application documents will be allowed for applicants)'



	def clean(self):
		if any(self.errors):return

		active_for_applicaton_flag = self.cleaned_data.get('active_for_applicaton_flag', None)
		document_submission_flag = self.cleaned_data.get('document_submission_flag', None)
		active_for_admission_flag = self.cleaned_data.get('active_for_admission_flag', None)
		if not document_submission_flag:
			if active_for_applicaton_flag:
				raise ValidationError({
					'active_for_applicaton_flag': ValidationError("Program cannot be open for Application while document submissions are disabled")
				})

		if document_submission_flag:
			if not active_for_admission_flag:
				raise ValidationError({
					'document_submission_flag': ValidationError("Document submissions cannot be enabled while Admissions are closed")
					})

		is_zest_emi_enable = self.cleaned_data['is_zest_emi_enable']
		is_eduvanz_emi_enable = self.cleaned_data['is_eduvanz_emi_enable']

		if is_zest_emi_enable and is_eduvanz_emi_enable:
			zest_location = list(self.cleaned_data['zest_location'].values_list('pk', flat=True))
			eduvanz_location = list(self.cleaned_data['eduvanz_location'].values_list('pk', flat=True))

			if not zest_location and not eduvanz_location:
				raise forms.ValidationError("Zest and Eduvanz Loan options cannot be provided together. Please check either of the options or restrict either to a set of locations")

			if list(set(zest_location) & set(eduvanz_location)):
				raise forms.ValidationError("Zest and Eduvanz Loan Options cannot be provided for the same locations")



	def clean_collaborating_organization(self):
		program_type = self.cleaned_data.get('program_type',False)
		collaborating_organization = self.cleaned_data['collaborating_organization']
		if (program_type == 'specific') and not collaborating_organization:
			raise forms.ValidationError(
				"Select Collaborating Organization"
				)
		return collaborating_organization
		
	def clean_serial_number_on_page(self):
		serial_number_on_page = self.cleaned_data['serial_number_on_page']
		show_on_page_flag = self.cleaned_data['show_on_page_flag']
		program_code = self.cleaned_data.get('program_code',None)

		if show_on_page_flag == True: 
			if Program.objects.filter(show_on_page_flag=True,
				serial_number_on_page=serial_number_on_page,).exclude(program_code=program_code).exists():
				raise forms.ValidationError(
				"Enter Unique Serial Number"
				)
		return serial_number_on_page
		
	def clean_min_work_exp_in_months(self):
		min_work_exp_in_months = self.cleaned_data['min_work_exp_in_months']
		work_exp_check_req = self.cleaned_data['work_exp_check_req']

		if work_exp_check_req and not min_work_exp_in_months:
			raise forms.ValidationError(
				"Enter Minimum Work Experience in Months"
				)
		return min_work_exp_in_months

	def clean_alternative_program_code(self):
		a_p_c = self.cleaned_data.get('alternative_program_code',None)
		

		e_p =[ x.alternative_program_code.split(',') for x in Program.objects.exclude(
			Q(alternative_program_code = '') | Q(alternative_program_code__isnull = True )
			).exclude(
			program_code=self.cleaned_data.get('program_code',None)
			)]
		pg_list = set((reduce(lambda x,y:x+y,e_p) if e_p else [] ) + list(Program.objects.values_list('program_code',flat=True)))


		if a_p_c:
			if pg_list & set(a_p_c.split(',')):
				raise forms.ValidationError(
					"""
					Alternate program code {0} already assigned to another program""".
					format( ','.join(list(pg_list & set(a_p_c.split(',')))) )
					)

			for  x in a_p_c.split(','):
				if len(x) != 4:
					raise forms.ValidationError(
						"""
						One or more entries for alternate program codes are not 4 
						characters long. Please correct the entry
						"""
						)

				if not re.match("^[a-zA-Z0-9]{4}$",x):
					raise forms.ValidationError(
						"""
						No special characters other than comma is allowed. 
						Please correct the entry
						"""
						)

		return a_p_c

	class Meta(object):
		model = Program
		fields = '__all__'

	class Media(object):
		js = ('{}bits-static/js/program-js.js'.format(settings.STATIC_URL),)

class BaseExperienceFormSet(BaseModelFormSet):
	def __init__(self,*args,**kwargs):
		super(BaseExperienceFormSet, self).__init__(*args, **kwargs)


	class Meta(object):
			model = StudentCandidateWorkExperience
			exclude = ('application',)



class ExperienceForm(forms.ModelForm):
	"""Experience model form."""

	start_date = forms.DateField(widget=DateInput(format='%d-%m-%Y'),
								 input_formats=('%d-%m-%Y',))
	end_date = forms.DateField(widget=DateInput(format='%d-%m-%Y'),
							   input_formats=('%d-%m-%Y',))

	class Meta(object):
		"""Experience model form Meta class."""

		model = StudentCandidateWorkExperience
		exclude = ('application',)

	class Media(object):
		"""Experience model form Media class."""

		js = formset_media_js




class ProgramFeesAdmissionForm(forms.ModelForm):
	def clean_stud_id_gen_st_num(self):
		stud_id_gen_st_num = self.cleaned_data.get('stud_id_gen_st_num',None)
		fee_type = self.cleaned_data.get('fee_type',False)
		latest_fee_amount_flag = self.cleaned_data['latest_fee_amount_flag']
		if fee_type =='2':
			return None
		if fee_type == '1' and stud_id_gen_st_num == None:
			raise forms.ValidationError('this field is required',
				code='invalid')
		if stud_id_gen_st_num>999:
			raise forms.ValidationError('Please enter a value between 0 and 999',
				code='invalid')
		if not latest_fee_amount_flag :
			raise forms.ValidationError(
				'Update of sequence start number is allowed for records with latest fee amounts only',
				code='invalid')

		return stud_id_gen_st_num

	def clean_admit_sem_des(self):
		admit_sem_des = self.cleaned_data.get('admit_sem_des')
		return admit_sem_des.title() if admit_sem_des else admit_sem_des

	def clean(self):
		stud_id_gen_st_num = self.cleaned_data.get('stud_id_gen_st_num',None)
		fee_type = self.cleaned_data.get('fee_type',False)
		latest_fee_amount_flag = self.cleaned_data['latest_fee_amount_flag']
		admit_year= self.cleaned_data.get('admit_year',False)
		program = self.cleaned_data.get('program',False)

		if fee_type =='1'  :
			cs = CandidateSelection.objects.filter(
				application__program = program,
				application__program__program_fees_admission_requests_created_4__fee_type = fee_type,
				application__program__program_fees_admission_requests_created_4__latest_fee_amount_flag = True,
				application__admit_year = admit_year,
				).aggregate(
				Max('student_id')
				)
			g_s_id = int(cs['student_id__max'][-3:]) if cs['student_id__max'] else 0
			if g_s_id > stud_id_gen_st_num:
				raise forms.ValidationError(
					'''Value of starting sequence number is smaller than the maximum sequence number 
					for the program and admit batch. 
					Please enter a higher value. Suggested value {0}
					'''.format(g_s_id),
				code='invalid')

		if fee_type == ZEST_FEE_TYPE and program and not program.is_zest_emi_enable:
			raise forms.ValidationError(
				'''Zest EMI flag is not set for this program in Program Master table''', 
				code='invalid'
			)
				
		elif fee_type == EDUVANZ_FEE_TYPE and program and not program.is_eduvanz_emi_enable:
			raise forms.ValidationError(
				'Eduvanz EMI flag is not set for this program in Program Master table', 
				code='invalid'
			)
				


	class Meta(object):
		model = PROGRAM_FEES_ADMISSION
		fields = '__all__'

class ProgramAndStatusForm(forms.Form):
		def showStatusChoice():
			st = [(None,'Choose Status')]
			status = [(x[0],x[0])for x in list(settings.APP_STATUS[:12])+[settings.APP_STATUS[17]]]
			status.sort()
			st.extend(status)
			return  st

		programs = forms.ModelChoiceField(
			widget=forms.Select,
			empty_label='Choose Program',
			queryset=Program.objects.none(),
			required=False)
		status = forms.ChoiceField(choices=showStatusChoice(), required=False)
		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)

def rev_filter_form(data = None):
	class ProgramAndStatusForm(forms.Form):
		def showStatusChoice():
			st = [(None,'Choose Status')]
			status = [(x[0],x[0])for x in list(settings.APP_STATUS[:12])+[settings.APP_STATUS[17]]]
			status.sort()
			st.extend(status)
			return  st

		programs = forms.ModelChoiceField(
			widget=forms.Select,
			empty_label='Choose Program',
			queryset=Program.objects.filter(
				program_type = data['pg_type']).order_by('program_code') if data['pg_type'] else Program.objects.none(),
			required=False)
		status = forms.ChoiceField(choices=showStatusChoice(), required=False)
		pg_type = forms.ChoiceField(choices=PROGRAM_TYPE_CHOICES,required=False)
		admit_batch = forms.ChoiceField(choices=[(None,'Choose Admit Batch')] + [
				(x,x) for x in StudentCandidateApplication.objects.values_list('admit_batch', 
				flat=True).distinct().order_by('admit_batch') if x is not None and x != ''],
				required=False,)

	return ProgramAndStatusForm(data)

class ProgramDocumentMapForm(forms.ModelForm):
	def clean(self):
		if any(self.errors):return
		program = self.cleaned_data.get("program")
		document = self.cleaned_data.get("document_type")
		mandatory_flag = self.cleaned_data.get('mandatory_flag')
		deffered_submission_flag = self.cleaned_data.get('deffered_submission_flag')

		pdm = ProgramDocumentMap.objects.filter(program=program, document_type=document)

		if self.instance:
			pdm=pdm.exclude(pk=self.instance.pk)

		if pdm.exists():
			raise forms.ValidationError("Program Document Map with this Program and Document type already exists.")

		elif mandatory_flag and deffered_submission_flag:
		 	raise forms.ValidationError('Select either Mandatory flag or Deferred Submission flag', code='invalid')

		return self.cleaned_data

	class Meta:
		model = ProgramDocumentMap
		fields = '__all__'
		#exclude = ('deffered_submission_flag',)



class PlainTextWidget(forms.Widget):
	def render(self, name, value, attrs=None):
		if value is None:
			value = '-'
		final_attrs = self.build_attrs(attrs, name=name)
		return format_html('<span{}>{}</span>', flatatt(final_attrs), force_text(value))


def student_elective(pg):
	class SESForm(forms.ModelForm):
		fscl_course_id = forms.CharField(required=False,widget=PlainTextWidget)
		fscl_course_name = forms.CharField(required=False,widget=PlainTextWidget)
		fscl_course_unit = forms.CharField(required=False,widget=PlainTextWidget)
		course_id_slot=forms.ModelChoiceField(queryset=FirstSemCourseList.objects.filter(program=pg),
								widget=forms.HiddenInput(),)
		course=forms.ModelChoiceField(required=False,empty_label='Choose Elective',
										queryset=None,widget=forms.Select(attrs={
										'style':'width:50%'}
										),)
				
		def __init__(self,*args, **kwargs):
			super(SESForm, self).__init__(*args, **kwargs)
			if self.initial:
				fscl=FirstSemCourseList.objects.get(id = self.initial['course_id_slot'],)				
				self.initial['fscl_course_id']=fscl.course_id
				self.initial['fscl_course_name']=fscl.course_name
				self.initial['fscl_course_unit']=fscl.course_unit
				self.fields['course'].queryset = ElectiveCourseList.objects.filter(program=pg,
															course_id_slot=fscl)				

			if 'instance' in kwargs:
				obj=kwargs['instance']
				if obj and obj.course_units:
					self.initial['fscl_course_id']=obj.course_id_slot.course_id
					self.initial['fscl_course_name']=obj.course_id_slot.course_name
					self.initial['fscl_course_unit']=obj.course_units.course_units
					self.fields['course'].widget.attrs['disabled']=obj.is_locked

		class Meta:
			model = StudentElectiveSelection
			fields = ('id','fscl_course_id','fscl_course_name','fscl_course_unit',
					'course','course_id_slot',)
	return SESForm


class AdminElectiveCourseListForm(forms.ModelForm):
	ajax_url = forms.CharField(max_length=254,required=False,
		widget=forms.HiddenInput(),)
	course_id_slot = forms.ModelChoiceField(queryset=FirstSemCourseList.objects.filter(
		active_flag=True,is_elective = True))

	def __init__(self, *args, **kwargs):
		super(AdminElectiveCourseListForm, self).__init__(*args, **kwargs)
		self.fields['ajax_url'].initial = reverse_lazy('registrationForm:elective-ajax')
		if 'instance' in kwargs:
			if kwargs['instance']:
				self.fields['course_id_slot'].queryset = FirstSemCourseList.objects.filter(
										program=kwargs['instance'].program,
										active_flag=True,is_elective = True)
	class Meta:
		model = ElectiveCourseList
		fields = '__all__'
	
	class Media:
		js = ['{}/bits-static/js/elective_ajax.js'.format(settings.STATIC_URL),]

def showFieldChoice():
	sca_meta = StudentCandidateApplication._meta.local_fields
	required_filed = [
		'employer_consent_flag',
		'employer_mentor_flag',
		'teaching_mode',
		'programming_flag',
		'alternate_email_id',
		'current_org_employee_number',
	]

	return [(None, '---- choose field ----')] + map(
		lambda x: (x.name, x.verbose_name.capitalize()), 
		filter(
			lambda y: y.name in required_filed, 
			sca_meta
		)
	)


def generate_fields(dyanmic_model_name, dyanmic_field_name):
	import registrations.models as reg_models
	from django.db.models import fields as d_fields

	dynamic_model = getattr(reg_models, dyanmic_model_name)
	dynamic_field = dynamic_model._meta.get_field(dyanmic_field_name)
	label = dynamic_field.verbose_name.capitalize()

	if dynamic_field.select_format.im_class == d_fields.CharField:
		if dynamic_field.choices:
			return forms.ChoiceField(label=label, choices=dynamic_field.choices, required=False)
		else:
			return forms.CharField(label=label, max_length=254, required=False)

	elif dynamic_field.select_format.im_class == d_fields.BooleanField:
		return forms.BooleanField(label=label, required=False)
	else:
		return forms.CharField(label=label, max_length=254, required=False)


class FormFieldPopulationSpecificForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		super(FormFieldPopulationSpecificForm, self).__init__(*args, **kwargs)
		self.fields['program'].queryset = Program.objects.filter(program_type__in=['specific','certification','cluster',])
		self.fields['default_value'].disabled = True
		self.fields['field_name'] = forms.ChoiceField(choices=showFieldChoice())
		self.fields['is_editable'].help_text ='''Employer Consent Flag, employee mentor flag and
		 employee ID - is shown on form by default. You can make an entry to remove if from the 
		 form for a program. Employee id field hiding is currently available for specific program
		  template only. Teaching mode, programming flag and alternate email id are NOT shown
		   on the form by default. You can make an entry to show it on the form for a program.'''
		# if self.instance:
		# 	self.fields['default_value'] = generate_fields(StudentCandidateApplication._meta.object_name, self.instance.field_name)

	# def clean(self):
	# 	if any(self.errors):return
	# 	show_on_form = self.cleaned_data.get("show_on_form")
	# 	is_editable = self.cleaned_data.get("is_editable")
	# 	default_value = self.cleaned_data.get("default_value")

	# 	if not default_value and (not show_on_form or is_editable):
	# 	 	raise forms.ValidationError('Please Enter Default Value', code='invalid')

	# 	return self.cleaned_data

	def save(self, commit=True):
		instance = super(FormFieldPopulationSpecificForm, self).save(commit=False)
		is_editable = self.cleaned_data.get('is_editable', False)
		show_on_form = self.cleaned_data.get('show_on_form', False)
		instance.show_on_form = True if not show_on_form and is_editable else instance.show_on_form
		instance.save()
		return instance

	class Meta:
		model = FormFieldPopulationSpecific
		fields = '__all__'


def form_field_population_specific_ajax(dyanmic_model_name, dyanmic_field_name):

	class FormFieldPopulationSpecificFormAjax(forms.ModelForm):

		def __init__(self, *args, **kwargs):
			super(FormFieldPopulationSpecificFormAjax, self).__init__(*args, **kwargs)
			self.fields['default_value'] = generate_fields(dyanmic_model_name, dyanmic_field_name)

		class Meta:
			model = FormFieldPopulationSpecific
			fields = ('default_value', )

	return FormFieldPopulationSpecificFormAjax

class LocalLoginOrRegisterForm(forms.Form):
	email = forms.EmailField(label='email')

class DMRCertificationForm(forms.Form):
	program = forms.ModelChoiceField(
		queryset=Program.objects.filter(Q(program_type=PROGRAM_TYPE_CHOICES[5][0], active_for_applicaton_flag = True)|
			Q(program_type=PROGRAM_TYPE_CHOICES[5][0], active_for_admission_flag = True)).order_by('program_code'),
		required=False,
		label = 'Certification Program',
		empty_label = 'choose program',
	)

class DMRClusterForm(forms.Form):
	program = forms.ModelChoiceField(
		queryset=Program.objects.filter(Q(program_type=PROGRAM_TYPE_CHOICES[3][0], active_for_applicaton_flag = True)|
		Q(program_type=PROGRAM_TYPE_CHOICES[3][0], active_for_admission_flag = True)).order_by('program_code'),
		required=False,
		label = 'Cluster Program',
		empty_label = 'choose program',
	)

class DMRSpecificForm(forms.Form):
	program = forms.ModelChoiceField(
		queryset=Program.objects.filter(Q(program_type=PROGRAM_TYPE_CHOICES[1][0], active_for_applicaton_flag = True)|
			Q(program_type=PROGRAM_TYPE_CHOICES[1][0], active_for_admission_flag = True)).order_by('program_code'),
		required=False,
		label = 'Specific Program',
		empty_label = 'choose program',
	)

class DMRNonSpecificForm(forms.Form):
	program = forms.ModelChoiceField(
		queryset=Program.objects.filter(Q(program_type=PROGRAM_TYPE_CHOICES[2][0], active_for_applicaton_flag=True)|
			Q(program_type=PROGRAM_TYPE_CHOICES[2][0], active_for_admission_flag = True)).order_by('program_code'),
		required=False,
		label = 'Non Specific Program',
		empty_label = 'choose program',
	)


class DocFileInputWidget(forms.ClearableFileInput):
	def __init__(self, instance=None, *args, **kwargs):
		self.instance = instance
		super(DocFileInputWidget, self).__init__(*args, **kwargs)

	template_with_initial = ('%(input)s<br>'
			'<a href="%(initial_url)s">%(initial)s</a> '
		)

	def get_template_substitution_values(self, value):
		return {
		'initial': conditional_escape(value)[:40]+'...',
		'initial_url': (
			reverse_lazy('registrationForm:document-view', kwargs={'pk': self.instance.pk})
				if self.instance and self.instance.file  else '#'
			),
		}

class DocumentUploadForm(forms.ModelForm):
	
	def __init__(self, *args, **kwargs):
		super(DocumentUploadForm, self).__init__(*args, **kwargs)

		if kwargs.get('instance'):
			document = kwargs.get('instance').document
			sca = kwargs.get('instance').application
		elif self.initial:
			document = self.initial['document']
			sca = StudentCandidateApplication.objects.get(pk=self.initial['application'])
		elif kwargs.get('data'):
			document = DocumentType.objects.get(pk=kwargs['data']['document'])
			sca = StudentCandidateApplication.objects.get(pk=kwargs['data']['application'])

		pdm = ProgramDocumentMap.objects.filter(program=sca.program)
		
		mandatory = (
			pdm.get(document_type=document).mandatory_flag if pdm.exists() 
			else document.mandatory_document
		)

		deffered = (
			pdm.get(document_type=document).deffered_submission_flag if pdm.exists() 
			else False
		)

		self.fields['document'].label = '%s %s %s' % (
			document, 
			'<span class="text-danger">*</span>' if mandatory else '',
			'<br><span style="color:red">Will need to be submitted but can be done later</span>' if deffered else '',
		)
		self.fields['document'].widget = forms.HiddenInput()
		self.fields['application'].widget = forms.HiddenInput()
		self.fields['file'].widget = DocFileInputWidget(instance=kwargs.get('instance') or kwargs.get('data', {}).get('id'))
		self.fields['file'].widget.attrs['class'] = 'filecss'

		if document.document_name=='APPLICANT PHOTOGRAPH':
			self.fields['file'].widget.attrs['accept'] = 'image/*'
			self.fields['x'] = forms.FloatField(required=False, widget=forms.HiddenInput())
			self.fields['y'] = forms.FloatField(required=False, widget=forms.HiddenInput())
			self.fields['width'] = forms.FloatField(required=False, widget=forms.HiddenInput())
			self.fields['height'] = forms.FloatField(required=False, widget=forms.HiddenInput())
			self.fields['rotate'] = forms.FloatField(required=False, widget=forms.HiddenInput())

	def save(self, commit=True):
		instance = super(DocumentUploadForm, self).save(commit=False)
		file = self.cleaned_data.get('file')
		is_cropped_file = (
			file and
			'file' in self.changed_data and 
			instance.document.document_name == 'APPLICANT PHOTOGRAPH'
		)
		instance.verified_rejected_by = ''
		if is_cropped_file:
			tmp_file = NamedTemporaryFile(delete=True)
			x = self.cleaned_data.get('x')
			y = self.cleaned_data.get('y')
			w = self.cleaned_data.get('width')
			h = self.cleaned_data.get('height')
			r = self.cleaned_data.get('rotate')

			with Image.open(file) as image:
				rotated_image = image.rotate(r*(-1), expand=1)
				crop_image = rotated_image.crop((x, y, w+x, h+y))
				resized_image = crop_image.resize((150, 150), Image.ANTIALIAS)
				resized_image.save(tmp_file, format=image.format)
			instance.file = File(tmp_file, name=file.name)

		if commit:
			instance.save()
			if is_cropped_file:
				tmp_file.close()
		return instance

	class Meta(object):
			model = ApplicationDocument
			fields = ('document', 'file', 'application')

class DocumentUploadFormSet(BaseInlineFormSet):
	model = ApplicationDocument