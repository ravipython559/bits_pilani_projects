import json
import requests
import time
from uuid import uuid4
import logging
from django import forms
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.core.urlresolvers import reverse
from .models import ( ExceptionListOrgApplicants as ELOA,ProgramDomainMapping,
	ProgramDocumentMap as PDOCM )
from .models import *
from .forms import *
from django.contrib.auth.models import User
from django.core.mail import send_mail
from djqscsv import render_to_csv_response
from django.db.models.functions import Concat
from django.db.models import Value,F
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.forms.models import (modelformset_factory, inlineformset_factory,
								 formset_factory)
from functools import partial
from django.http import HttpResponsePermanentRedirect
from django.views.decorators.cache import never_cache
from ckeditor.widgets import CKEditorWidget
from django.db import IntegrityError, transaction
from django.views.generic.edit import FormView
from django.conf import settings
from requests.exceptions import ConnectionError
from django.contrib.auth import authenticate, login
from django.template.loader import render_to_string
import uuid
import os
import phonenumbers
from wsgiref.util import FileWrapper
from django.http import FileResponse
from django.http import HttpResponse, JsonResponse
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib
from django.utils import timezone
from .bits_decorator import *
from django.db.models import Q
from django.utils.decorators import method_decorator
from smtplib import SMTPRecipientsRefused
from validate_email import validate_email as v_e
from django.views.static import serve
from registrations.dynamic_views import BaseApplicant
from registration.backends.hmac.views import RegistrationView as BaseRegistrationView
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.template.defaultfilters import mark_safe
from django.http import Http404
from bits_rest.models import MetaZest
from bits_rest.zest_utils import login_approval_update
from registrations.dynamic_views import BaseStudentUpload,BaseDocumentUpload, BaseConfirmationFile, BaseFinalUploadFile, BaseUserFileViewDownload
from registrations.utils.encoding_pdf import BasePDFTemplateView
from registrations.utils.utility_function import check_inactive_program_flag
from datetime import date, timedelta, datetime
import urllib
from urllib import unquote



DateInput = partial(forms.DateInput, {'class': 'datepicker'})
logger = logging.getLogger("main")

class LoginOrRegister(FormView):
	template_name = 'registrations/login-or-register.html'
	success_url = reverse_lazy('registrationForm:applicantData')
	form_class = LocalLoginOrRegisterForm

	def form_valid(self, form):

		user = authenticate(username=form.cleaned_data['email'])
		if user is not None:
			login(self.request, user)
		return super(LoginOrRegister, self).form_valid(form)

class RegistrationView(BaseRegistrationView):
	def create_inactive_user(self, form):
		new_user = form.save(commit=False)
		s_e_d = ProgramDomainMapping.objects.filter(Q(email = new_user.email)|
				Q(email_domain__iexact = new_user.email.split('@')[1])).exists()

		if s_e_d:
			new_user.is_active = True
			new_user.save()
			user = authenticate(username=new_user.email,
			 password=form.cleaned_data['password1'])
			login(self.request, user)
		else:
			# With utm codes, for direct or genric link and direct link without utm codes
			if unquote(self.request.META.get('QUERY_STRING')) != '':
				requested_path = unquote(self.request.META.get('QUERY_STRING')).split('/')
				program_code_utm_code = requested_path[-1]
				program_code_for_direct_utm = -2
				if requested_path[-1] == '':
					program_code_utm_code = requested_path[-2]
					program_code_for_direct_utm = -3
				# genric with utm codes
				program_code = program_code_utm_code
				utm_codes = program_code_utm_code.split('&')
				# direct with utm codes
				if '?' in program_code_utm_code:
					program_code_utm_code = program_code_utm_code.split('?')
					program_code = requested_path[program_code_for_direct_utm]
					program_object = Program.objects.filter(program_code=program_code).first()
					if program_object:
						new_user._program = program_object
					else:
						new_user._program = None
				else:
					program_object = Program.objects.filter(program_code=program_code_utm_code).first()
					if program_object:
						new_user._program = program_object
					else:
						new_user._program = None
			else:
				new_user._program = None
			new_user.is_active = False
			new_user.save()

			self.send_activation_email(new_user)
			#With utm codes, for direct or genric link and direct link without utm codes
			print("105", unquote(self.request.META.get('QUERY_STRING')))
			if unquote(self.request.META.get('QUERY_STRING'))!= '':
				requested_path = unquote(self.request.META.get('QUERY_STRING')).split('/')
				program_code_utm_code = requested_path[-1]
				program_code_for_direct_utm = -2
				if requested_path[-1] == '':
					program_code_utm_code = requested_path[-2]
					program_code_for_direct_utm = -3
				#genric with utm codes
				program_code = program_code_utm_code
				utm_codes = program_code_utm_code.split('&')
				#direct with utm codes
				if '?' in program_code_utm_code:
					program_code_utm_code = program_code_utm_code.split('?')
					program_code = requested_path[program_code_for_direct_utm]
					utm_codes = program_code_utm_code[1].split('&')
				bits_user_object = BitsUser.objects.get(user=new_user.id)
				program_object = Program.objects.filter(program_code=program_code).first()
				bits_user_object.register_program_id = program_object
				# for direct link without utm codes len(utm_codes) will be 1
				if len(utm_codes) != 1:
					bits_user_object.utm_source_first = utm_codes[0].split('=')[-1]
					bits_user_object.utm_medium_first = utm_codes[1].split('=')[-1]
					bits_user_object.utm_campaign_first = utm_codes[2].split('=')[-1]
					bits_user_object.utm_source_last = utm_codes[0].split('=')[-1]
					bits_user_object.utm_medium_last = utm_codes[1].split('=')[-1]
					bits_user_object.utm_campaign_last = utm_codes[2].split('=')[-1]
				bits_user_object.save()
		return new_user

	def get_success_url(self, user):
		s_e_d = ProgramDomainMapping.objects.filter(Q(email = user.email)|
				Q(email_domain__iexact = user.email.split('@')[1])).exists()
		return ('registrationForm:applicantData',(), {}) if s_e_d else ('registration_complete', (), {})

	def get_email_context(self, activation_key):
		pg_code = self.request.COOKIES['program_code'] if 'program_code' in self.request.COOKIES else None
		source_site = self.request.COOKIES['source_site'] if 'source_site' in self.request.COOKIES else None
		ctx = super(RegistrationView, self).get_email_context(activation_key)
		ctx['pg_code'] = pg_code
		ctx['source_site'] = source_site
		return ctx

