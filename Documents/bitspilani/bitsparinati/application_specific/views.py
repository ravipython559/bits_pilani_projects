import datetime
import json
import requests
import time
from django.http import Http404  
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
from django.contrib.auth.models import User
from django.core.mail import send_mail
from easy_pdf.views import PDFTemplateView
from djqscsv import render_to_csv_response
from django.db.models.functions import Concat
from django.db.models import Value
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
import phonenumbers
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib
from .bits_decorator import *
from django.shortcuts import render
from registrations.models import *
from registrations.models import (ProgramDomainMapping as PDM,
	ProgramDocumentMap as PDOCM)
from registrations.bits_decorator import *
from .bits_decorator import *
from .forms import *
from registrations.forms import *
from registrations.dynamic_views import (BaseApplicant, 
	BaseOfferLetter, BaseStudentUpload, BaseDocumentUpload,
	BaseConfirmationFile, BaseFinalUploadFile)
from django.db.models import Q
from application_specific.specific_user import *
from django.utils.decorators import method_decorator
from django.utils import timezone
import collections
from PIL import Image
from django.core.files import File
from tempfile import NamedTemporaryFile
from registrations.utils import offer_letter as ol

logger = logging.getLogger("main")

# Create your views here.

@login_required
@is_specific_user
@never_cache
def user_specific_login(request):
	logger.info("{0} invoked funct.".format(request.user.email))

	if ProgramDomainMapping.objects.filter(email = request.user.email).count()>0:
		pg = ProgramDomainMapping.objects.filter(email = request.user.email)
	elif ProgramDomainMapping.objects.filter(email_domain__iexact = request.user.email.split('@')[1]).count()>0:
		pg = ProgramDomainMapping.objects.filter(email_domain__iexact = request.user.email.split('@')[1])
	pg = pg.filter(program__active_for_applicaton_flag = True,
		program__show_on_page_flag = True,program__program_type='specific').distinct()
	eloa = ExceptionListOrgApplicants.objects.filter(
		Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
		employee_email = request.user.email,
		program__in = pg.values_list('program__pk',flat=True),
		exception_type__in=['1','2'])
	program = Program.objects.filter(
		Q(pk__in = eloa.values_list('program__pk',flat=True))|
		Q(show_to_fee_wvr_appl_flag = True)
		)
	pg = pg.filter(program__in = program) if eloa.exists() else pg
	
	return render(request, 'application_specific/user_specific_pg.html',
                  {'pg':pg})



@login_required(login_url="registration_register")
@is_specific_user
@is_specific_program
@applicant_status_permission(None)
@never_cache
def application_form(request,pg_code):
	logger.info("{0} invoked funct.".format(request.user.email))

	StudentFormset = inlineformset_factory(
		User, StudentCandidateApplication, form=studentApplication(pg_code),max_num=1, can_delete=False)
	EducationFormset = modelformset_factory(
		StudentCandidateQualification,
		form=StudentEducation(pg_code), extra=0,min_num=1, can_delete=True, exclude=('application',),
		formset = StudentBaseEducationFormSet(pg_code))
	ExpFormset = modelformset_factory(
		StudentCandidateWorkExperience, form=ExperienceForm, extra=1,
		can_delete=True,formset = BaseExperienceFormSet)
	pgm = Program.objects.get(program_code=str(pg_code))
	form_note = ProgramFormNotesFields.objects.filter(program__program_code=pg_code).values('notes')
	if form_note:
		form_note = form_note[0]['notes']
	else:
		form_note=" "

	if request.method == "POST":
		logger.info("{0} inside POST request".format(request.user.email))
		student_formset = StudentFormset(
            request.POST, instance=request.user, prefix="a")
		exp_formset = ExpFormset(request.POST, prefix="expForm")
		education_formset = EducationFormset(request.POST, prefix="eduForm")
		if student_formset.is_valid() and exp_formset.is_valid() and education_formset.is_valid():
			logger.info("{0} POST request is valid".format(request.user.email))
			try:
				with transaction.atomic():
					for s in student_formset:
						x = s.save(commit=False)
						x.application_status = settings.APP_STATUS[12][0]
						pfa = PROGRAM_FEES_ADMISSION.objects.get(
							program=x.program, latest_fee_amount_flag=True,
							fee_type='2')
						x.admit_year = pfa.admit_year
						x.admit_sem_cohort = pfa.admit_sem_cohort
						x.admit_batch = '{0}-{1}'.format(pfa.admit_year, pfa.admit_sem_cohort)
						x.save()


					app = StudentCandidateApplication.objects.get(login_email=request.user)
					exp_formset.save(commit=False)
					education_formset.save(commit=False)


					for e in exp_formset:
						if e.is_valid() and e.has_changed():
							x = e.save(commit=False)
							if x in exp_formset.deleted_objects:x.delete()
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
					app = StudentCandidateApplication.objects.get(login_email=request.user)
					app.student_application_id = "A" + app.program.program_code
					app.student_application_id += '{:04d}'.format(app.id)
					app.save()
					ExceptionListOrgApplicants.objects.filter(employee_email = app.login_email.email,
						program = app.program).update(application=app)
					ApplicantExceptions.objects.filter(applicant_email = app.login_email.email,
						program = app.program,
						transfer_program__isnull = False ).update(application = app)

					StudentCandidateApplicationSpecific.objects.create(application=app,
						collaborating_organization=app.program.collaborating_organization)
			except IntegrityError:
				logger.error("{0} Integrity error {1}".format(request.user.email,e))
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
		logger.info("{0} inside GET request".format(request.user.email))

		student_formset = StudentFormset(instance=request.user, prefix="a")
		exp_formset = ExpFormset(
            prefix="expForm",
            queryset=StudentCandidateWorkExperience.objects.none())
		education_formset = EducationFormset(
            prefix="eduForm",
            queryset=StudentCandidateQualification.objects.none())
	logger.info("{0} ready to render".format(request.user.email))

	return render(request, 'application_specific/application_form.html', {
        'studentFormset': student_formset,
        'exformset': exp_formset,
        'educationFormset': education_formset,
        'title':pgm.form_title,
        'pg_code':pg_code,
        'form_note':form_note,
        'is_pg_active':pgm.active_for_applicaton_flag,
        'company_logo':pgm.org_logo_image})


