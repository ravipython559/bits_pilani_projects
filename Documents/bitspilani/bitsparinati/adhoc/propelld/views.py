from django.shortcuts import render,HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests

from django.shortcuts import render, redirect
from registrations.models import *
import json, ast
from registrations.review_views import AdmissionFeeView
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.http import JsonResponse, HttpResponsePermanentRedirect
from django.db import IntegrityError, transaction

from adhoc.models import AdhocPropelldApplication, AdhocMetaEmi
from django.views.decorators.cache import never_cache


from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView

from adhoc.tpsl import AdhocMixin, BaseAdhocView
from .forms import ApplicationForm


from django.utils.decorators import method_decorator
from bits_rest.models import MetaEzcredexceptions
from django.core.urlresolvers import reverse

from django.contrib import messages
from .utils import get_propelld_inprogress, create_sha256_signature, complete_admission_process
from django.core.exceptions import ValidationError

class ApplicationCreateView(AdhocMixin, BaseAdhocView):

	form_class = ApplicationForm
	template_name = 'adhoc/pay_adhoc_fee.html'

	def post_api_call(self, form):
		mobile = form.cleaned_data['mobile']
		pin_code = form.cleaned_data['pin_code']
		full_name = form.cleaned_data['full_name']

		propelld_record = get_propelld_inprogress(self.object.email)
		
		if propelld_record:
			ap = propelld_record

		else:

			ap = AdhocPropelldApplication.objects.create(
				order_id=str(uuid.uuid4().hex),
				program=self.object.program,
				created_on= timezone.now(),
				full_name= full_name,
				email=self.object.email,
				mobile=mobile,
				loan_amount=self.object.fee_amount,
				updated_on= timezone.now(),
				fee_type=self.object.fee_type
			)

		return redirect(reverse_lazy('adhoc:propelld:api', kwargs={'pk':ap.pk}))
		

class Propelld(TemplateView):
	template_name = 'adhoc/propelld/pay.html'
	
	def get_context_data(self, **kwargs):
		context = super(Propelld, self).get_context_data(**kwargs)
		context['pk'] = kwargs['pk']
		return context

@csrf_exempt
def apicall(request,**kwargs):

	
	
	data = json.loads(request.body)
	app = AdhocPropelldApplication.objects.get(id=data['pk'])
	ofp = OtherFeePayment.objects.filter(email=app.email).latest('created_on')
	url=("%s%s"%(settings.PROPELLD_URL,"product/apply/generic"))
	resp_data = { }

	def get_keys():

		propelld = ofp.Propelld_Program_Map

		if propelld is not None:
			c_id = propelld.client_id.strip()
			c_sec = propelld.client_secret.strip()
		else:
			c_id = settings.PROPELLD_CLIENT_ID
			c_sec = settings.PROPELLD_CLIENT_SECRET

		return dict(client_id=c_id, client_secret=c_sec)

	propelld_keys = get_keys()
	client_id = propelld_keys['client_id']
	client_secret = propelld_keys['client_secret']
	
	headers = {
            "Content-Type" : "application/json",
            "client-id" : client_id,
            "client-secret" : client_secret,
			}

	details = OtherFeePayment.objects.get(email=app.email)
	
	#propelld api data
	data={
    "CourseId": int(ofp.propelld_course_id),  #dynamic?
    "FirstName": app.full_name.rsplit(' ', 1)[0],
    "DiscountedCourseFee": int(ofp.fee_amount),
    "Email": app.email,
    "Mobile": app.mobile.national_number,
    "ReferenceNumber": app.order_id,
    "RedirectUrl": 'http%s://%s%s' % ('s' if request.is_secure() else '',
							request.get_host(),
							reverse_lazy('adhoc:pay-adhoc-fee-view-token-user',kwargs={'pk':ofp.pk})),
 	}

	try:
		res = requests.post(url, headers=headers, json=data)
		resp_data=eval(json.dumps(res.json()))
		if res.status_code == 200 and resp_data["Code"]==0:

			app.quote_id=resp_data['PayLoad']['QuoteId']
			app.redirect_url=resp_data['PayLoad']['RedirectionUrl']
			app.updated_on= timezone.now()
			app.save()
			return HttpResponse(str(resp_data['PayLoad']['RedirectionUrl']))

		else:
			raise Exception("Propelld,error")
	except Exception as e:

		if res.status_code == 406:
			messages.error(request, res.json()['Errors'][0]['Message'])

		failed='http%s://%s%s' % ('s' if request.is_secure() else '',
							request.get_host(),
						reverse_lazy('adhoc:pay-adhoc-fee-view-token-user',kwargs={'pk':ofp.pk}))
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


				app = AdhocPropelldApplication.objects.get(quote_id=received_json_data['Payload']['Application']['QuoteId'])
				callback_body_meta = app.callback_body_meta or []
				callback_body_meta.append(received_json_data)
				app.callback_body_meta = callback_body_meta

				if not app:
					context = {"return_status": {
						"status": "INVALID QUOTE ID"
						}
					}
					return JsonResponse(context,status=404)


				app.status = received_json_data['Payload']['Application']['Status']
				app.updated_on= timezone.now()

				if 'Disbursement' in received_json_data['Payload']:

					app.updated_on = timezone.now()
					app.disbursed_amount = received_json_data['Payload']['Disbursement'][0]['DisbursementAmount']
					app.utr_number = received_json_data['Payload']['Disbursement'][0]['DisbursementReference']
					app.disbursement_date = received_json_data['Payload']['Disbursement'][0]['DisbursementDate']

					ofp = OtherFeePayment.objects.get(program=app.program, fee_type=app.fee_type, email=app.email)
					ofp.paid_on = timezone.now()
					ofp.transaction_id = app.quote_id,
					ofp.payment_bank = 'Propelld'
					ofp.gateway_total_amount = app.loan_amount
					ofp.gateway_net_amount = app.disbursed_amount
					ofp.full_name = app.full_name
					ofp.mobile = app.mobile

					ofp.save()

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