class ActivationEmailResend(BaseRegistrationView):
	def get(self, request):
		emails = []
		start_time = datetime.strptime(request.GET.get('start_time'),'%Y-%m-%d %H:%M:%S')
		end_time = datetime.strptime(request.GET.get('end_time'),'%Y-%m-%d %H:%M:%S')
		users = User.objects.filter(is_active=False, date_joined__gte=start_time, date_joined__lte=end_time)
		for i in users:
			self.send_activation_email(i)
			emails.append(i.email)
		return JsonResponse({'success':True, 'no_of_user':users.count(), 'start_time': str(start_time), 'end_time':str(end_time), 'email': emails})

		
class RegistrationViewUser(FormView):
	"""User registration view."""

	template_name = 'registration/registration_form.html'
	form_class = MyRegForm
	success_url = '/registrations/view/'

	def form_valid(self, form):
		"""Validate user registration form."""
		logger.debug("Creating user {}".format(form.cleaned_data['username']))
		form.save()
		username = self.request.POST['email']
		password = self.request.POST['password1']
		# authenticate user then login
		user = authenticate(username=username, password=password)
		login(self.request, user)
		return super(RegistrationViewUser, self).form_valid(form)

@login_required
def bits_login(request):
	"""Redirect a user to user login or admin login."""
	if request.user.is_staff:
		logger.info("User is staff user redirecting to Admin User login page.")
		return redirect(reverse('bits_admin:applicantData'))
	else:
		bits_user_object = BitsUser.objects.get(user=request.user.id)
		requested_path = request.META.get('HTTP_REFERER').split('/')
		program_code_utm_code = requested_path[-1]
		if requested_path[-1] == '':
			program_code_utm_code = requested_path[-2]
		program_code_utm_code = program_code_utm_code.split('?')
		if len(program_code_utm_code) !=1:
			utm_codes = program_code_utm_code[1].split('&')
			bits_user_object.utm_source_last = utm_codes[0].split('=')[-1]
			bits_user_object.utm_medium_last = utm_codes[1].split('=')[-1]
			bits_user_object.utm_campaign_last = utm_codes[2].split('=')[-1]
		bits_user_object.save()
		logger.info("User is redirecting to User login page.")
		return redirect(reverse('registrationForm:bits-login-user'))

def direct_url_for_application(request, pg_code=None, source_site=None, params=None):
	try:
		pg = Program.objects.get(program_code = pg_code)
		q = request.META['QUERY_STRING']
		if pg.program_type == 'specific':
			response = redirect(str(reverse('application_specific:specific_form_add',kwargs={'pg_code':pg_code}))+ '?' + q)
		else:
			response = redirect(str(reverse('registrationForm:student-application',kwargs={'pg_code':pg_code})) + '?' + q)

		response.set_cookie('program_code', pg_code)
		if source_site:
			response.set_cookie('source_site',source_site)
			if source_site not in dict(BitsUser.SOURCE_SITE_CHOICES).keys():
				raise Exception("no such source site {0}".format(source_site))
	except Exception as e:
		response = redirect(reverse('registration_register'))
	return response

def verification_link_for_activation(request, activation_key, pg_code=None, source_site=None):
	response = HttpResponseRedirect(reverse('registration_activate',
		kwargs={'activation_key':activation_key})
	)
	if pg_code:
		response.set_cookie('program_code',pg_code)
	if source_site:
		response.set_cookie('source_site',source_site)
	return response
	

@staff_member_required
def bits_admin_login(request):
	"""Redirect the user to admin instructions page."""
	logger.info("Redirecting to Admin Page.")
	return render(request, 'instructions.html',
				  {'data': Instruction.objects.get(id=1)})


@login_required
def user_login(request):
	logger.info("There are no submitted applications. "
					"Redirecting to User instructions page.")
	pg = Program.objects.filter(show_on_page_flag = True,
		active_for_applicaton_flag = True,
		program_type__in=['non-specific','cluster','certification']).distinct()
	clust = pg.filter(program_type='cluster').exists()

	return render(request, 'instructionuser.html',
				  {'data': Instruction.objects.get(id=1),
				  'pg':pg,
				  'clust':clust,
				  })



