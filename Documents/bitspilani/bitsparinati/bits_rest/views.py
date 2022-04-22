"""
Rest API for Payment Integration.

Rest API to interact with PHP Payment API for Payment
"""
import json
import requests
from registrations.models import *
from django.views.decorators.csrf import csrf_exempt
from bits_admin.models import StudentCandidateApplicationArchived
from django.views.generic import FormView
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from datetime import datetime
from requests.exceptions import ConnectionError
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Max
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_mysql.locks import Lock
from bits_rest.bits_extra import student_id_generator
from .models import MetaAdhocPayment
from django.utils import timezone
from dateutil.parser import parse
from registrations.bits_decorator import *
from django.views.generic import View
from django.http import HttpResponsePermanentRedirect
from easy_pdf.views import PDFTemplateView
from django.views.generic import TemplateView
from bits_rest.bits_decorators import *
import phonenumbers
from .forms import *
import logging
import uuid
import decimal
import re

logger = logging.getLogger("main")


@never_cache
@require_POST
@csrf_exempt
def bits_view(request):
	"""Method to process Payment."""
	headers = {'Content-type': 'application/json'}
	ctx = {}
	ctx['responseMsg'] = request.POST.get('msg')
	ctx['responseType'] ='APP'
	r = requests.post(settings.PAYMENT_RESPONSE_URL,
		data=json.dumps(ctx), 
		headers=headers)

	if r.status_code == 200:
		a = r.json()
		msg = a['responseMessage'].split("|")
		r_order_id = msg[3].split("=")[1]
		meta_payment_obj = MetaPayment.objects.get(order_id=r_order_id)
		app_id = meta_payment_obj.application_id
		app = StudentCandidateApplication.objects.get(id=app_id)
		seq_max = MetaPayment.objects.filter(application = app, fee_type='2').aggregate(Max('sequence_number'))['sequence_number__max']
		meta_payment, created = MetaPayment.objects.get_or_create(application = app, sequence_number = seq_max, fee_type='2')
		meta_payment.res_pay_req_date = datetime.now()
		meta_payment.res_json_data = json.dumps(ctx)
		meta_payment.save()
		meta_payment.res_pay_status = r.status_code
		meta_payment.res_pay_res_date = datetime.now()
		meta_payment.save()
		meta_payment.res_json_return_data = a
		meta_payment.save()
		r_status = msg[0].split("=")[1]
		if r_status == "0300":
			try:
				with transaction.atomic():
					app = StudentCandidateApplication.objects.get(
						id=app_id)
					ApplicationPayment.objects.create(
						payment_id=msg[3].split("=")[1],
						payment_amount=msg[6].split("=")[1],
						payment_date=datetime.strptime(
							msg[8].split("=")[1], 
							'%d-%m-%Y %H:%M:%S'),
						payment_bank=msg[4].split("=")[1],
						transaction_id=msg[5].split("=")[1],
						application=app,fee_type='2',
						)
					app.application_status = settings.APP_STATUS[13][0]
					app.save()

			except ConnectionError as e:
				return redirect(reverse('registrationForm:error-payment'))
			except IntegrityError:
				messages.error(request,'There was an error while payment.')
				return redirect(reverse('registrationForm:error-payment'))
			except:
				return redirect(reverse('registrationForm:error-payment'))
			else:
				return redirect(reverse('registrationForm:fee'))
		else:
			return redirect(reverse('registrationForm:error-payment'))
	else:
		return redirect(reverse('registrationForm:error-payment'))
	return redirect(reverse('registrationForm:bits-login-user'))

@never_cache
@require_POST
@csrf_exempt
def bits_view_admission(request):
	headers = {'Content-type': 'application/json'}
	ctx = {}
	ctx['responseMsg'] = request.POST.get('msg')
	ctx['responseType'] ='ADM'
	logger.info("bits_view_admission ----1")

	r = requests.post(settings.PAYMENT_RESPONSE_URL,
		data=json.dumps(ctx),
		headers=headers)

	if r.status_code == 200:
		a = r.json()
		msg = a['responseMessage'].split("|")
		r_order_id = msg[3].split("=")[1]
		meta_payment_obj = MetaPayment.objects.get(order_id=r_order_id)
		app_id = meta_payment_obj.application_id
		app = StudentCandidateApplication.objects.get(id=app_id)
		try:
			ae = ApplicantExceptions.objects.get(applicant_email = app.login_email.email, program = app.program)
			ae = ae.transfer_program if ae.transfer_program else None
		except ApplicantExceptions.DoesNotExist:
			ae=None

		seq_max = MetaPayment.objects.filter(application = app, fee_type='1').aggregate(Max('sequence_number'))['sequence_number__max']
		meta_payment, created = MetaPayment.objects.get_or_create(application = app, sequence_number = seq_max,fee_type='1')
		meta_payment.res_pay_req_date = datetime.now()
		meta_payment.res_json_data = json.dumps(ctx)
		meta_payment.save()
		meta_payment.res_pay_status = r.status_code
		meta_payment.res_pay_res_date = datetime.now()
		meta_payment.save()
		meta_payment.res_json_return_data = a
		meta_payment.save()

		r_status = msg[0].split("=")[1]

		if  r_status == "0300":
			try:
				with transaction.atomic():
					app = StudentCandidateApplication.objects.get(id=app_id)
					ApplicationPayment.objects.create(
						payment_id=msg[3].split("=")[1],
						payment_amount=msg[6].split("=")[1],
						payment_date=datetime.strptime(
							msg[8].split("=")[1], '%d-%m-%Y %H:%M:%S'),
						payment_bank=msg[4].split("=")[1],
						transaction_id=msg[5].split("=")[1],
						application=app,fee_type='1')
					app.application_status = settings.APP_STATUS[11][0]
					app.save()
					logger.info("ApplicationPayment done still in transaction")
					try:
						logger.info("lock starts to generate student id")
						with Lock('bits_student_id_lock'):

							cs = CandidateSelection.objects.get(application = app,)
							cs.student_id = student_id_generator(login_email = app.login_email.email)
							cs.admitted_to_program = ae
							cs.save()
							logger.info("lock ends")
					except TimeoutError:
						logger.error("time out error for student id")
						return redirect(reverse('registrationForm:admission-payment-error'))

					user_detail ={'program':app.program.program_name,
					'en_roll':cs.student_id }

					msg_plain = render_to_string('email_admission_fees.txt',
						user_detail)
					msg_html = render_to_string('email_admission_fees.html', 
						user_detail)
					email = send_mail('admission fee',
						msg_plain,
						'<' + settings.FROM_EMAIL + '>',
						[app.email_id],
						html_message=msg_html, fail_silently=True)
					logger.info("email ")
					return redirect(reverse('registrationForm:fee-adm-page'))
			except ConnectionError as e:
				
				return redirect(reverse('registrationForm:admission-payment-error'))
			except IntegrityError:
				
				messages.error(request,'There was an error while payment.')
				return redirect(reverse('registrationForm:error-payment'))
			except:
				return redirect(reverse('registrationForm:admission-payment-error'))
		else :
			return redirect(reverse('registrationForm:admission-payment-error'))
	else:
		return redirect(reverse('registrationForm:admission-payment-error'))

	return redirect(reverse('registrationForm:bits-login-user'))