@login_required
@is_specific_user
@application_edit_permission
@never_cache
def application_form_edit(request):
	logger.info("{0} invoked funct.".format(request.user.email))
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
	
	form_note = ProgramFormNotesFields.objects.filter(program__program_code=app.program.program_code).values('notes')
	if form_note:
		form_note = form_note[0]['notes']
	else:
		form_note=" "


	if request.method == "POST":
		logger.info("{0} inside POST request".format(request.user.email))
		student_formset = StudentFormset(
		request.POST, instance=request.user, prefix="a")
		exp_formset = ExpFormset(
		request.POST, prefix="expForm", instance=app)
		education_formset = EducationFormset(
		request.POST, prefix="eduForm", instance=app)
		if student_formset.is_valid() and exp_formset.is_valid() and education_formset.is_valid():
			logger.info("{0} POST request is valid".format(request.user.email))

			try:
				with transaction.atomic():

					for s in student_formset:
						x = s.save(commit=False)
						pfa = PROGRAM_FEES_ADMISSION.objects.get(
							program=x.program, latest_fee_amount_flag=True,
							fee_type='2')
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
					app.student_application_id = "A" + app.program.program_code
					app.student_application_id += '{:04d}'.format(app.id)

					app.exam_location = str(app.current_location)
					if app.application_status == settings.APP_STATUS[16][0] :
						app.application_status = settings.APP_STATUS[14][0]
					app.save()
					exp_formset.save()
					education_formset.save()
					ExceptionListOrgApplicants.objects.filter(employee_email = app.login_email.email,
						program = app.program).update(application=app)
					ApplicantExceptions.objects.filter(applicant_email = app.login_email.email,
						program = app.program,
						transfer_program__isnull = False ).update(application = app)

			except IntegrityError:
				logger.error("{0} Integrity error {1}".format(request.user.email,e))
				messages.error(request,
					'There was an error saving your student application.')
				return redirect(reverse('registrationForm:applicantData'))

			subject = 'Application Form %s has been received'%(app.student_application_id)
			user_detail={'progName': app.program.program_name,
			'location': app.current_location.location_name,
			'appID': app.student_application_id,
			'userID':app.login_email.email,
			'regEmailID':app.email_id,
			'is_pg_active':app.program.active_for_applicaton_flag
			}
			msg_plain = render_to_string('application_specific/reg_email.txt', user_detail)
			msg_html = render_to_string('application_specific/reg_email.html', user_detail)
			email = send_mail(subject,msg_plain,'<'+settings.FROM_EMAIL+'>',
				[app.email_id],html_message=msg_html, fail_silently=True)

			return HttpResponseRedirect(reverse('registrationForm:applicantData'))

	else:
		logger.info("{0} inside GET request".format(request.user.email))
		student_formset = StudentFormset(instance=request.user, prefix="a")
		exp_formset = ExpFormset(instance=app, prefix="expForm")
		education_formset = EducationFormset(instance=app, prefix="eduForm")
	logger.info("{0} ready to render".format(request.user.email))	
	return render(
		request, 
		'application_specific/application_form_edit.html',
		{'studentFormset': student_formset,
		'exformset': exp_formset,
		'educationFormset': education_formset,'title':app.program.form_title,
		'company_logo':app.program.org_logo_image,
		'pg_code':app.program.program_code,
		'form_note':form_note,
		'is_pg_active':app.program.active_for_applicaton_flag,
		})