@login_required
def user_waiver_login(request):
	logger.info("There are no submitted applications. "
					"Redirecting to waiver instructions page.")
	pg = Program.objects.filter(
		Q(
			show_on_page_flag = True,
			active_for_applicaton_flag = True,
			show_to_fee_wvr_appl_flag = True ,
			program_type__in=['non-specific','cluster']
			)|
		Q(
			exceptionlistorgapplicants_requests_created_101__employee_email=request.user.email,
			exceptionlistorgapplicants_requests_created_101__exception_type__in=['1','2'],
			show_on_page_flag = True,
			active_for_applicaton_flag = True,
			program_type__in=['non-specific','cluster']
		)
		).distinct()
	clust = pg.filter(program_type='cluster').exists()

	return render(request, 'user_waiver.html',{'pg':pg,'clust':clust})

@login_required
@reviewer_login_permission
def bits_user_login(request):
	"""Redirect the user.

	Redirect the user to application page if the user account exists or
	redirect to user instructions page.
	"""
	query = StudentCandidateApplication.objects.filter(
		login_email=request.user)
	if len(query) > 0 and (
		query[0].application_status == settings.APP_STATUS[12][0] or
			query[0].application_status == settings.APP_STATUS[13][0] or
			query[0].application_status == settings.APP_STATUS[0][0] or
			query[0].application_status == settings.APP_STATUS[14][0]

			):
		logger.info(
			"User Application Status is {}".format(
				query[0].application_status))
		return redirect(reverse('registrationForm:applicantData'))
	else:
		logger.info("There are no submitted applications. "
					"Redirecting to User instructions page.")
		return redirect(reverse('registrationForm:applicantData'))


@login_required
def applicant_data(request):
	query = StudentCandidateApplication.objects.filter(
		login_email=request.user)
	logger.info("Return Student Candidate Application data.")
	return render(request, 'applicantView.html', {"queryResult": query})
	

@login_required
@reviewer_login_permission
@program_cookie
def view_data(request,*args,**kwargs):
	"""Return the Student Candidate Applicant data."""
	query = StudentCandidateApplication.objects.filter(
		login_email=request.user)
	if query:
		p_code = str(query[0].student_application_id)[1:5]
		program_object = Program.objects.filter(program_code=p_code)
		document_submission_flag = program_object[0].document_submission_flag
	else:
		document_submission_flag = True
	try:
		login_approval_update(request.user.email)
	except Exception as e:
		errors_list = {'request_error':str(e), 'zest_error':None}
		MetaZest.objects.create(user=request.user, errors=errors_list)
	logger.info("Return Student Candidate Application data.")
	if len(query) == 0:
		list_ = []
		application_object = StudentCandidateApplication()
		application_object.application_status = "Not Submitted"
		list_.append(application_object)
		return render(request, 'progress.html', {"queryResult": list_, "document_submission_flag": document_submission_flag})
	else:
		return render(request, 'progress.html', {"queryResult": query, "document_submission_flag": document_submission_flag})



@method_decorator([login_required,pdf_certificate_user],name='dispatch')
class Applicant (BaseApplicant):
	"""Student candidate applicantion data in PDF format."""

	template_name = "applicantpdf.html"
	pdf_kwargs = {'encoding' : 'utf-8',}



class ReviewApplicant (BasePDFTemplateView):

	template_name = "applicantpdf.html"
	pdf_kwargs = {'encoding' : 'utf-8',}

	def get_context_data(self,app_id, **kwargs):
		if self.request.user.is_authenticated():
			logger.info("Application Data for the user {}".format(app_id))
			context = super(ReviewApplicant, self).get_context_data(
				pagesize="A4",
				title="Hi there!",
				**kwargs)
		
		sca = StudentCandidateApplication.objects.get(student_application_id=app_id)
		pfa_admit = PROGRAM_FEES_ADMISSION.objects.filter(program=sca.program, fee_type=2)[0]
		context['pfa_admit']=pfa_admit
		context['q'] = sca
		context['qualification'] = \
			StudentCandidateQualification.objects.filter(application=sca)[:5]
		context['qual_count'] = range(context['qualification'].count(),5)
		context['exp'] = \
			StudentCandidateWorkExperience.objects.filter(application=sca)

		if context['q'].program.application_pdf_template:
			self.template_name = context['q'].program.application_pdf_template


		return context


@login_required
def fee_download_page(request):
	"""Return transaction id, payment_date and payment_bank."""
	query = StudentCandidateApplication.objects.get(login_email=request.user)
	q = ApplicationPayment.objects.get(application=query,fee_type='2')
	
	logger.info("Download the Application Fee Status page for {}".format(
		request.user))
	ctx = {}
	ctx['ap_id'] = query.application_id()
	logger.debug("Application id {}".format(ctx['ap_id']))
	ctx['ap_name'] = query.full_name
	logger.debug("Application Name {}".format(ctx['ap_name']))
	ctx['ap_program'] = query.program.program_name

	logger.debug("Application Program {}".format(ctx['ap_program']))
	ctx['ap_fee_amount'] = q.payment_amount
	logger.debug("Program Fee {}".format(ctx['ap_fee_amount']))
	
	ctx['ap_pay_bank'] = q.payment_bank
	logger.debug("Paid Fee Bank {}".format(ctx['ap_pay_bank']))
	ctx['ap_trans_io'] = q.transaction_id
	logger.debug("Paid fee Transaction id {}".format(ctx['ap_trans_io']))
	ctx['ap_pay_d_t'] = q.payment_date
	logger.debug("Application Fee paid Date {}".format(ctx['ap_pay_d_t']))

	return render(request, 'freeDownload.html', {"ctx": ctx})


