from django.shortcuts import render,HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests

from django.shortcuts import render, redirect
from registrations.models import *
from bits_rest.models import *
import json, ast
from .forms import propelldApplicationForm
from registrations.review_views import AdmissionFeeView
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse_lazy
from .utils import (complete_admission_process, create_sha256_signature)
from django.utils.decorators import method_decorator

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from adhoc.models import *
from registrations.models import OtherFeePayment
from django.db.models import Q
from django.http import HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

class ApplicationCreateView(AdmissionFeeView, CreateView):

	model = PropelldApplication
	form_class = propelldApplicationForm
	prefix = 'propelld'
	errors_list = None

	def post(self, request, *args, **kwargs):

		self.object = self.get_object()
		form = propelldApplicationForm(request.POST, prefix='propelld')
		if form.is_valid():
			
			if PropelldApplication.objects.filter(application=self.object).exists():
				latest = PropelldApplication.objects.filter(application=self.object).latest('created_on')
				#if PropelldApplication.objects.filter(application=self.object).exclude(status__in=['DROPPED', 'REJECTED']).exists():
				if latest.status not in ['DROPPED', 'REJECTED']:
					latest = PropelldApplication.objects.filter(application=self.object).latest('created_on')
					return HttpResponsePermanentRedirect(latest.redirect_url)
					
				elif latest.status =='REJECTED':
					return HttpResponseRedirect(reverse('registrationForm:pay-fee-adm'))
						
				else:
					return HttpResponseRedirect(reverse('bits_rest:propelld:api', kwargs={'pk':self.object.pk}))

			else:
				return HttpResponseRedirect(reverse('bits_rest:propelld:api', kwargs={'pk':self.object.pk}))
		else:
			return HttpResponseRedirect(reverse('registrationForm:pay-fee-adm'))
		return super(AdmissionFeeView, self).post(request, *args, **kwargs)


class Propelld(TemplateView):
	template_name = 'propelld/payment.html'
	def get_context_data(self, **kwargs):
		context = super(Propelld, self).get_context_data(**kwargs)
		context['pk'] = kwargs['pk']
		return context		

@csrf_exempt
def apicall(request,**kwargs):
	data = json.loads(request.body)
	url=("%s%s"%(settings.PROPELLD_URL,"product/apply/generic"))
	resp_data = { }
	def get_program():
		
		sca = StudentCandidateApplication.objects.get(login_email__email=request.user.email)
		return sca.program

	def get_keys():
		prog = get_program()
		propelld = prog.propelld

		if propelld is not None:
			c_id = propelld.client_id.strip()
			c_sec = propelld.client_secret.strip()
		else:
			c_id = settings.PROPELLD_CLIENT_ID
			c_sec = settings.PROPELLD_CLIENT_SECRET

		return dict(client_id=c_id, client_secret=c_sec)

	propelld_keys = get_keys()
	headers = {
            "Content-Type" : "application/json",
            "client-id" : propelld_keys['client_id'],
            "client-secret" : propelld_keys['client_secret'],
			}
	details = StudentCandidateApplication.objects.get(login_email__email=request.user.email)
	course_id = Program.objects.get(id=details.program_id)
	propelld_amount = PROGRAM_FEES_ADMISSION.objects.get(program=details.program, fee_type='8')

	#propelld api data
	data={
    "CourseId": int(course_id.propelld_course_id),
    "FirstName": details.full_name.rsplit(' ', 1)[0],
    "DiscountedCourseFee": int(propelld_amount.fee_amount),
    "Email": details.login_email.email,
    "Mobile": details.mobile.national_number,
    "ReferenceNumber": details.student_application_id,
    "RedirectUrl": 'http%s://%s%s' % ('s' if request.is_secure() else '',
							request.get_host(),
							reverse_lazy('registrationForm:pay-fee-adm')),
 	}

	try:
		res = requests.post(url, headers=headers, json=data)
		resp_data=eval(json.dumps(res.json()))
		if res.status_code == 200 and resp_data["Code"]==0:

			PropelldApplication.objects.create(quote_id=resp_data['PayLoad']['QuoteId'], 
					application= details,
					program= details.program,
					created_on= timezone.now(),
					full_name=details.full_name.rsplit(' ', 1)[0],
					email = details.login_email.email,
					mobile= details.phone.national_number,
					loan_amount=int(propelld_amount.fee_amount),
					updated_on= timezone.now(),
					redirect_url=resp_data['PayLoad']['RedirectionUrl'],
					)

			return HttpResponse(str(resp_data['PayLoad']['RedirectionUrl']))
		else:
			raise Exception("Propelld,error")
	except Exception as e:

		if res.status_code == 406:
			messages.error(request, res.json()['Errors'][0]['Message'])

		failed='http%s://%s%s' % ('s' if request.is_secure() else '',
							request.get_host(),
						reverse_lazy('registrationForm:pay-fee-adm'))
		return HttpResponse(failed)


@method_decorator([require_POST, csrf_exempt,], name='dispatch')
class CallBackView(View):
	def post(self, request, *args, **kwargs):
		received_json_data = json.loads(request.body)
		error_list = []

		if create_sha256_signature(settings.PROPELLD_CALLBACK_KEY, request.body) != request.META.get('HTTP_X_PROPELLD_SIGNATURE'):
			context = {"return_status": {
						"status": "SIGNATURE NOT VERIFIED"
						}
					}

			return JsonResponse(context,status=401)
		
		try:
			with transaction.atomic():

				app = PropelldApplication.objects.get(quote_id=received_json_data['Payload']['Application']['QuoteId'])
				callback_body_meta = app.callback_body_meta or []
				callback_body_meta.append(received_json_data)
				app.callback_body_meta = callback_body_meta

				if not app:
					context = {"return_status": {
						"status": "INVALID QUOTE ID"
						}
					}
					return JsonResponse(context,status=404)

				if app.application.application_status == settings.APP_STATUS[9][0]:
					
					app.status = received_json_data['Payload']['Application']['Status']
					app.updated_on= timezone.now()

					if 'Disbursement' in received_json_data['Payload']:
						
						app.updated_on = timezone.now()
						app.disbursed_amount = received_json_data['Payload']['Disbursement'][0]['DisbursementAmount']
						app.utr_number = received_json_data['Payload']['Disbursement'][0]['DisbursementReference']
						app.disbursement_date = received_json_data['Payload']['Disbursement'][0]['DisbursementDate']
						
						complete_admission_process(app.application.login_email.email)
						ApplicationPayment.objects.create(
							payment_id=app.quote_id,
							payment_amount=app.loan_amount,
							payment_date=timezone.now(),
							payment_bank='Propelld',
							transaction_id=app.quote_id,
							application=app.application,
							fee_type='1',
							insertion_datetime=timezone.now()
						)

					app.save()

		except Exception as e:
			error_list.append(str(e))

		if error_list:
			context={
					"return_status":{
							"status":"FAILURE",
							"errors":[{
								"error_code":500,
								"message": ','.join(error_list) if error_list else 'bits propelld callback was hit...',
									}]
							}
						}
		else:
			context = {"return_status": {
						"status": "SUCCESS"
						}
					}
		return JsonResponse(context)



class PropelldRedirectView(TemplateView):
	template_name = 'propelld/landing_page.html'
