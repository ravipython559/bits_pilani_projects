import logging
import smtplib
import json
import requests
import time
from django.http import JsonResponse
from uuid import uuid4
from django.core.mail import send_mass_mail
from django import forms
from functools import partial
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.core import mail
from django.views.decorators.cache import never_cache
from easy_pdf.views import PDFTemplateView
from django.conf import settings
from django.template.loader import render_to_string
from django.db import IntegrityError, transaction
from .forms import *
from .extra_forms import *
from django.http import HttpResponsePermanentRedirect
from django.core.mail import get_connection, EmailMultiAlternatives
from django.forms.models import (modelformset_factory, inlineformset_factory,
								 formset_factory)
from django.shortcuts import (render, redirect, HttpResponseRedirect)
from .models import (StudentCandidateApplication, ApplicantionDocumentReason,
					 StudentCandidateQualification,PROGRAM_FEES_ADMISSION,
					 StudentCandidateWorkExperience, 
					 ApplicationDocument, CandidateSelection, 
					 Program,ApplicationPayment,MetaPayment,
					 Location, BitsRejectionReason,ExceptionListOrgApplicants as ELOA, 
					 ApplicantRejectionReason,ProgramLocationDetails) 
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from .bits_decorator import *
from django.db.models import Max
from django.views.decorators.http import require_http_methods
from django.db.models.functions import Concat
from django.db.models import Max,Value,Count,F,Q,CharField, Case,  When,DateTimeField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from djqscsv import render_to_csv_response
from bits_admin.db_tools import Datediff
from bits_admin.task import *
from requests.exceptions import ConnectionError
from table.views import FeedDataView
from .tables import *
from .tables_ajax import *
from .dynamic_views import *
from django.core import serializers
from django.utils import timezone
from bits_rest.bits_extra import student_id_generator
from bits_rest.models import ZestEmiTransaction
from bits_rest.zest_utils import (emi_in_decline, 
	emi_in_progress, 
	emi_in_document_complete, 
	emi_in_cancellation
	)
from bits_rest.viewsets.eduvanz.forms import ApplicationForm as EduvanzApplicationForm
from bits_rest.viewsets.ezcred.forms import ezcredApplicationForm

from bits_rest.viewsets.eduvanz.utils import get_eduvanz_inprogress, get_eduvanz_declined, delete_initiated_application
from bits_rest.viewsets.ezcred.utils import get_ezcred_inprogress,get_ezcred_declined
from bits_rest.viewsets.propelld.utils import get_propelld_inprogress, get_propelld_innew
from bits_rest import zest_statuses as ZS
from bits_rest.bits_decorators import check_emi_status, check_cross_payment
from registrations.bits_api import name_verify_api
import pytz
import cPickle
import operator
from django.core.serializers.json import DjangoJSONEncoder
from bits_admin.forms import DobForm
from registrations.csv_views import *
from django.views.generic import View,UpdateView
from registrations.utils.encoding_pdf import BasePDFTemplateView
import datetime
from django.utils.html import format_html
from django.forms.utils import flatatt
from registrations.utils.utility_function import check_inactive_program_flag
from registrations.utils import offer_letter as ol
from PIL import Image
from django.core.files import File
from tempfile import NamedTemporaryFile
from django_mysql.locks import Lock

from bits_rest.viewsets.propelld.forms import propelldApplicationForm

DateInput = partial(forms.DateInput, {'class': 'datepicker'})
logger = logging.getLogger("main")

subject =_('Application Evaluation Completed - BITS Pilani Work Integrated Learning Programmes')

def get_choice_display(value,choices):
	for k,v in choices:
		if k==value:return v
	return "Not Found"

@method_decorator([login_required,reviewer_permission],name='dispatch')
class MyDataView(ReviewerDataView):
	token = filter_paging().token
	
@method_decorator([login_required,reviewer_permission],name='dispatch')
class RAData(ReviewerApplicantData):
	template_name = 'reviewapplicantview.html'


@method_decorator([login_required, reviewer_permission, if_deffer_redirect],
	name='dispatch')
class ReviewApplicationDetails(BaseReviewData):
	template_name = 'registrations/review_application_form_view.html'
	def get_template_names(self):
		return 'registrations/review_application_pre_select_rej.html' if self.object.application_status in \
		[settings.APP_STATUS[12][0],settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]] else self.template_name
	

@login_required
@reviewer_permission
@require_POST
def send_confirmation_email(request, application_id):
	logger.info("{0} invoked funct.".format(request.user.email))
	app = StudentCandidateApplication.objects.get(id=application_id)
	cs =CandidateSelection.objects.get(application = app)

	try:
		ap_exp = ApplicantExceptions.objects.get(application=app,
			program = app.program)
		if ap_exp.offer_letter:
			cs.offer_letter_template = ap_exp.offer_letter
	except ApplicantExceptions.DoesNotExist:
		if app.program.offer_letter_template:
			cs.offer_letter_template = app.program.offer_letter_template 

	user_detail={'app_name': app.full_name.strip().split()[0],
		'program':app.program.program_name}
	msg_plain = render_to_string('email_content.txt', user_detail)
	msg_html = render_to_string('email_content.html', user_detail)
	email = send_mail(subject,msg_plain,
		'<'+settings.FROM_EMAIL+'>',
		[app.email_id],
		html_message=msg_html,fail_silently=True)
	logger.info("{0} sent shortlisting mail".format(request.user.email))
	app.application_status = settings.APP_STATUS[6][0]	
	cs.offer_reject_mail_sent = timezone.localtime(timezone.now())
	cs.save()
	app.save()
	logger.info("{0} changed applicant status".format(request.user.email))
	return HttpResponseRedirect(reverse(
		'registrationForm:review-applicant-data'))

@login_required
@reviewer_permission
@require_POST
def send_rejection_email(request, application_id):
	app = StudentCandidateApplication.objects.get(id=application_id)
	user_detail={'app_name': app.full_name.strip().split()[0],
		'program':app.program.program_name}
	msg_plain = render_to_string('email_content.txt', user_detail)
	msg_html = render_to_string('email_content.html', user_detail)
	email = send_mail(subject,msg_plain,
		'<'+settings.FROM_EMAIL+'>',
		[app.email_id],
		html_message=msg_html,fail_silently=True)
	logger.info("{0} sent rejecting mail".format(request.user.email))
	app.application_status = settings.APP_STATUS[8][0]
	cs =CandidateSelection.objects.get(application = app)
	cs.offer_reject_mail_sent = timezone.localtime(timezone.now())
	cs.student_id = None
	cs.save()
	app.save()
	logger.info("{0} changed applicant status".format(request.user.email))
	return HttpResponseRedirect(
		reverse('registrationForm:review-applicant-data'))

@method_decorator([login_required,reviewer_permission],name='dispatch')
class BulkMailFilterPagingView(FeedDataView):

	token = bulk_mail_filter_paging().token

	def get_queryset(self):

		query = super(BulkMailFilterPagingView, self).get_queryset()
		pg_id = int(self.kwargs.get('pg',None))
		loc_id = int(self.kwargs.get('lo',None))
		pg_id = None if  not pg_id else int(pg_id)
		loc_id = None if  not loc_id else int(loc_id)
		try:
			pg = Program.objects.get(id=pg_id)
		except Program.DoesNotExist:
			pg = None
		try:
			loc = Location.objects.get(id=loc_id)
		except Location.DoesNotExist:
			loc = None

		exclude_status = [
		settings.APP_STATUS[12][0],
		settings.APP_STATUS[13][0],
		settings.APP_STATUS[14][0],
		settings.APP_STATUS[15][0],
		settings.APP_STATUS[16][0],
		]
		query = query.exclude(application_status__in = exclude_status)
		if loc and pg:
			query = query.filter(Q(program=pg),
				Q(current_location=loc))
		elif not loc and not pg:pass
		else:
			query = query.filter(Q(program=pg)|
				Q(current_location=loc))

		query = query.annotate(
			app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
			pg_name = F('program__program_name'),
			)
		return query