class Payfee (BasePDFTemplateView):
	"""Payment Fee template view."""

	template_name = "payfee.html"
	pdf_kwargs = {'encoding' : 'ISO-8859-1',}

	def get_context_data(self, **kwargs):
		query = StudentCandidateApplication.objects.get(login_email=self.request.user)
		q = ApplicationPayment.objects.get(application=query,fee_type='2')
		context =super(Payfee, self).get_context_data(pagesize="A4", title="Pay fees", **kwargs)      
		context['ap_id'] = query.application_id()
		context['ap_name'] = query.full_name
		context['ap_program'] = query.program.program_name
		context['ap_fee_amount'] = q.payment_amount
		context['ap_pay_bank'] = q.payment_bank
		context['ap_trans_io'] = q.transaction_id
		context['ap_pay_d_t'] = q.payment_date
		return context


@login_required
def csv_view(request):
	"""Return csv response with application data."""
	query = StudentCandidateApplication.objects.filter().values(
		'application_id', 'full_name')
	return render_to_csv_response(
		query, append_datestamp=True,
		field_header_map={'application_id': 'The Id',
						  'full_name': 'Full Name'})


@login_required
@applicant_status_permission([settings.APP_STATUS[12][0],settings.APP_STATUS[18][0]])
@never_cache
def getdata(request):

	"""Return Student candidate application data with payment."""
	query = StudentCandidateApplication.objects.get(login_email=request.user)
	context = {}
	context['pg_type'] = query.program.program_type != 'certification'
	context['ap_id'] = query.application_id()
	context['ap_name'] = query.full_name
	context['ap_program'] = query.program.program_name
	is_pg_inactive = check_inactive_program_flag(query,'active_for_applicaton_flag')
	context['is_pg_inactive'] = is_pg_inactive
	pay_fee = reverse_lazy('registrationForm:payment-redirect')
	context['pay_fee'] = pay_fee
	context['disable'] = ''
	context['pay_now']=Program.objects.filter(pk =query.program.pk, available_in_cities=query.current_location).exists()
	if is_pg_inactive:
		context['pay_fee'] = '#'
		context['disable'] = 'disabled'
	try:
		fee_amount, is_paytm = ELOA.objects.get(
			Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
			employee_email=query.login_email.email, 
			exception_type='1', 
			program=query.program).fee_amount, None

	except ELOA.DoesNotExist : 
		pfa = PROGRAM_FEES_ADMISSION.objects.get(
			program=query.program,latest_fee_amount_flag=True,
			fee_type='2')
		fee_amount, is_paytm = pfa.fee_amount, pfa.is_paytm_enable

	context['ap_fee_amount'] = fee_amount
	context['is_paytm'] = is_paytm
	return render(request, 'payfeeview.html', {"queryResult": context},)