@method_decorator([
	never_cache, 
	login_required, 
	is_specific_user, 
	payment_exception_permission_upload,
	applicant_status_permission(settings.APP_STATUS[13][0])
	], name='dispatch')
#class StudentUpload(BaseStudentUpload):
class StudentUpload(BaseDocumentUpload):
	template_name = 'registrations/upload_document.html'
	
@method_decorator([
	login_required,
	never_cache,
	is_specific_user,
	applicant_status_permission(settings.APP_STATUS[14][0])
	], name='dispatch')
#class StudentUploadEdit(BaseStudentUpload):
class StudentUploadEdit(BaseDocumentUpload):
	template_name = 'registrations/upload_document.html'

@method_decorator([
    login_required,
    is_specific_user,
    applicant_status_permission(settings.APP_STATUS[14][0]),
    ], name='dispatch')
class ConfirmationFile(BaseConfirmationFile):
    template_name = 'application_specific/student_document_view.html'


@method_decorator([
    login_required,
	require_GET,
	is_specific_user,
    ], name='dispatch')
class FinalUploadFile(BaseFinalUploadFile):
    template_name = 'registrations/student_file_final_display.html'


@login_required
@is_specific_user
def application_form_view(request):
	app = StudentCandidateApplication.objects.get(login_email=request.user)
	edu = StudentCandidateWorkExperience.objects.filter(application=app)
	qual = StudentCandidateQualification.objects.filter(application=app)
	uploadFiles=ApplicationDocument.objects.filter(application=app)

	sca_attributes = app.__dict__.keys()
	for x in sca_attributes:
		setattr(app, '%s_hide' %(x), False)

	#logic to check teaching mode,programming_flag
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
		request, 
		'application_specific/application_form_view.html',
		{
			'form': app,
			'edu1': edu,
			'qual1': qual,
			'uploadFiles':uploadFiles,
			'teaching_mode_check':teaching_mode_check,
			'is_specific':is_specific,
		}
	)


@login_required
@never_cache
@is_specific_user
def pdf_redirect_direct_upload(request):

    return render(
        request, 'application_specific/pdf_upload_page.html',
        )

@method_decorator(login_required,name='dispatch')
class Applicant (BaseApplicant):
	template_name = "applicantpdf.html"
	pdf_kwargs = {'encoding' : 'ISO-8859-1',}

@login_required
@is_specific_user
def finalUploadFile1(request):
    return redirect(reverse('application_specific:applicantViewPDF'))

@method_decorator(login_required,name='dispatch')
class OfferLetter (ol.OfferLetterUserView):pass

@login_required
@applicant_status_permission(settings.APP_STATUS[3][0])
def reload_documentation(request):
	app =StudentCandidateApplication.objects.get(login_email=request.user)
	ReviewAcceptedFormSet = formset_factory(ReviewAcceptedForm,
		can_delete=False,extra=0)
	ReviewRejectedFormSet = formset_factory(ReviewRejectedForm,
		can_delete=False,extra=0)
	p_code = str(app.student_application_id)[1:5]
	program_object = Program.objects.filter(program_code=p_code)
	document_submission_flag = program_object[0].document_submission_flag

	if request.method == "POST":
		reviewAcceptedFormSet = ReviewAcceptedFormSet(request.POST,prefix='accp_form')
		reviewRejectedFormSet = ReviewRejectedFormSet(request.POST,request.FILES,prefix="rej_form")
		print reviewRejectedFormSet.is_valid()
		if reviewRejectedFormSet.is_valid() and document_submission_flag:
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
						ad.reload_flag = not ad.program_document_map.deffered_submission_flag
						ad.accepted_verified_by_bits_flag = False
						ad.rejected_by_bits_flag = False
						ad.rejection_reason = None
						ad.verified_rejected_by = ''
						ad.last_uploaded_on = timezone.now()
						ad.save()
						tmp_file.close()
					app.application_status = settings.APP_STATUS[4][0]
					app.save()

			except IntegrityError:
				messages.error(request,'There was an error while reload file')
				return redirect(reverse('registrationForm:applicantData')) #need to be set
		return redirect(reverse('registrationForm:applicantData'))

	else:
		doc = ApplicationDocument.objects.filter(application = app )
		accept_data = []
		reject_data = []
		for x in doc.filter(accepted_verified_by_bits_flag=True):
			data={}
			data['doc_type'] = x.document.document_name
			data['status'] = 'Accepted'
			data['rejection_reason'] = x.rejection_reason
			data['doc_link'] = x.pk if x.file else None
			data['doc_name'] = x.file.name.split("/")[-1] if x.file else '-'
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

	return render(request,'application_specific/reload_upload_file.html',
		{'RAF': reviewAcceptedFormSet,
		'RRF': reviewRejectedFormSet,
		'app_id': app.student_application_id,
		'formset_prefix':'rej_form',
		'document_submission_flag': document_submission_flag
		})