@login_required
@reviewer_permission
def review_applicant_list(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	query = StudentCandidateApplication.objects.filter(
			application_status__in=[
				settings.APP_STATUS[1][0],
				settings.APP_STATUS[2][0],
				settings.APP_STATUS[3][0],
				settings.APP_STATUS[4][0],
				settings.APP_STATUS[5][0],
				settings.APP_STATUS[6][0],
				settings.APP_STATUS[7][0],
				settings.APP_STATUS[8][0],
				settings.APP_STATUS[9][0],
				settings.APP_STATUS[10][0],
				settings.APP_STATUS[11][0],
				])
	query = query.annotate(
		app_id = Case(
			When(candidateselection_requests_created_5550__new_application_id=None, 
				then=Concat('student_application_id',Value(' '))),
			default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
			output_field=CharField(),
			),
		pg_name = F('program__program_name'),
		)


	SCATable = bulk_mail_filter_paging()
	table = SCATable(query)

	return render(request, 'reviewapplicantviewlist.html',
		{
		'queryResult': query,
		 'form1': ProgramsAndLocation(),
		 'number_of_applicants': 0,
		 'table':table,
		 })
	
@login_required
@require_POST
@reviewer_permission
def review_program_location_refresh(request):
   
	pg_id = request.POST.get('programs',None)
	pg_id = None if  not pg_id else int(pg_id)

	loc_id = request.POST.get('locations',None)
	loc_id = None if  not loc_id else int(loc_id)
	try:
		pg = Program.objects.get(id=pg_id)
	except Program.DoesNotExist:
		pg = None
	try:
		loc = Location.objects.get(id=loc_id)
	except Location.DoesNotExist:
		loc = None

	exclude_status = [settings.APP_STATUS[12][0],
	settings.APP_STATUS[13][0],
	settings.APP_STATUS[14][0],
	settings.APP_STATUS[15][0],
	settings.APP_STATUS[16][0],
	]
	SCA = StudentCandidateApplication.objects.exclude(application_status__in = exclude_status)
	if loc and pg:
		SCA = SCA.filter(Q(program=pg),
			Q(current_location=loc))
	elif not loc and not pg:pass
	else:
		SCA = SCA.filter(Q(program=pg)|
			Q(current_location=loc))

	SCA = SCA.annotate(
		app_id = Case(
			When(candidateselection_requests_created_5550__new_application_id=None, 
				then=Concat('student_application_id',Value(' '))),
			default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
			output_field=CharField(),
			),
		pg_name = F('program__program_name'),
		)

	SCATable = bulk_mail_filter_paging(
		programs=pg_id,
		location=loc_id
		)
	table = SCATable(SCA)

	data = {'programs': pg_id, 'locations': loc_id}
	return render(request, 'reviewapplicantviewlist.html',
				  {
				  'queryResult': SCA,
				   'form1': ProgramsAndLocation(data),
				   'table':table,}
				   )

@login_required
@require_POST
@reviewer_permission
@csrf_exempt
def recheck_send_confirmation_email(request):
	if request.is_ajax():
		pg_id = request.POST.get('program',None)
		pg_id = None if  not pg_id else int(pg_id)

		loc_id = request.POST.get('location',None)
		loc_id = None if  not loc_id else int(loc_id)
		try:
			pg = Program.objects.get(id=pg_id)
		except Program.DoesNotExist:
			pg = None
		try:
			loc = Location.objects.get(id=loc_id)
		except Location.DoesNotExist:
			loc = None
		apps = StudentCandidateApplication.objects.filter(
			application_status=settings.APP_STATUS[5][0])
		if loc and pg:
			apps = apps.filter(Q(current_location = loc) , Q(program = pg))
		elif not loc and not pg:pass
		else:
			apps = apps.filter(Q(current_location = loc) | Q(program = pg))
  
		connection = mail.get_connection(fail_silently=True)
		connection.open()
		datatuple = []
		for app in apps:
			user_detail={'app_name': app.full_name.strip().split()[0],
			'program':app.program.program_name}
			msg_plain = render_to_string('email_content.txt', user_detail)
			msg_html = render_to_string('email_content.html', user_detail)
			temp=EmailMultiAlternatives(subject,
				msg_plain,
				'<'+settings.FROM_EMAIL+'>',
				 [app.email_id,])
			temp.attach_alternative(msg_html, "text/html")
			datatuple.append(temp)
		counts =apps.count()
		apps_list = list(apps.values_list('pk',flat = True))
		apps.update(application_status = settings.APP_STATUS[6][0])
		CandidateSelection.objects.filter(application__in = apps_list).update(
			offer_reject_mail_sent = timezone.localtime(timezone.now())
			)
		datatuple =tuple(datatuple)
		connection.send_messages(datatuple)
		connection.close()
		return JsonResponse({'num':counts})

@login_required
@reviewer_permission
@csrf_exempt
@require_POST
def recheck_send_rejection_email(request):
	if request.is_ajax():
		
		pg_id = request.POST.get('program',None)
		pg_id = None if  not pg_id else int(pg_id)

		loc_id = request.POST.get('location',None)
		loc_id = None if  not loc_id else int(loc_id)
		try:
			pg = Program.objects.get(id=pg_id)
		except Program.DoesNotExist:
			pg = None
		try:
			loc = Location.objects.get(id=loc_id)
		except Location.DoesNotExist:
			loc = None

		apps = StudentCandidateApplication.objects.filter(
			application_status=settings.APP_STATUS[7][0],)
		if loc and pg:
			apps = apps.filter(Q(current_location = loc) , Q(program = pg))
		elif not loc and not pg:pass
		else:
			apps = apps.filter(Q(current_location = loc) | Q(program = pg))

		connection = mail.get_connection( fail_silently=True)
		connection.open()
		datatuple = []
		for app in apps:
			user_detail={'app_name': app.full_name.strip().split()[0],
			'program':app.program.program_name}
			msg_plain = render_to_string('email_content.txt', user_detail)
			msg_html = render_to_string('email_content.html', user_detail)
			temp=EmailMultiAlternatives(subject,
				msg_plain,
				'<'+settings.FROM_EMAIL+'>',
				 [app.email_id,])
			temp.attach_alternative(msg_html, "text/html")
			datatuple.append(temp)

		counts =apps.count() 
		apps_list = list(apps.values_list('pk',flat = True))
		apps.update(
			application_status = settings.APP_STATUS[8][0])

		CandidateSelection.objects.filter(application__in = apps_list).update(
			offer_reject_mail_sent = timezone.localtime(timezone.now())
			)

		datatuple =tuple(datatuple)
		connection.send_messages(datatuple)
		connection.close()
		return JsonResponse({'num':counts})

@login_required
@specif_viewer_redirect_to('application_specific:reload-documentation')
@applicant_status_permission(settings.APP_STATUS[3][0])
def reload_documentation(request):
	logger.info("{0} invoked funct.".format(request.user.email))

	app =StudentCandidateApplication.objects.get(login_email=request.user)
	ReviewAcceptedFormSet = formset_factory(ReviewAcceptedForm,
		can_delete=False,extra=0)
	ReviewRejectedFormSet = formset_factory(ReviewRejectedForm,
		can_delete=False,extra=0)
	p_code = str(app.student_application_id)[1:5]
	program_object = Program.objects.filter(program_code=p_code)
	document_submission_flag = program_object[0].document_submission_flag

	if request.method == "POST":
		logger.info("{0} inside POST request".format(request.user.email))
		reviewAcceptedFormSet = ReviewAcceptedFormSet(request.POST,prefix='accp_form')
		reviewRejectedFormSet = ReviewRejectedFormSet(request.POST,request.FILES,prefix="rej_form")
		if reviewRejectedFormSet.is_valid() and document_submission_flag:
			logger.info("{0} POST request is valid".format(request.user.email))
			try:
				with transaction.atomic():
					for rrf in reviewRejectedFormSet:
						ad = ApplicationDocument.objects.get(id=rrf.cleaned_data['doc_id'])

						upload_file=rrf.cleaned_data['file']
						tmp_file = NamedTemporaryFile(delete=True)
						if ad.document.document_name == 'APPLICANT PHOTOGRAPH':
							x = rrf.cleaned_data.get('x')
							y = rrf.cleaned_data.get('y')
							w = rrf.cleaned_data.get('width')
							h = rrf.cleaned_data.get('height')
							r = rrf.cleaned_data.get('rotate')
							with Image.open(upload_file) as image:
								rotated_image = image.rotate(r*(-1),expand=1)
								crop_image = rotated_image.crop((x, y, w+x, h+y))
								resized_image = crop_image.resize((150, 150), Image.ANTIALIAS)
								resized_image.save(tmp_file, format=image.format)
							upload_file = File(tmp_file, name=upload_file.name)
						ad.file = upload_file
						#To handle when no data in program_domain_map
						if ad.program_document_map==None:
							ad.reload_flag = False
						else:
							ad.reload_flag = not ad.program_document_map.deffered_submission_flag
						#Previous code
						#ad.reload_flag = not ad.program_document_map.deffered_submission_flag
						ad.accepted_verified_by_bits_flag = False
						ad.rejected_by_bits_flag = False
						ad.rejection_reason = None
						ad.verified_rejected_by = ''
						ad.last_uploaded_on=timezone.now()
						ad.save()
						tmp_file.close()
					app.application_status = settings.APP_STATUS[4][0]
					app.save()

			except IntegrityError,e:
				logger.error("{0} Integrity error {1}".format(request.user.email,e))
				messages.error(request,'There was an error while reload file')
				return redirect(reverse('registrationForm:applicantData')) #need to be set 
		return redirect(reverse('registrationForm:applicantData'))

	else:
		logger.info("{0} inside GET request".format(request.user.email))
		doc = ApplicationDocument.objects.filter(application = app )
		accept_data = []
		reject_data = []
		for x in doc.filter(accepted_verified_by_bits_flag=True):
			data={}
			data['doc_type'] = x.document.document_name
			data['status'] = 'Accepted'
			data['rejection_reason'] = x.rejection_reason
			data['doc_link'] = x.pk if x.file else None
			data['doc_name'] = x.file.name.split("/")[-1]
			accept_data.append(data)

		for x in doc.filter(rejected_by_bits_flag=True):
			data={}
			data['doc_type'] = x.document.document_name
			data['status'] = 'Rejected'
			data['rejection_reason'] = x.rejection_reason
			data['doc_link'] = x.pk if x.file else None
			data['doc_name'] = x.file.name.split('/')[-1]
			data['doc_id'] = x.id
			reject_data.append(data)

		reviewAcceptedFormSet = ReviewAcceptedFormSet(initial=accept_data,
			prefix='accp_form')
		reviewRejectedFormSet = ReviewRejectedFormSet(initial=reject_data,
			prefix='rej_form')
	logger.info("{0} ready to render".format(request.user.email))

	return render(request,'reload_upload_file.html',
		{'RAF': reviewAcceptedFormSet,
		'RRF': reviewRejectedFormSet,
		'app_id': app.student_application_id,
		'formset_prefix':'rej_form',
		'document_submission_flag': document_submission_flag
		})

def get_program_data(request,app,prog):
	amount = None
	pgd = ProgramLocationDetails.objects.get(
			program = prog,
			location = app.current_location
		)

	pfa = PROGRAM_FEES_ADMISSION.objects.get(program=prog,
		fee_type='1',
		latest_fee_amount_flag=True
	)

	fees = PROGRAM_FEES_ADMISSION.objects.get(program = prog,
		fee_type='1',
		latest_fee_amount_flag=True)

	try:
		amount = ExceptionListOrgApplicants.objects.get(
			Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
			employee_email=request.user.email,
			exception_type='2',
			program=prog,
			).fee_amount
	except ExceptionListOrgApplicants.DoesNotExist:
		amount = pfa.fee_amount
	return amount,fees,pgd
	
@require_POST
@login_required
@applicant_status_permission(settings.APP_STATUS[6][0])
def acceptOffer(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	query = StudentCandidateApplication.objects.get(login_email=request.user)
	cs = CandidateSelection.objects.get(application = query)
	cs.accepted_rejected_by_candidate = timezone.localtime(timezone.now())
	is_admission_inactive = check_inactive_program_flag(query, 'active_for_admission_flag')
	input_template = '<input class="btn btn-sm btn-primary" {} type="submit">'
	get_input = lambda **kwargs: format_html(input_template, flatatt(kwargs))
	accept_offer = get_input(value='Accept Admission Offer',disabled = is_admission_inactive)
	reject_offer = get_input(value='Decline Program Selection', id='valB', disabled=is_admission_inactive)
	hr_form = HRDetails(request.POST)
	men_form = MentorDetails(request.POST)
	form = RejectForm()
	amount = None
	template_name = query.program.offer_letter_template
	try:
		amount,fees,pgd=get_program_data(request,query,query.program)
		ap_exp = ApplicantExceptions.objects.get(applicant_email=query.login_email.email,
			program = query.program)
		ap_exp_is_men = ap_exp.mentor_waiver
		ap_exp_is_hr = ap_exp.hr_contact_waiver
		template_name = ap_exp.offer_letter or template_name
		if ap_exp.transfer_program:
			amount,fees,pgd = get_program_data(request,query,ap_exp.transfer_program)
			template_name = (
					ap_exp.offer_letter or 
					ap_exp.transfer_program.offer_letter_template or 
					query.program.offer_letter_template
			)
					
	except (
		ApplicantExceptions.DoesNotExist, 
		ProgramLocationDetails.DoesNotExist,
		PROGRAM_FEES_ADMISSION.DoesNotExist,
		) as e:
		ap_exp_is_men, ap_exp_is_hr = (False, False)
		amount,fees,pgd=get_program_data(request,query,query.program)


		
	is_invalid_form = False
	is_mentor_required = not ap_exp_is_men and query.program.mentor_id_req
	is_hr_required = not ap_exp_is_hr and query.program.hr_cont_req

	if is_mentor_required:
		if men_form.is_valid():
				logger.info("{0} POST request is valid".format(request.user.email))
				cs.m_name = men_form.cleaned_data['m_name']
				cs.m_des = men_form.cleaned_data['m_des']
				cs.m_mob_no = men_form.cleaned_data['m_mob_no']
				cs.m_email = men_form.cleaned_data['m_email']
		else:is_invalid_form = True

	if is_hr_required:
		if hr_form.is_valid():
				logger.info("{0} POST request is valid".format(request.user.email))
				cs.hr_cont_name = hr_form.cleaned_data['hr_cont_name']
				cs.hr_cont_des = hr_form.cleaned_data['hr_cont_des']
				cs.hr_cont_mob_no = hr_form.cleaned_data['hr_cont_mob_no']
				cs.hr_cont_email = hr_form.cleaned_data['hr_cont_email']
		else:is_invalid_form = True

	if is_invalid_form:
		return render(request, 'accept_reject.html', {'form': form,
			'app_name':query.full_name,
			'program_name':query.program.program_name,
			'fees' :fees.fee_amount,
			'app_id':query.student_application_id,
			'dead_date':cs.fee_payment_deadline_dt if cs.fee_payment_deadline_dt else pgd.fee_payment_deadline_date,
			'hr_form':hr_form,
			'men_form':men_form,
			'is_mentor_required':is_mentor_required,
			'is_hr_required':is_hr_required,
			'accept_offer':accept_offer,
			'reject_offer':reject_offer,})

	with Lock('bits_student_id_lock'):

		try:
			ap = ApplicationPayment.objects.get(application = query, fee_type = '1')
		except ApplicationPayment.DoesNotExist:
			query.application_status = settings.APP_STATUS[9][0]
		else:
			query.application_status = settings.APP_STATUS[11][0]
			cs.student_id = student_id_generator(login_email = query.login_email.email)

		cs.fee_payment_deadline_dt = cs.fee_payment_deadline_dt if cs.fee_payment_deadline_dt else pgd.fee_payment_deadline_date
		cs.orientation_dt = pgd.orientation_date
		cs.lecture_start_dt = pgd.lecture_start_date
		cs.orientation_venue = pgd.orientation_venue
		cs.lecture_venue = pgd.lecture_venue
		cs.admin_contact_person = pgd.admin_contact_person
		cs.acad_contact_person = pgd.acad_contact_person
		cs.admin_contact_phone = pgd.admin_contact_phone
		cs.acad_contact_phone = pgd.acad_contact_phone
		cs.adm_fees = amount
		cs.offer_letter_generated_flag = True
		cs.offer_letter_template = template_name
		cs.offer_letter_regenerated_dt = timezone.now()
		cs.offer_letter = ol.render_offer_letter_content(cs)
		cs.save()
	
	logger.info("{0} candidate selection table updated".format(request.user.email))
	query.save()
	logger.info("{0} candidate status updated".format(request.user.email))
	return HttpResponseRedirect(
				reverse('registrationForm:pdf-offer-letter-redirect-direct-upload'))


@login_required
@applicant_status_permission(settings.APP_STATUS[6][0])
def acceptReject(request):
    logger.info("{0} invoked funct.".format(request.user.email))
    query = StudentCandidateApplication.objects.get(login_email=request.user)
    program_name = query.program.program_name
    # m_hr_form = MentorHRDetails()
    hr_form = HRDetails()
    men_form = MentorDetails()
    #is_admission_inactive = not query.program.active_for_admission_flag or is_transfer_program_admission_active_disable(query)
    is_admission_inactive = check_inactive_program_flag(query,'active_for_admission_flag')
    input_template = '<input class="btn btn-sm btn-primary" {} type="submit">'
    get_input = lambda **kwargs: format_html(input_template, flatatt(kwargs))
    accept_offer = get_input(value = 'Accept Admission Offer',disabled = is_admission_inactive)
    reject_offer = get_input(value = 'Decline Program Selection',id='valB',disabled = is_admission_inactive)
    ap_exp_is_men, ap_exp_is_hr = query.program.mentor_id_req,query.program.hr_cont_req
    is_prog_code_check = query.program.program_code == 'HC04'

    try:
        amount,fees,pgd=get_program_data(request,query,query.program)
        ap_exp = ApplicantExceptions.objects.get(applicant_email=query.login_email.email,
            program = query.program)
        ap_exp_is_men = not ap_exp.mentor_waiver
        ap_exp_is_hr = not ap_exp.hr_contact_waiver
        if ap_exp.transfer_program:
        	# commented since if there is transfer program then mentor and hr should be from program table
			#ap_exp_is_men, ap_exp_is_hr = ap_exp.transfer_program.mentor_id_req , ap_exp.transfer_program.hr_cont_req
			amount,fees,pgd = get_program_data(request,query,ap_exp.transfer_program)
			program_name = ap_exp.transfer_program.program_name

    except (
        ApplicantExceptions.DoesNotExist,
        ProgramLocationDetails.DoesNotExist,
        PROGRAM_FEES_ADMISSION.DoesNotExist,
        ) as e:
        #ap_exp_is_men, ap_exp_is_hr = (False, False)
        amount,fees,pgd=get_program_data(request,query,query.program)

    is_mentor_required = ap_exp_is_men
    is_hr_required = ap_exp_is_hr


    if request.method == 'POST':
        logger.info("{0} inside POST request".format(request.user.email))
        #m_hr_form = MentorHRDetails(request.POST)
        form = RejectForm(request.POST)
        if form.is_valid():
            logger.info("{0} POST request is valid".format(request.user.email))
            cs = CandidateSelection.objects.get(application = query)
            cs.accepted_rejected_by_candidate = timezone.localtime(timezone.now())
            cs.rejection_by_candidate_reason = form.cleaned_data['rejection_by_candidate_reason']
            cs.rejection_by_candidate_comments = form.cleaned_data['rejection_by_candidate_comments']
            query.application_status=settings.APP_STATUS[10][0]
            query.save()
            logger.info("{0} candidate status updated".format(request.user.email))
            cs.save()
            logger.info("{0} candidate selection table updated".format(request.user.email))
            return HttpResponseRedirect(
                reverse('registrationForm:applicantData'))

    else:
        logger.info("{0} inside GET request".format(request.user.email))
        form = RejectForm()

    logger.info("{0} ready to render".format(request.user.email))

    return render(request, 'accept_reject.html', {'form': form,
        'app_name':query.full_name,
        'program_name':program_name,
        'fees' :fees.fee_amount,
        'app_id':query.student_application_id,
        'dead_date':pgd.fee_payment_deadline_date,
        'hr_form':hr_form,
        'men_form':men_form,
        'is_mentor_required':is_mentor_required,
        'is_admission_inactive':is_admission_inactive,
        'is_hr_required':is_hr_required,
        'accept_offer':accept_offer,
        'reject_offer':reject_offer,
        'is_prog_code_check':is_prog_code_check,
        })

from bits_rest.models import *
@method_decorator([login_required, never_cache, check_emi_status], name='dispatch')
class AdmissionFeeView(TemplateView):
	template_name = 'registrations/pay_adm_fee_view.html'
	input_template = '<input class="btn btn-sm btn-primary" {} style="background-color: #228B22;">'
	model_sca = StudentCandidateApplication
	model_eloa = ExceptionListOrgApplicants
	model_pfa = PROGRAM_FEES_ADMISSION
	model_ae = ApplicantExceptions
	loan_amount = None
	get_object = lambda self: self.model_sca.objects.get(login_email=self.request.user)
	get_input = lambda self, **kwargs: format_html(self.input_template, flatatt(kwargs))

	def get(self, request, *args, **kwargs):
		self.object = self.get_object()
		self.program = self.get_program()
		self.emi_amount = self.model_pfa.objects.filter(
			Q(
				Q(program__zest_location=self.object.current_location)|
				Q(program__zest_location__isnull=True),
				fee_type=ZEST_FEE_TYPE,
				program__is_zest_emi_enable=True
			)|
			Q(
				Q(program__eduvanz_location=self.object.current_location)|
				Q(program__eduvanz_location__isnull=True),
				fee_type=EDUVANZ_FEE_TYPE, 
				program__is_eduvanz_emi_enable=True, 
			)|
			Q(
				fee_type=EZCRED_FEE_TYPE,
				program__is_ezcred_emi_enable=True,
			)|
			Q(
				fee_type=PROPELLD_FEE_TYPE,
				program__is_propelld_emi_enable=True
				),
			program=self.program, 
			latest_fee_amount_flag=True,
		)
		return super(AdmissionFeeView, self).get(request, *args, **kwargs)

	
	def get_program(self):
		try:
			ap_exp =self.model_ae.objects.get(
				applicant_email = self.request.user.email,
				program = self.object.program
			)
			return ap_exp.transfer_program or self.object.program
		except self.model_ae.DoesNotExist:
			return self.object.program


	def get_amount_and_available_payment_mod(self):
		try:
			amount, is_paytm = self.model_eloa.objects.get(
				Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
				employee_email=self.request.user.email,
				exception_type='2',
				program=self.program,
			).fee_amount, None

		except self.model_eloa.DoesNotExist:
			pfa = self.model_pfa.objects.get(
				program=self.program,
				latest_fee_amount_flag=True,
				fee_type='1'
			)
			amount, is_paytm = pfa.fee_amount, pfa.is_paytm_enable

		return amount, is_paytm
	

	def get_context_data(self, *args, **kwargs):
		context = super(AdmissionFeeView, self).get_context_data(*args, **kwargs)

		delete_initiated_application(self.object.login_email.email)
		is_adm_inactive = check_inactive_program_flag(self.get_object(),'active_for_admission_flag')
		zest_decline = emi_in_decline(self.object.login_email.email)
		zest_progress = emi_in_progress(self.object.login_email.email)
		eduvanz = get_eduvanz_inprogress(self.object.login_email.email) 
		ezcred = get_ezcred_inprogress(self.object.login_email.email)
		propelld = get_propelld_inprogress(self.object.login_email.email)
		propelld_new = get_propelld_innew(self.object.login_email.email)

		if zest_progress:
			zest_details = ZestEmiTransaction.objects.filter(application__login_email__email=self.object.login_email.email).latest('requested_on')
			context['zest_emi_link'] = zest_details.zest_emi_link

		ezcred_details = EzcredApplication.objects.filter(application__login_email__email=self.object.login_email.email).values()
		if ezcred_details:
			context['ezcred_link']=ezcred_details[0]['lead_link']
			context['lead_id'] = ezcred_details[0]['lead_id']
			context['ezcred_status'] = ezcred_details[0]['status']
		
		context['ezcred_progress'] = ezcred
		context['ezcred_declined'] = get_ezcred_declined(self.object.login_email.email)
		context['active_emi'] = eduvanz or zest_progress or ezcred  or propelld
		context['active_propelld'] = propelld_new

		context['ap_id'] = self.object.student_application_id
		context['ap_program'] = self.program.program_name
		context['ap_fee_amount'], context['is_paytm'] = self.get_amount_and_available_payment_mod()
		context['is_adm_inactive'] = is_adm_inactive
		
		context['zest_document_complete'] = emi_in_document_complete(self.object.login_email.email)
		context['zest_decline'] = zest_decline
		context['zest_incancellation'] = emi_in_cancellation(self.object.login_email.email)
		context['zest_progress'] = zest_progress

		context['eduvanz_declined'] = get_eduvanz_declined(self.object.login_email.email)
		context['eduvanz_progress'] = eduvanz

		propelld_details = PropelldApplication.objects.filter(application__login_email__email=self.object.login_email.email)
		if propelld_details:
			context['propelld_progress'] = propelld
			context['propelld_data'] = PropelldApplication.objects.filter(application__login_email__email=self.object.login_email.email).latest('created_on')


		
		emi_options = self.emi_amount.values_list('fee_type', flat=True)

		if ZEST_FEE_TYPE in emi_options:
			if 'zest_form' not in kwargs:
				context['zest_form'] = ZestForm(initial={
					'is_terms_and_condition_accepted': zest_progress,
					'amount_requested':self.emi_amount.filter(fee_type=ZEST_FEE_TYPE)[0].fee_amount
					},
					prefix='zest',
				) 

		if EDUVANZ_FEE_TYPE in emi_options:
			if 'eduvanz_form' not in kwargs:
				context['eduvanz_form'] = EduvanzApplicationForm(
					instance=eduvanz,
					initial={
						'is_terms_and_condition_accepted': eduvanz is not None, 
						'application': self.object, 
						'amount_requested':self.emi_amount.get(fee_type=EDUVANZ_FEE_TYPE).fee_amount
					},
					prefix='eduvanz',
				)

		if EZCRED_FEE_TYPE in emi_options:
			if 'ezcred_form' not in kwargs:
				context['ezcred_form'] = EduvanzApplicationForm(
					instance=ezcred,
					initial={
						'is_terms_and_condition_accepted': ezcred is not None,
						'application': self.object,
						'amount_requested':self.emi_amount.get(fee_type=EZCRED_FEE_TYPE).fee_amount
					},
					prefix='ezcred',
				)
		if PROPELLD_FEE_TYPE in emi_options:
			if 'propelld_form' not in kwargs:

				context['propelld_form'] = propelldApplicationForm(
					#instance=propelld,
					initial={
						'loan_amount':self.emi_amount.get(fee_type=PROPELLD_FEE_TYPE).fee_amount
					},
					prefix='propelld',
				)		
				
		return context 

@never_cache
@login_required
@require_POST
@admission_payment_exception_permission
@check_cross_payment
@applicant_status_permission(settings.APP_STATUS[9][0])
def redirect_page(request):
	"""Redirect to Payment Gateway Page."""
	logger.info("{0} invoked funct.".format(request.user.email))
	ctx = {}
	app = StudentCandidateApplication.objects.get(login_email=request.user)
	prog = app.program

	try:
		ap_exp = ApplicantExceptions.objects.get(applicant_email=request.user.email,
		program = prog)
		prog = ap_exp.transfer_program if ap_exp.transfer_program else prog
	except ApplicantExceptions.DoesNotExist:pass

	try:
		amount = ExceptionListOrgApplicants.objects.get(
			Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
			employee_email=request.user.email,
			exception_type='2',
			program=prog,
			).fee_amount

	except ExceptionListOrgApplicants.DoesNotExist:
		amount = PROGRAM_FEES_ADMISSION.objects.get(
			program=prog,latest_fee_amount_flag=True,
			fee_type='1').fee_amount

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
	ctx['requestType'] = 'ADM'

	headers = {'Content-type': 'application/json'}
	try:
		with transaction.atomic():
			logger.info("{0} Request payment gateway.".format(request.user.email))
			start_time = time.time()
			seq_count = MetaPayment.objects.filter(application = app,fee_type='1').count()
			meta_payment = MetaPayment.objects.create(application=app,
				req_pay_req_date =timezone.localtime(timezone.now()),
				req_json_data = json.dumps(ctx),
				sequence_number = seq_count + 1,
				order_id= ctx['merchantTxnRefNumber'],
				fee_type='1'
				)
			r = requests.post(
				settings.PAYMENT_URL,
				data=json.dumps(ctx),
				headers=headers)
			meta_payment.req_pay_status = r.status_code
			meta_payment.req_pay_res_date = timezone.localtime(timezone.now())
			meta_payment.save()
			logger.info("Request took {} seconds".format(time.time() - start_time))
			if r.status_code == 200:
				logger.info("{0} attempting to read responseMessage".format(request.user.email))
				a = r.json()
				meta_payment.req_json_return_data = a
				meta_payment.save()
				if len(a['responseMessage']) > 10:
					logger.info("{0} valid responseMessage".format(request.user.email))
					return HttpResponsePermanentRedirect(a['responseMessage'])
				else:
					logger.info("{0} responseMessage didn't satisfy condn.".format(request.user.email))
					return redirect(reverse('registrationForm:error-payment'))
			else:
				logger.info("{0} Connection status code other than 200.".format(request.user.email))
				return redirect(reverse('registrationForm:error-payment'))

	except ConnectionError,e:
		logger.error("{0} Connection error - {1}".format(request.user.email,e))
		return redirect(reverse('registrationForm:error-payment'))
	except IntegrityError,e:
		logger.error("{0} Integrity error - {1}".format(request.user.email,e))
		messages.error(request,'There was an error while payment.')
		return redirect(reverse('registrationForm:error-payment'))
	except Exception, e:
		logger.error("{0} Unexpected exception {1}".format(request.user.email,e))
		return redirect(reverse('registrationForm:error-payment'))

@login_required
def fee_download_page(request):
	"""Return transaction id, payment_date and payment_bank."""
	logger.info("{0} invoked funct.".format(request.user.email))
	query = StudentCandidateApplication.objects.get(login_email=request.user)
	logger.info("Download the Application Fee Status page for {}".format(
		request.user))

	q = ApplicationPayment.objects.get(application=query,fee_type='1')

	ctx = {}
	ctx['ap_id'] = query.application_id()
	ctx['ap_name'] = query.full_name
	ctx['ap_program'] = query.program.program_name
	ctx['ap_fee_amount'] = q.payment_amount
	
	ctx['roll_no'] = CandidateSelection.objects.get(application=query).student_id
	ctx['ap_pay_bank'] = q.payment_bank 
	ctx['ap_trans_io'] = q.transaction_id  
	ctx['ap_pay_d_t'] = q.payment_date
	ctx['roll_no'] = CandidateSelection.objects.get(application=query).student_id
	
	return render(request, 'adm-display.html', {"ctx": ctx})


@method_decorator(login_required,name='dispatch')
class Payfee (BasePDFTemplateView):
	template_name = "admission_fee_pdf.html"
	pdf_kwargs = {'encoding' : 'utf-8',}

	def get_context_data(self, **kwargs):
		query = StudentCandidateApplication.objects.get(login_email=self.request.user)
		try:
			q = ApplicationPayment.objects.get(application=query,fee_type='1')
		except ApplicationPayment.DoesNotExist:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
			
		context = super(Payfee, self).get_context_data(
			pagesize="A4", title="Pay fees", **kwargs)			
		context['ap_id'] = query.application_id()
		context['ap_name'] = query.full_name
		context['ap_program'] = query.program.program_name
		context['ap_fee_amount'] = q.payment_amount
		
		cs = CandidateSelection.objects.get(application=query)
		context['roll_no'] = cs.student_id
		context['ap_pay_bank'] = q.payment_bank
		context['ap_trans_io'] = q.transaction_id
		context['ap_pay_d_t'] = q.payment_date
		return context

@method_decorator(login_required,name='dispatch')
class OfferLetter (ol.OfferLetterUserView):pass

@login_required
@never_cache
@admission_payment_exception_permission
def pdf_redirect_direct_upload(request):
	return render(
		request, 'pdf_offer_letter_redirect.html',
		)

@login_required
@never_cache
def pdf_redirect_direct_upload1(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	app = StudentCandidateApplication.objects.get(login_email=request.user)
	pfa = PROGRAM_FEES_ADMISSION.objects.get(program=app.program,
								fee_type = '1',latest_fee_amount_flag=True)

	cs = CandidateSelection.objects.get(application = app,)
	with Lock('bits_student_id_lock'):
		student_id = student_id_generator(login_email=app.login_email.email)
		if cs.student_id:student_id = cs.student_id
		cs.student_id = student_id
		cs.save()

	return render(
		request, 'pdf_offer_letter_redirect.html',
		)

@login_required
def viewBitsRejectionReason(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	query = StudentCandidateApplication.objects.get(login_email=request.user)
	rej = CandidateSelection.objects.get(application = query)
	try:
		reasons =', '.join(cPickle.loads(str(rej.bits_rejection_reason)))
	except cPickle.UnpicklingError: reasons = []
	logger.info("Return Student Candidate Application data.")
	return render(request,'view_bits_rejection_reason.html',
		{ 'queryResult': query,'rej': rej,'reasons':reasons })


@method_decorator(login_required,name='dispatch')
class PreviewOfferLetter(BasePDFTemplateView):
	"""Preview Offer Letter template view."""
	template_name = "offer_letter_pdf.html"

	def get_program_data(self,app,prog,context):
		amount = None
		context['courseL'] = FirstSemCourseList.objects.filter(
					program=prog,
					admit_year=app.admit_year, 
					active_flag=True
				)
		context['pgFeeAdm'] = PROGRAM_FEES_ADMISSION.objects.get(
				program =prog,
				fee_type='1',latest_fee_amount_flag=True
			)
		context['appfees'] = PROGRAM_FEES_ADMISSION.objects.get(
				program =prog,
				fee_type='2',
				latest_fee_amount_flag=True
			).fee_amount
			
		try:
			amount = ExceptionListOrgApplicants.objects.get(
				Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
				application=app,
				exception_type='2',
				program=prog,
				).fee_amount

		except ExceptionListOrgApplicants.DoesNotExist:
			amount = context['pgFeeAdm'].fee_amount	

		pld = ProgramLocationDetails.objects.get(
			program=prog,
			location = app.current_location
		)
		return amount,pld



	def get_context_data(self,app_id, **kwargs):
		context = super(PreviewOfferLetter, self).get_context_data(
			pagesize="A4", title="Offer letter", **kwargs)
		app = StudentCandidateApplication.objects.get(
			student_application_id=app_id
			)
		cs = CandidateSelection.objects.get(application=app)
		template_name = app.program.offer_letter_template
		program_name = cs.application.program.program_name
		try:
			ap_exp = ApplicantExceptions.objects.get(applicant_email=app.login_email.email,
				program = app.program)
			template_name = ap_exp.offer_letter or template_name
			amount,pld=self.get_program_data(app,app.program,context)
			if ap_exp.transfer_program:
				amount,pld=self.get_program_data(app,ap_exp.transfer_program,context)
				template_name = (
					ap_exp.offer_letter or 
					ap_exp.transfer_program.offer_letter_template or 
					app.program.offer_letter_template
				)
				program_name = ap_exp.transfer_program.program_name
				
			
		except (
			ApplicantExceptions.DoesNotExist, 
			ProgramLocationDetails.DoesNotExist,
			PROGRAM_FEES_ADMISSION.DoesNotExist,
			) as e:
			amount,pld=self.get_program_data(app,app.program,context)

		context['cs'] = cs.__dict__
		context['cs']['application'] = cs.application
		context['cs']['fee_payment_deadline_dt'] = pld.fee_payment_deadline_date
		context['cs']['orientation_dt'] = pld.orientation_date
		context['cs']['lecture_start_dt'] = pld.lecture_start_date
		context['cs']['orientation_venue'] = pld.orientation_venue
		context['cs']['lecture_venue'] = pld.lecture_venue
		context['cs']['admin_contact_person'] = pld.admin_contact_person
		context['cs']['acad_contact_person'] = pld.acad_contact_person
		context['cs']['admin_contact_phone'] = pld.admin_contact_phone
		context['cs']['acad_contact_phone'] = pld.acad_contact_phone
		context['cs']['adm_fees'] = amount

		
		adm_fees = amount
		context['admmf'] = settings.ADMISSION_FEES

		context['semFees'] = adm_fees - 16500

		context['program_name'] = program_name

		if template_name:
			self.template_name = template_name

		return context


@login_required
@specif_viewer_redirect_to('application_specific:specific-offer-letter')
def offerLetterRedirect(request):
	return redirect(reverse('registrationForm:offer-letter-pdf'))


@login_required
@never_cache
def offerReviewerLetterRedirect(request,app_id):
	query = StudentCandidateApplication.objects.get(student_application_id=app_id)
	s_e_d = ProgramDomainMapping.objects.filter(Q(email = query.login_email)|
		Q(email_domain__iexact =  query.login_email.email.split('@')[1])).exists()
	if s_e_d:return redirect(reverse('registrationForm:offer-letter-specific-pdf',
		kwargs={'app_id':app_id}))
	else:
		return redirect(reverse('registrationForm:offer-letter-non-specific-pdf',
			kwargs={'app_id':app_id}))

@login_required
@never_cache
def archivedOfferReviewerLetterRedirect(request,pk):
	query = StudentCandidateApplicationArchived.objects.get(pk=pk)
	s_e_d = ProgramDomainMapping.objects.filter(Q(email = query.login_email)|
		Q(email_domain__iexact =  query.login_email.split('@')[1])).exists()
	if s_e_d:return redirect(reverse('registrationForm:archived-offer-letter-specific-pdf',
		kwargs={'pk':pk}))
	else:
		return redirect(reverse('registrationForm:archived-offer-letter-non-specific-pdf',
			kwargs={'pk':pk}))


def get_prog_context(app,prog,context):

	context['courseL'] = FirstSemCourseList.objects.filter(
		program = prog,
		admit_year=app.admit_year,active_flag=True
		)
	context['pgFeeAdm'] = PROGRAM_FEES_ADMISSION.objects.get(
		program =prog,
		fee_type='1',latest_fee_amount_flag=True
		)
	context['appfees'] = PROGRAM_FEES_ADMISSION.objects.get(
		program =prog,
		fee_type='2',
		latest_fee_amount_flag=True
		).fee_amount

@method_decorator(login_required,name='dispatch')
class OfferLetterReviewerNonSpecific(ol.OfferLetterView):pass 
	
@method_decorator(login_required,name='dispatch')
class OfferLetterReviewerSpecific(ol.OfferLetterView):pass
	
@method_decorator(login_required,name='dispatch')
class ArchivedOfferLetterReviewerSpecific(ol.OfferLetterArchiveView):pass
	
@method_decorator(login_required,name='dispatch')
class ArchivedOfferLetterReviewerNonSpecific(ol.OfferLetterArchiveView):pass


@method_decorator([login_required, reviewer_permission,],name='dispatch')
class RCSV(BaseRCSV):
	app_status=[(settings.APP_STATUS[12][0],),(settings.APP_STATUS[18][0],),(settings.APP_STATUS[19][0],)]

@login_required
@require_http_methods(["POST","GET"])
@reviewer_permission
def view_short_rej_list(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	CSFormset = modelformset_factory(
		CandidateSelection,
		form = ShortRejForm, extra = 0, can_delete = False,
		)
   
	hid = None if 'filter_list' in request.POST else request.POST.get('hidden_id',None)
	if 'escalate' in request.POST:
		cs_red = []
		ids =  list(set(int(x) for x in json.loads(hid)))  if hid else []

		cs_formset = CSFormset(request.POST, request.FILES,prefix='CSForm',)
		if cs_formset.is_valid():

			for f in cs_formset:
				sca = f.cleaned_data['application']
				if not sca.application_status == settings.APP_STATUS[15][0] and \
				 f.cleaned_data['es_to_su_rev']:
					ids.append(sca.id)
	
			cs_red = CandidateSelection.objects.filter( application_id__in = ids ).distinct() 

			cs_formset_red = CSFormset(prefix="CSForm_red",queryset=cs_red)
			es_comment = EscCommentForm()
			return render(request, 'offer_status_esc.html',
				{'cs_formset_red':cs_formset_red,
				'es_comment':es_comment
				})

	else:
		query = StudentCandidateApplication.objects.filter(
				application_status__in=[
					settings.APP_STATUS[6][0],
					settings.APP_STATUS[8][0],
					settings.APP_STATUS[15][0],
					settings.APP_STATUS[9][0],
					settings.APP_STATUS[11][0],

					])

		pg = request.POST.get('programs',None)
		query = query.filter(program = pg) if pg else query

		loc = request.POST.get('locations',None)
		query = query.filter(current_location=loc) if loc else query

		admit_batch = request.POST.get('admit_batch',None)
		query = query.filter(admit_batch=admit_batch) if admit_batch else query

		search = request.POST.get('search',None)

		query=query.filter(
			reduce(operator.and_, (
				Q(student_application_id__icontains = item)|
				Q(full_name__icontains = item)|
				Q(created_on_datetime__icontains = item)|
				Q(program__program_name__icontains = item)|
				Q(application_status__icontains = item)|
				Q(admit_batch__icontains = item)
				for item in search.split()))
			) if search else query

		cs = CandidateSelection.objects.filter(application__in=query) 
		pg_app = StudentCandidateApplication.objects.filter(id__in=json.loads(hid)).distinct() \
		 if hid else StudentCandidateApplication.objects.none() 
		data = {'programs': pg, 
		'locations': loc, 
		'hidden_id': hid,
		'admit_batch':admit_batch,
		'search': search }

		paginator = Paginator(cs, 10)
		page = request.POST.get('page', 1)

		try:  
			objects = paginator.page(page)  
		except PageNotAnInteger:  
			objects = paginator.page(1)  
		except EmptyPage:  
			objects = paginator.page(paginator.num_pages)

		page_query = CandidateSelection.objects.filter(id__in=[obj.id for obj in objects])
		

		cs_formset = CSFormset(
				prefix='CSForm',
				queryset=page_query,
				)

	return render(request, 'view_short_rej_list.html',
		{
		'form1': ExtraForm(data),
		'cs_formset':cs_formset,
		'hidden_id' : pg_app,
		'objects': objects,
		'total':cs.count(),

		 })

@login_required
@require_POST
def submit_osc_list(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	CSFormset = modelformset_factory(
		CandidateSelection,
		form = ShortRejForm, extra = 0, can_delete = False,)
	cs_formset_red = CSFormset(request.POST,prefix="CSForm_red",)
	es_comment = EscCommentForm(request.POST)
	if cs_formset_red.is_valid() and es_comment.is_valid():
		comment = es_comment.cleaned_data['es_comments']

		for f in cs_formset_red:
			application = f.cleaned_data['application']
			cs = CandidateSelection.objects.get( application = application )
			cs.prior_status = cs.application.application_status
			cs.application.application_status = settings.APP_STATUS[15][0]
			cs.es_com = comment
			cs.es_to_su_rev = True
			cs.su_rev_app = False
			cs.es_to_su_rev_dt =timezone.localtime(timezone.now())
			cs.application.save()
			cs.save()
		return  redirect(reverse('registrationForm:review-applicant-data'))


	return render(request, 'offer_status_esc.html',
		{'cs_formset_red':cs_formset_red,
		'es_comment':es_comment})


@login_required
@require_http_methods(["POST","GET"])
@reviewer_permission
def prog_change_list(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	hid = None if 'filter_list' in request.POST else request.POST.get('hidden_id',None)
	
	CSFormset = modelformset_factory(StudentCandidateApplication,
		form = ProgramRejForm,extra=0, 
		can_delete=False)

	if 'escalate' in request.POST:
		cs_red =[]
		cs_formset = CSFormset(request.POST, request.FILES, prefix='CSForm')  
		ids = json.loads(hid)  if hid else {}

		if cs_formset.is_valid():
			for f in cs_formset:
				sca = f.cleaned_data['id'] 
	
				if not sca.application_status == settings.APP_STATUS[15][0] and \
				f.cleaned_data['es_to_su_rev'] and f.cleaned_data['program'] :
					ids[str( sca.id )] = str( f.cleaned_data['program'].id )

			cs_red =[ {'app_id':int(k),'program':int(v)} for k,v in ids.items() ]

			CSEscFormset = formset_factory(ProgramRejEscForm,extra=0, can_delete=False)
			cs_formset_red = CSEscFormset(prefix="CSForm_red",initial=cs_red)
			es_comment = EscCommentForm()

			return render(request, 'prog_change_esc.html',
				{'cs_formset_red':cs_formset_red,
				'es_comment':es_comment})

	else:
		
		search = request.POST.get('search',None)
		pg = request.POST.get('programs',None)
		loc = request.POST.get('locations',None)
		search = request.POST.get('search',None)
		pg_app = json.loads(hid) if hid else {}
		eloa = ELOA.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),).values_list('employee_email').distinct()
		query = StudentCandidateApplication.objects.filter(
				application_status__in=[
					settings.APP_STATUS[0][0],
					settings.APP_STATUS[1][0],
					settings.APP_STATUS[4][0],
					settings.APP_STATUS[14][0],
					settings.APP_STATUS[5][0],
					settings.APP_STATUS[6][0],
					settings.APP_STATUS[11][0],
					settings.APP_STATUS[15][0],
					settings.APP_STATUS[13][0],
					settings.APP_STATUS[3][0],
					settings.APP_STATUS[9][0],
					]).exclude(
					login_email__email__in = eloa
					)

		query = query.filter(program = pg) if pg else query
		query = query.filter(current_location=loc) if loc else query
		
		query=query.filter(
			reduce(operator.and_, (
				Q(student_application_id__icontains = item)|
				Q(full_name__icontains = item)|
				Q(created_on_datetime__icontains = item)|
				Q(program__program_name__icontains = item)|
				Q(application_status__icontains = item)
				for item in search.split()))
			) if search else query

		data = { 'programs': pg,
		 'locations': loc,
		 'hidden_id': hid,
		 'search': search }

		paginator = Paginator(query, 10)
		page = request.POST.get('page', 1)

		try:  
			objects = paginator.page(page)  
		except PageNotAnInteger:  
			objects = paginator.page(1)  
		except EmptyPage:  
			objects = paginator.page(paginator.num_pages)

		page_query = StudentCandidateApplication.objects.filter(id__in=[obj.id for obj in objects])

		cs_formset = CSFormset(
				prefix='CSForm',
				queryset=page_query)

	return render(request, 'prog_change_list.html',
		{
		'form1': ExtraForm(data),
		'cs_formset':cs_formset,
		'hidden_id' : pg_app,
		'objects': objects,
		'total':query.count(),
		'esc_status':settings.APP_STATUS[15][0],
		 })

@login_required
@require_POST
def submit_pc_list(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	CSFormset = formset_factory(ProgramRejEscForm,extra=0, can_delete=False)
	cs_formset_red = CSFormset(request.POST,prefix="CSForm_red",)
	es_comment = EscCommentForm(request.POST)
	
	if cs_formset_red.is_valid() and es_comment.is_valid():
		comment = es_comment.cleaned_data['es_comments']

		for f in cs_formset_red:
			pg =Program.objects.get(id=int(f.cleaned_data['program']))
			sca = StudentCandidateApplication.objects.get(
				id =int(f.cleaned_data['app_id'])
				)
			cs, created = CandidateSelection.objects.get_or_create(application = sca,)
			cs.prior_status = cs.application.application_status
			cs.application.application_status = settings.APP_STATUS[15][0]
			cs.es_com = comment
			cs.es_to_su_rev = True
			cs.es_to_su_rev_dt =timezone.localtime(timezone.now())
			cs.new_sel_prog = pg
			cs.prog_ch_flag = True
			cs.su_rev_app = False
			cs.application.save()
			cs.save()
		return  redirect(reverse('registrationForm:review-applicant-data'))

@login_required
def acceptOffer_later(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	cs = CandidateSelection.objects.get(application__login_email__email = request.user.email)
	try:
		ap_exp = ApplicantExceptions.objects.get(applicant_email=cs.application.login_email.email,
			program = cs.application.program)

		ap_exp_is_men = ap_exp.mentor_waiver
		ap_exp_is_hr = ap_exp.hr_contact_waiver

	except ApplicantExceptions.DoesNotExist:
		ap_exp_is_men, ap_exp_is_hr = (False, False)

	is_mentor_required = not ap_exp_is_men and cs.application.program.mentor_id_req
	is_hr_required = not ap_exp_is_hr and cs.application.program.hr_cont_req
	is_invalid_form = False

	if request.method == "POST":
		logger.info("{0} inside POST request".format(request.user.email))
		# m_hr_form = MentorHRDetails(request.POST)
		hr_form = HRDetails(request.POST)
		men_form = MentorDetails(request.POST)

		if is_mentor_required:
			if men_form.is_valid():
					logger.info("{0} POST request is valid".format(request.user.email))
					cs.m_name = men_form.cleaned_data['m_name']
					cs.m_des = men_form.cleaned_data['m_des']
					cs.m_mob_no = men_form.cleaned_data['m_mob_no']
					cs.m_email = men_form.cleaned_data['m_email']
			else:is_invalid_form = True

		if is_hr_required:
			if hr_form.is_valid():
					logger.info("{0} POST request is valid".format(request.user.email))
					cs.hr_cont_name = hr_form.cleaned_data['hr_cont_name']
					cs.hr_cont_des = hr_form.cleaned_data['hr_cont_des']
					cs.hr_cont_mob_no = hr_form.cleaned_data['hr_cont_mob_no']
					cs.hr_cont_email = hr_form.cleaned_data['hr_cont_email']
			else:is_invalid_form = True

		if not is_invalid_form:
			logger.info("{0} candidate selection table updated".format(request.user.email))
			cs.save()
			return redirect(reverse('registrationForm:applicantData'))

	else:
		logger.info("{0} inside GET request".format(request.user.email))
		hr_form = HRDetails()
		men_form = MentorDetails()
	logger.info("{0} ready to render".format(request.user.email))

	return render(request, 'mentor_hr_details.html', 
			{'hr_form':hr_form,
			'men_form':men_form,
			'is_mentor_required':is_mentor_required,
			'is_hr_required':is_hr_required})



@login_required
@require_GET
@reviewer_permission
def esc_applicants(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	search=request.GET.get("user",'') 

	query = ApplicationDocument.objects.annotate(finalName=F('application__full_name'))

	
	query=query.filter(
		Q(rejected_by_bits_flag= True)|
		Q(reload_flag= True)|(
			Q(exception_notes__isnull=False) & 
			~Q(exception_notes="")
			))

	query=query.filter(
		reduce(operator.and_, (
			Q(finalName__icontains = item)|
			Q(exception_notes__icontains = item)|
			Q(rejection_reason__reason__icontains = item)|
			Q(application__program__program_name__icontains = item)|
			Q(application__student_application_id__icontains = item)|
			Q(document__document_name__icontains = item)
			for item in search.split())),) if search else query

	query=query.filter(
		application__application_status__in=[
		settings.APP_STATUS[2][0],
		settings.APP_STATUS[3][0],
		settings.APP_STATUS[4][0]
		],
		)

	pg = request.GET.get('programs',None)
	query = query.filter(application__program = pg) if pg else query

	st = request.GET.get('status',None)
	query = query.filter(application__application_status = st) if st else query

	if 'escalate' in request.GET:     
		esc_csv_value =['application__student_application_id',
		'finalName',
		'application__created_on_datetime',
		'application__program__program_code',
		'application__program__program_name',
		'application__application_status',
		'document__document_name',
		'rejection_reason__reason',
		'exception_notes',
		]

		esc_csv_header={'application__student_application_id':'Application ID',
		'finalName':'Name',
		'application__created_on_datetime':'Applied On',
		'application__program__program_code':'Program Code',
		'application__program__program_name':'Program',
		'application__application_status':'Current Status',
		'document__document_name':'Document Name',
		'rejection_reason__reason':'Rejection Reason',
		'exception_notes':'Exception Comments',
		}

		esc_field_serializer_map={'application__created_on_datetime':
		(lambda x: (x or '') and timezone.localtime(x).strftime("%d/%m/%Y")), }

		query=query.values(*esc_csv_value)
		head,ser_map,f_order = esc_csv_header,esc_field_serializer_map,esc_csv_value    
		filename = 'esc_applicant'

		return render_to_csv_response(query,append_datestamp=True,
			field_header_map=head, field_serializer_map=ser_map,
			field_order=f_order,filename=filename,)
	
	data = {'programs':pg, 'status':st,}

	return render(request, 'esc_applicants.html',
		{'queryResult':query,
		'form1':ProgramStatusForm(data),
		})
# View to show list of escalated applicants ends...  



@login_required
@require_POST
@reviewer_permission
@csrf_exempt
def pgram_change_ajax_validate(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	if request.is_ajax():
		pg_id = request.POST.get('pg')
		s_id = request.POST.get('sca')
		sca = StudentCandidateApplication.objects.get(id=int(s_id))
		program = Program.objects.get( id = int(pg_id) )

		p_ad = ApplicationPayment.objects.filter(application = sca , fee_type = '1')
		p_ap = ApplicationPayment.objects.filter(application = sca , fee_type = '2')

		try:

			pf_ap_old_pg = PROGRAM_FEES_ADMISSION.objects.get(program = sca.program,
				# admit_year = sca.admit_year,
				fee_type = '2',
				latest_fee_amount_flag = True)
			pf_ap_new_pg = PROGRAM_FEES_ADMISSION.objects.get(program = program,
				# admit_year = sca.admit_year,
				fee_type = '2',
				latest_fee_amount_flag = True)

			pf_ad_old_pg = PROGRAM_FEES_ADMISSION.objects.get(program = sca.program,
				# admit_year = sca.admit_year,
				fee_type = '1',
				latest_fee_amount_flag = True)

			pf_ad_new_pg = PROGRAM_FEES_ADMISSION.objects.get(program = program,
				# admit_year = sca.admit_year,
				fee_type = '1',
				latest_fee_amount_flag = True)
		except PROGRAM_FEES_ADMISSION.DoesNotExist ,e:
			return JsonResponse({'e':str(e)}) 

		if not pf_ap_old_pg.fee_amount == pf_ap_new_pg.fee_amount:
			return JsonResponse({'e':'application fee doesnt match'}) 

		if p_ad.exists() and not pf_ad_old_pg.fee_amount == pf_ad_new_pg.fee_amount:
			return JsonResponse({'e':'admission fee doesnt match'}) 

		return JsonResponse({ 'e': 0})

				

@login_required
@require_POST
@reviewer_permission
@csrf_exempt
def offer_change_list_ajax(request):
	logger.info("{0} invoked funct.".format(request.user.email))
	if request.is_ajax():
		search = request.POST.get('search',None)
		pg = request.POST.get('programs',None)
		loc = request.POST.get('locations',None)

		query = StudentCandidateApplication.objects.filter(
				application_status__in=[
					settings.APP_STATUS[6][0],
					settings.APP_STATUS[8][0],
					settings.APP_STATUS[15][0],
					settings.APP_STATUS[9][0],
					settings.APP_STATUS[11][0],

					])
		
		query = query.filter(program = pg) if pg else query
		query = query.filter(current_location=loc) if loc else query
		cs = CandidateSelection.objects.filter(application__in=query)
		cs = cs.annotate(finalName = F('application__full_name'),
			pg_name = F('application__program__program_name'),
			created_on_datetime = F('application__created_on_datetime'),
			app_id = F('application__id'),
			student_application_id = F('application__student_application_id'),
			application_status = F('application__application_status'),
			)

		cs = cs.filter(
			reduce(operator.and_, (
				Q(student_application_id__icontains = item)|
				Q(finalName__icontains = item)|
				Q(created_on_datetime__icontains = item)|
				Q(pg_name__icontains = item)|
				Q(application_status__icontains = item)
				for item in search.split()))
			) if search else cs

		paginator = Paginator(cs, 10)
		objects = paginator.page(1)
		sorted_cs = cs.values(
				'student_application_id',
				'app_id','finalName',
				'created_on_datetime',
				'pg_name','id',
				'application_status',
				'es_to_su_rev')[:10]


		return JsonResponse({ 
			'app': json.dumps(list(sorted_cs), cls=DjangoJSONEncoder),
			'count':cs.count(),
			'per_page':10 if cs.count() > 10 else cs.count(),
			'locations':loc if loc else '',
			'programs':pg if pg else '',
			'search':search if search else '',
			'total_pages':objects.paginator.num_pages,
		})


@login_required
@require_POST
@reviewer_permission
@csrf_exempt
def prog_change_list_ajax(request):
	logger.info("{0} invoked funct.".format(request.user.email))

	if request.is_ajax():
		search = request.POST.get('search',None)
		pg = request.POST.get('programs',None)
		loc = request.POST.get('locations',None)
		eloa = ELOA.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),).values_list(
			'employee_email').distinct()
		query = StudentCandidateApplication.objects.filter(
			application_status__in=[
				settings.APP_STATUS[0][0],
				settings.APP_STATUS[1][0],
				settings.APP_STATUS[4][0],
				settings.APP_STATUS[14][0],
				settings.APP_STATUS[5][0],
				settings.APP_STATUS[6][0],
				settings.APP_STATUS[11][0],
				settings.APP_STATUS[15][0],
				settings.APP_STATUS[13][0],
				settings.APP_STATUS[3][0],
				settings.APP_STATUS[9][0],
				]).exclude(
				login_email__email__in = eloa
				)

		query = query.filter(program = pg) if pg else query
		query = query.filter(current_location=loc) if loc else query

		query = query.annotate(
			finalName = F('full_name'),
			pg_name = F('program__program_name'),
			pg_cd = F('program__program_code'),
			pg_typ = F('program__program_type'),

		)

		query=query.filter(
			reduce(operator.and_, (
				Q(student_application_id__icontains = item)|
				Q(finalName__icontains = item)|
				Q(created_on_datetime__icontains = item)|
				Q(pg_name__icontains = item)|
				Q(pg_cd__icontains = item)|
				Q(pg_typ__icontains = item)|
				Q(application_status__icontains = item)
				for item in search.split())) 
			) if search else query

		paginator = Paginator(query, 10)
		objects = paginator.page(1)
		sorted_cs = query.values(
				'student_application_id',
				'finalName',
				'created_on_datetime',
				'pg_name','id',
				'application_status',
				'pg_cd','pg_typ',
				)[:10]
		
		list_of_pg = {}
		pg_list = Program.objects.filter(active_for_applicaton_flag = True)
		for x in sorted_cs:
			sca = StudentCandidateApplication.objects.get(id = x['id'])
			


			tmp = pg_list.exclude(
				program_code = sca.program.program_code
				)
			list_of_pg[str(sca.id)] = json.dumps(list(tmp.values('id',
				'program_code','program_name','program_type')), cls = DjangoJSONEncoder)

		return JsonResponse({ 
			'app': json.dumps(list(sorted_cs), cls = DjangoJSONEncoder),
			'list_of_pg': json.dumps(list_of_pg),
			'count':query.count(),
			'per_page':10 if query.count() > 10 else query.count(),
			'locations':loc if loc else '',
			'programs':pg if pg else '',
			'search':search if search else '',
			'total_pages':objects.paginator.num_pages,

		})


@login_required
@reviewer_permission
@man_id_wav_chk
@never_cache
def rev_manID_gen(request,app_id):
	logger.info("{0} invoked funct.".format(request.user.email))
	app = StudentCandidateApplication.objects.get(id=int(app_id))
	pfa = PROGRAM_FEES_ADMISSION.objects.get(program=app.program,
								fee_type = '1',latest_fee_amount_flag=True)
	cs = CandidateSelection.objects.get(application = app,)
	with Lock('bits_student_id_lock'):
		student_id = student_id_generator(login_email = app.login_email.email)
		if cs.student_id:student_id = cs.student_id
		cs.student_id = student_id
		cs.save()

	return redirect(reverse('registrationForm:applicantData'))


class NclDataView(FeedDataView):

	token = ncl_paging().token

	def get_queryset(self):
		query = super(NclDataView, self).get_queryset()
		pg1 = int(self.kwargs.get('pg',None))
		pg_type = self.kwargs.get('p_type',None)
		batch = self.kwargs.get('ab')
		query = query.filter( application__program=pg1 ) if pg1 and pg1 > 0 else query
		query = query if batch=='0' or not batch else query.filter(application__admit_batch=batch)
		query = query.filter(application__program__program_type=pg_type ) if pg_type and not pg_type == '0' else query

		query = query.exclude(
			Q(student_id__isnull=True)|Q(student_id='')).annotate(
			app_id = Case(
				When(new_application_id=None,
					then=Concat('application__student_application_id',Value(' '))),
				default=Concat('new_application_id',Value(' ')),
				output_field=CharField(),
				),
			finalName = F('application__full_name'),
			applied_on = F('application__created_on_datetime'),
			pg_name = Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
			sca_id = F('application__id'),
			admit_batch = F('application__admit_batch'),
			)

		return query


# @staff_member_required
@require_GET
def sdms_progress(request):
	if request.is_ajax():

		if 'job' in request.GET:
			job_id = request.GET['job']
		else:
			return JsonResponse({'message':None,'status':'FAILURE'})
		job = AsyncResult(job_id)
		try :
			message = job.result['message']
		except : 
			message ='processing...'

		print 'Message............',message
		if job.status == 'SUCCESS':
			request.session['synced_ids_job_result'] = job.result
			request.session['synced_ids'] = job.result['synced_list']
			job.revoke()
		return JsonResponse({'message':message,'status':job.status})

	else:
		return render(request,'sdms_progress.html',{
			'job_id':request.GET['job'] if 'job' in request.GET else 0,
			})


@login_required
@reviewer_permission 
def name_change_list(request):
	logger.info("{0} invoked funct.".format(request.user.email))

	query = CandidateSelection.objects.exclude(
		Q(student_id__isnull=True)|Q(student_id='')).annotate(
		app_id = Case(
			When(new_application_id=None,
				then=Concat('application__student_application_id',Value(' '))),
			default=Concat('new_application_id',Value(' ')),
			output_field=CharField(),
			),
		finalName = F('application__full_name'),
		applied_on = F('application__created_on_datetime'),
		pg_name = Concat('application__program__program_name',Value(' - '),
				'application__program__program_code',Value(' ('),
				'application__program__program_type',Value(')')),
		sca_id = F('application__id'),
		admit_batch = F('application__admit_batch'),

		)
	pg1 = request.POST.get('programs',None)
	ptype = request.POST.get('pg_type', None)
	batch = request.POST.get('admit_batch',None)
	query = query.filter(application__program=pg1) if pg1 else query
	query = query.filter(application__program__program_type=ptype) if ptype else query
	query = query.filter(application__admit_batch=batch) if batch else query

	data={'programs':pg1,'admit_batch':batch,'pg_type':ptype}
	if request.session.has_key('synced_ids_job_result'):
		data = request.session['synced_ids_job_result']['form_data']
		pg1 = data['programs']
		batch = data['admit_batch']
		ptype = data['pg_type']
	SCATable = ncl_paging(programs=pg1,admit_batch=batch,pg_type=ptype)
	table = SCATable(query)
	sync_data = None
	sync_error = False
	sync_success = False

	if 'sync' in request.POST:
		user_name = request.user
		job= sdms_sync_task.delay(programs=pg1,program_type=ptype,admit_batch=batch,user_name=user_name)
		return redirect(reverse('reviewer:sdms_progress') + '?job=' + job.id)
	if 'unsynceddetails' in request.POST:
		user_name = request.user
		job= sdms_sync_task.delay(programs=pg1,program_type=ptype,admit_batch=batch,user_name=user_name,unsynced_data=True)
		return redirect(reverse('reviewer:sdms_progress') + '?job=' + job.id)
	if request.session.has_key('synced_ids_job_result'):
		sync_success = request.session['synced_ids_job_result']['sync_success']
		sync_error = request.session['synced_ids_job_result']['sync_error']
		del request.session['synced_ids_job_result']
	else:
		sync_success = False
		sync_error = False

	return render(request, 'name_change_list.html',
		{'queryResult':query,
		'prog_form':Ncl_Form(data),
		'batch_form':Ncl_Form(data),
		'ptype_form':Ncl_Form(data),
		'table' : table,
		'sync_success': sync_success,
		'sync_error': sync_error,
		})

@login_required
@reviewer_permission 
def name_change_form(request,application_id):

	query = CandidateSelection.objects.get(
		application__id=application_id)
	doc = ApplicationDocument.objects.filter(
		application__id=application_id,document__n_v_flag=True)
	form = NameChangeForm(instance = query)
	sync_data = None

	if 'save' in request.POST:
		form = NameChangeForm(request.POST,instance = query)
		if form.is_valid():
			query.name_verified_on = timezone.localtime(timezone.now())
			query.name_verified_by = request.user.email
			query.save()
			form.save()
			return redirect(reverse('reviewer:name-change-list'))

	elif 'sync'in request.POST:
		try:
			sync_data, a = name_verify_api(CandidateSelection.objects.filter(
				application__id=application_id),request.user)
		except Exception as e:
			sync_data = [{'id_no': query.student_id,
			 'sdms_status_code': 400,
			 'sdms_error':str(e)},]
		else:
			for x in sync_data:
				if x['sdms_status_code'] == 200:
					cs = CandidateSelection.objects.get(student_id = x['id_no'])
					cs.dps_flag = True
					cs.dps_datetime = timezone.localtime(timezone.now())
					cs.save()
					
	return render(request, 'name_change_form.html',
		{'query':query,
		'doc':doc,
		'prog_form':form,
		'api_op': sync_data,
		})

@method_decorator([login_required,reviewer_permission], name='dispatch')
class SendConfirmationRejectEmail(View):
	sca = None
	cs= None
	email_template = 'registrations/applicant_offer_accept_reject_mail.html'
	subject = 'Application Evaluation Completed - BITS Pilani Work Integrated Learning Programmes'
	from_email = '<{}>'.format(settings.FROM_EMAIL)
	success_url = reverse_lazy('registrationForm:review-applicant-data')
	app_model = StudentCandidateApplication
	cs_model = CandidateSelection
	get_sca = lambda self, pk: self.app_model.objects.get(pk=int(pk))
	get_cs = lambda self, app: self.cs_model.objects.get(application=app)
	get_success_url = lambda self: JsonResponse({'bits_success':200})

	def send_evaluation_mail(self):
		email_kwargs = {
			'html_message' : render_to_string(self.email_template,
				{
					'app_name': self.sca.full_name.strip().split()[0],
					'program':self.sca.program.program_name
				}
			),
			'fail_silently':True
		}
		email_args = [self.subject, email_kwargs['html_message'], self.from_email, [self.sca.email_id],]
		return send_mail( *email_args, **email_kwargs)

	def selection_details(self):
		try:
			template_name = self.sca.program.offer_letter_template or None
			ap_exp = ApplicantExceptions.objects.get(application=self.sca, program =self.sca.program)
			template_name = ap_exp.offer_letter or template_name
			if ap_exp.transfer_program:
				template_name = (
					ap_exp.offer_letter or 
					ap_exp.transfer_program.offer_letter_template or 
					self.sca.program.offer_letter_template
				)
		except ApplicantExceptions.DoesNotExist:pass

		try:
			pld = ProgramLocationDetails.objects.get(program=self.sca.program,location=self.sca.current_location)
			self.cs.fee_payment_deadline_dt = pld.fee_payment_deadline_date

		except ProgramLocationDetails.DoesNotExist:pass

		self.cs.offer_letter_template = template_name
		self.sca.application_status = settings.APP_STATUS[6][0]

	def rejection_details(self):
		self.cs.student_id = None
		self.sca.application_status = settings.APP_STATUS[8][0]

	def post(self, request, *args, **kwargs):
		app_id = request.POST['app_id']
		do_status = request.POST['do_status']
		self.sca = self.get_sca(int(app_id))
		self.cs = self.get_cs(self.sca)
		
		self.send_evaluation_mail()

		if request.is_ajax():
			if do_status == 'SHORT': self.selection_details()
			elif do_status == 'REJ': self.rejection_details()

		self.cs.offer_reject_mail_sent = timezone.localtime(timezone.now())
		self.cs.save()
		self.sca.save()
		return self.get_success_url()


class SendDobDetails(UpdateView):
	
	model = StudentCandidateApplication
	form_class=DobForm

	def get_success_url(self):
		return reverse_lazy('registrationForm:review_application_details', 
				kwargs={'application_id':self.get_object().pk})

@method_decorator([login_required, reviewer_permission], name='dispatch')
class SendPreConfirmSelRejEmail(BaseSendPreConfirmSelRejEmail):
	success_url = reverse_lazy('registrationForm:review-applicant-data')