@login_required(login_url="registration_register")
@reviewer_login_permission
@if_certificate_redirect
@specif_viewer_redirect_to('application_specific:specific_form_add')
@if_waiver_redirect
@applicant_status_permission(None)
@never_cache
def application_form(request,pg_code):
	StudentFormset = inlineformset_factory(
		User, StudentCandidateApplication, form=studentApplication(pg_code),
		max_num=1, can_delete=False)
	EducationFormset = modelformset_factory(
		StudentCandidateQualification,
		form=StudentEducation(pg_code), extra=0,min_num=1, can_delete=True, exclude=('application',),
		formset = StudentBaseEducationFormSet(pg_code))
	ExpFormset = modelformset_factory(
		StudentCandidateWorkExperience, form=ExperienceForm, extra=1,
		can_delete=True,formset = BaseExperienceFormSet)
	pgm = Program.objects.get(program_code=str(pg_code))
	if request.method == "POST":
		student_formset = StudentFormset(
			request.POST, instance=request.user, prefix="a")
		exp_formset = ExpFormset(request.POST, prefix="expForm")
		education_formset = EducationFormset(request.POST, prefix="eduForm")

		if student_formset.is_valid() and exp_formset.is_valid() and \
				education_formset.is_valid():
			try:
				with transaction.atomic():

					for s in student_formset:
						x = s.save(commit=False)
						x.application_status = "Submitted"
						pfa = PROGRAM_FEES_ADMISSION.objects.get(
							program=x.program, latest_fee_amount_flag=True,
							fee_type='2')
						x.admit_year = pfa.admit_year
						x.admit_sem_cohort = pfa.admit_sem_cohort
						x.admit_batch = '{0}-{1}'.format(pfa.admit_year, pfa.admit_sem_cohort)
						x.save()

					app = StudentCandidateApplication.objects.get(
						login_email=request.user)
					app.student_application_id = "A" + app.program.program_code + \
					'{:04d}'.format(app.id)
					app.save()
					exp_formset.save(commit=False)
					education_formset.save(commit=False)

					for e in exp_formset:
						if e.is_valid() and e.has_changed():
							x = e.save(commit=False)
							if x in exp_formset.deleted_objects:
								x.delete()
							else:
								x.application = app
								x.save()
					for e in education_formset:
						if e.is_valid() and e.has_changed():
							x = e.save(commit=False)
							if x in education_formset.deleted_objects:
								x.delete()
							else:
								x.application = app
								x.save()
					ApplicantExceptions.objects.filter(applicant_email = app.login_email.email,
							program = app.program,
							transfer_program__isnull = False ).update(application = app)
			except IntegrityError:
				messages.error(
					request,
					'There was an error saving your student application.')
				return redirect(reverse('registrationForm:applicantData'))
			subject = 'Application Form %s has been received'%(app.student_application_id)
			user_detail={'progName': app.program.program_name,
			'location': app.current_location.location_name,
			'appID': app.student_application_id,
			'userID':app.login_email.email,
			'regEmailID':app.email_id}
			msg_plain = render_to_string('reg_email.txt', user_detail)
			msg_html = render_to_string('reg_email.html', user_detail)
			
			email = send_mail(subject,msg_plain,'<'+settings.FROM_EMAIL+'>',
			[app.email_id],html_message=msg_html, fail_silently=True)
			


			return HttpResponseRedirect(
				reverse('registrationForm:pdf-redirect-direct-upload'))
	else:
		student_formset = StudentFormset(instance=request.user, prefix="a")
		exp_formset = ExpFormset(
			prefix="expForm",
			queryset=StudentCandidateWorkExperience.objects.none())
		education_formset = EducationFormset(
			prefix="eduForm",
			queryset=StudentCandidateQualification.objects.none())
	return render(request, 'application_form.html', {
		'studentFormset': student_formset,
		'exformset': exp_formset,
		'educationFormset': education_formset,
		'title':pgm.form_title,
		'is_pg_active':pgm.active_for_applicaton_flag,
		'pg_code':pg_code})


@login_required
@never_cache
@specif_viewer_redirect_to('application_specific:pdf_redirect_direct_upload')
def pdf_redirect_direct_upload(request):

	return render(
		request, 'pdf_upload_page.html',
		)


@login_required
@if_certificate_redirect_to_edit
@specif_viewer_redirect_to('application_specific:specific_edit_form_add')
@if_waiver_redirect_to_edit
@applicant_status_edit_permission
@never_cache
def application_form_edit(request):
	"""
	Student Application Form to Edit.

	Student Ancdidate Application form with inline formset Experience and
	Education to Edit.
	"""
	app = StudentCandidateApplication.objects.get(login_email=request.user)
	StudentFormset = inlineformset_factory(
		User, StudentCandidateApplication, form=studentApplication(app.program.program_code),
		 max_num=1,
		can_delete=False)
	EducationFormset = inlineformset_factory(
		StudentCandidateApplication, StudentCandidateQualification,
		form=StudentEducation(app.program.program_code), extra=0,min_num=1, can_delete=True,
		formset=StudentBaseEducationInlineFormSet(app.program.program_code))

	ExpFormset = inlineformset_factory(
		StudentCandidateApplication, StudentCandidateWorkExperience,
		form=ExperienceForm, extra=1, can_delete=True)

	if request.method == "POST":

		student_formset = StudentFormset(
			request.POST, instance=request.user, prefix="a")
		exp_formset = ExpFormset(
			request.POST, prefix="expForm", instance=app)
		education_formset = EducationFormset(
			request.POST, prefix="eduForm", instance=app)
		if student_formset.is_valid() and exp_formset.is_valid() and education_formset.is_valid():
			try:
				with transaction.atomic():

					for s in student_formset:
						x = s.save(commit=False)
						pfa = PROGRAM_FEES_ADMISSION.objects.get(
							program=x.program, latest_fee_amount_flag=True
							,fee_type='2')
						x.admit_year = pfa.admit_year
						x.admit_sem_cohort = pfa.admit_sem_cohort
						x.admit_batch = '{0}-{1}'.format(pfa.admit_year, pfa.admit_sem_cohort)
						x.save()

					exp_formset.save(commit=False)
					for obj in exp_formset.deleted_objects:
						obj.delete()


					education_formset.save(commit=False)
					for obj in education_formset.deleted_objects:
						obj.delete()


					app = StudentCandidateApplication.objects.get(login_email=request.user)
					app.student_application_id = "A" + app.program.program_code + \
						'{:04d}'.format(app.id)
					app.exam_location = str(app.current_location)
					if app.application_status == settings.APP_STATUS[16][0] :
						app.application_status = settings.APP_STATUS[14][0]
					app.save()
					exp_formset.save()
					education_formset.save()
					ApplicantExceptions.objects.filter(applicant_email = app.login_email.email,
							program = app.program,
							transfer_program__isnull = False ).update(application = app)

			except IntegrityError:
				messages.error(
					request,
					'There was an error saving your student application.')
				return redirect(reverse('registrationForm:applicantData'))

			subject = 'Application Form %s has been received'%(app.student_application_id)
			user_detail={'progName': app.program.program_name,
			'location': app.current_location.location_name,
			'appID': app.student_application_id,
			'userID':app.login_email.email,
			'regEmailID':app.email_id,
			'is_pg_active':app.program.active_for_applicaton_flag}
			msg_plain = render_to_string('reg_email.txt', user_detail)
			msg_html = render_to_string('reg_email.html', user_detail)
			
			email = send_mail(subject,msg_plain,'<'+settings.FROM_EMAIL+'>',
				[app.email_id],html_message=msg_html,fail_silently=True)
			
			
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))

	else:
		student_formset = StudentFormset(instance=request.user, prefix="a")
		exp_formset = ExpFormset(instance=app, prefix="expForm")
		education_formset = EducationFormset(instance=app, prefix="eduForm")
	return render(
		request, 'application_form_edit.html',
		{'studentFormset': student_formset,
		'exformset': exp_formset,
		'educationFormset': education_formset,'title':app.program.form_title,
		'pg_code':app.program.program_code,
		'is_pg_active':app.program.active_for_applicaton_flag,
		})



