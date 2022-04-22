import datetime
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
from django.db.models import Q
from application_specific.specific_user import *
from django.utils.decorators import method_decorator

logger = logging.getLogger("main")

@login_required
@is_waiver
@is_waiver_program
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

    if request.method == "POST":
        logger.info("{0} inside POST request".format(request.user.email))
        student_formset = StudentFormset(
            request.POST, instance=request.user, prefix="a")
        exp_formset = ExpFormset(request.POST, prefix="expForm")
        education_formset = EducationFormset(request.POST, prefix="eduForm")

        if student_formset.is_valid() and exp_formset.is_valid() and \
                education_formset.is_valid():
            logger.info("{0} POST request is valid".format(request.user.email))
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
                    app.student_application_id = "A" + app.program.program_code + \
                        '{:04d}'.format(app.id)
                    app.save()
                    ExceptionListOrgApplicants.objects.filter(employee_email = app.login_email.email,
                          program = app.program).update(application=app)
                    ApplicantExceptions.objects.filter(applicant_email = app.login_email.email,
                            program = app.program,
                            transfer_program__isnull = False ).update(application = app)
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
            'regEmailID':app.email_id,
            'is_pg_active':app.program.active_for_applicaton_flag}
            msg_plain = render_to_string('reg_email.txt', user_detail)
            msg_html = render_to_string('reg_email.html', user_detail)
            email = send_mail(subject,msg_plain,'<'+settings.FROM_EMAIL+'>',
                [app.email_id],html_message=msg_html,fail_silently=True)

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
    return render(request, 'waiver/application_form.html', {
        'studentFormset': student_formset,
        'exformset': exp_formset,
        'educationFormset': education_formset,
        'title':pgm.form_title,
        'is_pg_active':pgm.active_for_applicaton_flag,
        'pg_code':pg_code})



@login_required
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
                    ExceptionListOrgApplicants.objects.filter(employee_email = app.login_email.email,
                        program = app.program).update(application=app)
                    ApplicantExceptions.objects.filter(applicant_email = app.login_email.email,
                            program = app.program,
                            transfer_program__isnull = False ).update(application = app)

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
            'regEmailID':app.email_id,
            'is_pg_active':app.program.active_for_applicaton_flag}
            msg_plain = render_to_string('reg_email.txt', user_detail)
            msg_html = render_to_string('reg_email.html', user_detail)
            
            email = send_mail(subject,msg_plain,'<'+settings.FROM_EMAIL+'>',
                [app.email_id],html_message=msg_html,fail_silently=True)
            
            
            return HttpResponseRedirect(reverse('registrationForm:applicantData'))

    else:
        logger.info("{0} inside GET request".format(request.user.email))
        student_formset = StudentFormset(instance=request.user, prefix="a")
        exp_formset = ExpFormset(instance=app, prefix="expForm")
        education_formset = EducationFormset(instance=app, prefix="eduForm")
    logger.info("{0} ready to render".format(request.user.email))   
    return render(
        request, 'waiver/application_form_edit.html',
        {'studentFormset': student_formset,
        'exformset': exp_formset,
        'educationFormset': education_formset,'title':app.program.form_title,
        'pg_code':app.program.program_code,
        'is_pg_active':app.program.active_for_applicaton_flag,
        })