@login_required
@certification_view_redirect
@specif_viewer_redirect_to('application_specific:application_form_view')
def application_form_view(request):
	"""Return Student Candidate Application Form."""
	app = StudentCandidateApplication.objects.get(login_email=request.user)
	edu = StudentCandidateWorkExperience.objects.filter(application=app)
	qual = StudentCandidateQualification.objects.filter(application=app)
	uploadFiles = ApplicationDocument.objects.filter(application=app)

	sca_attributes = app.__dict__.keys()
	for x in sca_attributes:
		setattr(app, '%s_hide' %(x), False)

	#logic to check teaching mode
	teaching_mode_check = FormFieldPopulationSpecific.objects.filter(program = app.program,show_on_form=True,
				field_name__in=['teaching_mode','programming_flag','alternate_email_id',]
			).values_list('field_name', flat=True)

	rejected_attributes = FormFieldPopulationSpecific.objects.filter(
		program=app.program,
		show_on_form=False,
	).values_list('field_name', flat=True)

	for x in rejected_attributes:
		setattr(app, '%s_hide' %(x), True)

	is_specific = app.program.program_type == 'specific'

	return render(
		request, 'application_form_view.html',
		{'form': app,
		 'edu1': edu,
		 'qual1': qual,
		 'uploadFiles':uploadFiles,
		 'is_specific':is_specific,
		 'teaching_mode_check':teaching_mode_check,
		 })


@login_required
def payment_error(request):
	"""Return to Payment Gateway Error."""
	return render(request, 'payment_error.html',)

@login_required
def admission_payment_error(request):
	"""Return to Payment Gateway Error."""
	return render(request, 'admission_payment_error.html',)

@login_required
def instruction_update_edit(request):
	"""Edit or Update the Instructions Page."""
	InstructionFormat = modelformset_factory(
		Instruction, fields=('text',), max_num=1,
		widgets={'text': CKEditorWidget()})
	if request.method == 'POST':
		instruction_format = InstructionFormat(request.POST)
		if instruction_format.is_valid():
			logger.debug("Instruction format to update: {}".format(
				instruction_format))
			# Instruction.objects.all().delete()
			for x in instruction_format:
				ins = x.save(commit=False)
				u, c = Instruction.objects.update_or_create(
					id=1, defaults={'text': ins.text})
		else:
			logger.error("Instruction format is not Valid.")
		return HttpResponseRedirect(
			reverse('registrationForm:bits-login-admin'))
	else:
		instruction_format = InstructionFormat(
			queryset=Instruction.objects.order_by('id'))
		logger.debug("Get the Instruction format: {}".format(
			instruction_format))
	return render(
		request, 'instructionsedit.html', {'data': instruction_format})



@never_cache
@login_required
@applicant_status_permission([settings.APP_STATUS[12][0],settings.APP_STATUS[18][0]])
@payment_exception_permission
def redirect_page(request):
	"""Redirect to Payment Gateway Page."""
	ctx = {}
	app = StudentCandidateApplication.objects.get(login_email=request.user)
	try:
		amount = ExceptionListOrgApplicants.objects.get(
			Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
			employee_email=request.user.email,
			exception_type='1',
			program=app.program,
			).fee_amount

	except ExceptionListOrgApplicants.DoesNotExist:
		amount = PROGRAM_FEES_ADMISSION.objects.get(program=app.program,
			latest_fee_amount_flag=True, 
			fee_type='2').fee_amount


	logger.info("Getting user {user}, app {app}".format(
		user=request.user, app=app))
	ctx['merchantTxnRefNumber'] = "C{0}T{1}".format(app.id,uuid4().hex[:])
	ctx['amount'] = str(amount)
	ctx['itc'] = app.student_application_id
	mobile = "%s%s" % (app.mobile.country_code, app.mobile.national_number)

	ctx['mobileNumber'] = mobile
	ctx['customerName'] = app.full_name
	ctx['email'] = app.email_id
	ctx['custID'] = app.id
	ctx['requestType'] = 'APP'

	headers = {'Content-type': 'application/json'}
	try:
		with transaction.atomic():
			logger.info('Request payment processor')
			start_time = time.time()
			seq_count = MetaPayment.objects.filter(application = app,
				fee_type='2').count()
			meta_payment = MetaPayment.objects.create(application=app,
				req_pay_req_date =datetime.now(),
				req_json_data = json.dumps(ctx),
				sequence_number = seq_count + 1,
				order_id = ctx['merchantTxnRefNumber'],
				fee_type='2'
				)
			r = requests.post(settings.PAYMENT_URL, data=json.dumps(ctx), headers=headers)

			meta_payment.req_pay_status = r.status_code
			meta_payment.req_pay_res_date = datetime.now()
			meta_payment.save()

			if r.status_code == 200:
				a = r.json()
				meta_payment.req_json_return_data = a
				meta_payment.save()

				if len(a['responseMessage']) > 10:
					logger.info(
						"Payment succeded user: {} transaction ref: {}".format(
							request.user, a['responseMessage']))
					return HttpResponsePermanentRedirect(a['responseMessage'])
				else:
					logger.warning("failed payment: {}".format(
						a['responseMessage']))
					return redirect(reverse('registrationForm:error-payment'))
			else:
				logger.warning("Payment processor returned: {}".format(
					r.status_code))
				return redirect(reverse('registrationForm:error-payment'))

	except ConnectionError as e:
		logger.error("Unable to establish connection {}".format(e))
		return redirect(reverse('registrationForm:error-payment'))
	except IntegrityError:
		messages.error(request,'There was an error while payment.')
		return redirect(reverse('registrationForm:error-payment'))
	except Exception, e:
		logger.error("Unexpected exception {}".format(e))
		return redirect(reverse('registrationForm:error-payment'))

def validatePhoneNumber(request):
	if request.is_ajax():
		x = phonenumbers.parse(request.GET.get('a'),None)
		if not phonenumbers.is_valid_number(x):return JsonResponse({'num':1})
		return JsonResponse({'num':0})

@method_decorator([
	login_required,
	specif_viewer_redirect_to('application_specific:upload_file_view'),
	applicant_status_permission(settings.APP_STATUS[14][0]),
	], name='dispatch')
class ConfirmationFile(BaseConfirmationFile):
	template_name = 'registrations/student_document_view.html'


@method_decorator([
    login_required,
    require_GET,
    specif_viewer_redirect_to('application_specific:final_upload_file')
    ], name='dispatch')
class FinalUploadFile(BaseFinalUploadFile):
    template_name = 'registrations/student_file_final_display.html'


@login_required
@specif_viewer_redirect_to('application_specific:applicantView')
def finalPDFRedirect(request):
	return redirect(reverse('registrationForm:applicantViewPDF'))

def validateEmailId(request):
	if request.is_ajax():
		x = request.GET.get('a')
		is_valid = v_e(x,check_mx=True)
		return JsonResponse({'num':0}) if is_valid else JsonResponse({'num':1})
		
def validateMentor(request,pg_code):
	if request.is_ajax():
		pg=Program.objects.get(program_code=pg_code)
		x = request.GET.get('a')
		is_mentor_consent = False
		try:
			app_exp = ApplicantExceptions.objects.get(
				applicant_email = request.user.email,
				program__program_code = pg_code
				)
			is_mentor_consent = app_exp.mentor_waiver

		except ApplicantExceptions.DoesNotExist:pass

		if x == 'false' and pg.mentor_id_req and not is_mentor_consent:
			return JsonResponse({'num':1})
		else:
			return JsonResponse({'num':0})


def qualCategoryAjax(request):
	if request.is_ajax():
		x = request.GET.get('select_id')
		degree = Degree.objects.filter(qualification_category = int(x)).order_by('degree_short_name')
		data = {x.id :x.degree_short_name for x in degree}
		return JsonResponse(data)


def qualCategoryAjax1(request):
	if request.is_ajax():
		x = request.GET.get('select_id')
		degree = Degree.objects.filter(qualification_category = int(x))
		data = {x.id :x.degree_short_name for x in degree}
		return JsonResponse(data)

@login_required
@media_permission
def protected_serve(request, path, document_root=None, show_indexes=False):
    return serve(request, path, document_root, show_indexes)

@method_decorator([login_required,], name='dispatch')
class ElectiveSelection(UpdateView):
    template_name = 'registrations/elective/choose_electives.html'
    prefix = 'sesForm'
    status=False
    success_url = reverse_lazy('registrationForm:choose-electives-with-alert-status',
		kwargs={'status':1})
    model = StudentCandidateApplication
    cs_model = CandidateSelection
    first_course_model = FirstSemCourseList
    elective_course_model = ElectiveCourseList
    elective_model = StudentElectiveSelection
    get_object = lambda self: self.model.objects.get(login_email=self.request.user)
    ses_queryset = lambda self: self.elective_model.objects.filter(application=self.object)
    is_ses_locked = lambda self: self.ses_queryset().filter(is_locked=False).exists() if self.ses_queryset().count() else True
    get_def_form = lambda self: student_elective(self.object.program)
    get_success_url = lambda self: self.success_url
    get_cl = lambda self: self.get_course_list().filter(
        is_elective=True
        ).exclude(
            id__in=self.ses_queryset().values_list('course_id_slot',flat=True)
        )

    def get_form_class(self):
        return inlineformset_factory(self.model,self.elective_model, 
            form=self.get_def_form(), extra=self.get_cl().count())

    def get_initial(self):
        return [ {'course_id_slot':x.id,} for x in self.get_cl()]

    def get_course_list(self):
        return self.first_course_model.objects.filter(program=self.object.program, 
            admit_year=self.object.admit_year,active_flag=True,)

    def is_ecl_exists(self):
        ecl = self.elective_course_model.objects.filter(program=self.object.program,
            is_active=True).values_list('course_id_slot',flat=True).distinct()
        return all(elem in ecl for elem in self.get_course_list().filter(is_elective=True).values_list('id',flat=True))

    def get(self, request, status=None, *args, **kwargs):
	self.status = status and bool(int(status))
	return super(ElectiveSelection, self).get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ElectiveSelection, self).get_context_data(*args, **kwargs)
        context['cs'] = self.cs_model.objects.get(application=self.object)
        context['course_list'] = self.get_course_list().filter(is_elective=False)
        context['ecl_exists'] = self.is_ecl_exists()
        context['ses_is_locked'] = self.is_ses_locked()
        context['applicant'] = self.object  
	context['status'] = self.status
        if 'formset' not in kwargs:
            context['formset'] = self.get_form()
        return context

    def form_valid(self, formset):
        self.object = self.get_object()

        with transaction.atomic():
            for f in formset:
                form = f.save(commit=False)
                form.student_id=self.cs_model.objects.get(application=self.object)
                form.program=self.object.program
                form.application=self.object
                form.course_units=form.course
                form.save()

        return super(ElectiveSelection, self).form_valid(formset)

    def form_invalid(self, formset):
        return self.render_to_response(self.get_context_data(formset=formset))


def electiveAjax(request):
	if request.is_ajax():
		x = request.GET.get('program')
		course_list = FirstSemCourseList.objects.filter(program=x,is_elective=True,
														active_flag=True,
													   ).values_list('id','course_id')
		return JsonResponse(dict(course_list))

class ApplicationDocumentAjax(object):
	model = ApplicationDocument
	template_name = 'registrations/inclusion/upload_form.html'
	form_class = DocumentUploadForm

	def form_valid(self, form):
		sca = StudentCandidateApplication.objects.get(login_email=self.request.user)
		document = form.cleaned_data['document']
		file = form.cleaned_data.get('file')

		try:
			pdm = ProgramDocumentMap.objects.get(program=sca.program, document_type=document)
			mandatory = pdm.mandatory_flag
		except ProgramDocumentMap.DoesNotExist:
			pdm = None
			mandatory = document.mandatory_document

		if not file and not mandatory:
			app_doc = None
		else:
			self.object = form.save(commit=False)
			self.object.program_document_map = pdm
			self.object.last_uploaded_on=timezone.localtime(timezone.now())
			self.object.save()
			app_doc = self.object.pk
			sca = self.object.application
			sca.application_status = settings.APP_STATUS[14][0]
			sca.save()
			
		return JsonResponse({'success':True, 'app_doc':app_doc,})

	def form_invalid(self, form):
		return JsonResponse({'success':False, 'errors':form.errors})

	def post(self, request, *args, **kwargs):
		if request.is_ajax():
			return super(ApplicationDocumentAjax, self).post(request, *args, **kwargs)

class ApplicationDocumentCreate(ApplicationDocumentAjax, CreateView):pass

class ApplicationDocumentUpdate(ApplicationDocumentAjax, UpdateView):pass

@method_decorator([
	never_cache, 
	login_required, 
	specif_viewer_redirect_to('application_specific:student_upload_form'),
	payment_exception_permission_upload,
	applicant_status_permission(settings.APP_STATUS[13][0]),
	], name='dispatch')
# class StudentUpload(BaseStudentUpload):pass
class StudentUpload(BaseDocumentUpload):
	template_name = 'registrations/upload_document.html'

@method_decorator([
	login_required,
	never_cache,
	specif_viewer_redirect_to('application_specific:student_upload_form_edit'),
	applicant_status_permission(settings.APP_STATUS[14][0]),
	], name='dispatch')
# class StudentUploadEdit(BaseStudentUpload):pass
class StudentUploadEdit(BaseDocumentUpload):
	template_name = 'registrations/upload_document.html'

@method_decorator([login_required, never_cache,], name='dispatch')
class UserFileViewDownload(BaseUserFileViewDownload):

	def get_application_document(self, request, pk):
		if request.user.is_superuser or request.user.is_staff:
			return ApplicationDocument.objects.get(pk=pk)
		try:
			rv = Reviewer.objects.get(user=request.user)
			return ApplicationDocument.objects.get(pk=pk)
		except Reviewer.DoesNotExist as e:
			return ApplicationDocument.objects.get(pk=pk, application__login_email=request.user)

@method_decorator([login_required, never_cache,], name='dispatch')
class UserArchivedFileViewDownload(BaseUserFileViewDownload):

	def get_application_document(self, request, pk):
		from bits_admin.models import ApplicationDocumentArchived
		if request.user.is_superuser or request.user.is_staff:
			return ApplicationDocumentArchived.objects.get(pk=pk)
			
		rv = Reviewer.objects.get(user=request.user)
		return ApplicationDocumentArchived.objects.get(pk=pk)	 