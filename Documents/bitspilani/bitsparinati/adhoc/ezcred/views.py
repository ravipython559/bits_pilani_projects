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
from django.http import JsonResponse
from django.db import IntegrityError, transaction

from adhoc.models import AdhocEzcredApplication, AdhocMetaEmi
from django.views.decorators.cache import never_cache


from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView

from adhoc.tpsl import AdhocMixin, BaseAdhocView
from .forms import ApplicationForm

from adhoc.ezcred.utils import *
from django.utils.decorators import method_decorator
from bits_rest.models import MetaEzcredexceptions

class ApplicationCreateView(AdhocMixin, BaseAdhocView):

	errors_list = None
	adhoc_error_model = AdhocMetaEmi
	form_class = ApplicationForm
	template_name = 'adhoc/pay_adhoc_fee.html'
	error_template_name = 'adhoc/500.html'

	def post_api_call(self, form):
		mobile = form.cleaned_data['mobile']
		pin_code = form.cleaned_data['pin_code']
		full_name = form.cleaned_data['full_name']
		
		ae = AdhocEzcredApplication.objects.create(
			order_id=str(uuid.uuid4().hex),
			email=self.object.email, program=self.object.program,
			fee_type=self.object.fee_type, amount_requested=self.object.fee_amount,
		)

		return redirect(reverse_lazy('adhoc:ezcred:api', kwargs={'pk':ae.pk}))



class Ezcred(TemplateView):
	template_name = 'adhoc/ezcred/payment.html'
	def get_context_data(self, **kwargs):
		context = super(Ezcred, self).get_context_data(**kwargs)
		context['pk'] = kwargs['pk']
		return context

@csrf_exempt
def apicall(request,**kwargs):
	data = json.loads(request.body)
	app = AdhocEzcredApplication.objects.get(id=data['pk'])
	ofp = OtherFeePayment.objects.get(email=app.email)
	url=("%s%s"%(settings.EZCRED_URL,"/lead/v2"))
	resp_data = { }
	headers = {
            "Content-Type" : "application/json",
			}
	details = StudentCandidateApplication.objects.get(login_email__email=app.email)
	program = Program.objects.get(id=details.program_id)
	state_choice = ast.literal_eval(json.dumps(dict(STATE_CHOICES)))
	employment_choice = ast.literal_eval(json.dumps(dict(EMPLOYMENTSTATUS_CHOICES)))
	f_name = details.full_name.rsplit(' ', 1)
	first_name = f_name[0]
	last_name = f_name[1] if len(f_name)>1 else ''
	gender = 'MALE' if details.gender=='M' else 'FEMALE'

	data={
			"partner_id":settings.EZCRED_PARTNER_ID,
			"merchant_id": "",
			"partner_reference_id":details.student_application_id,
			"redirect_url": 'http%s://%s%s' % ('s' if request.is_secure() else '',
							request.get_host(),
							reverse_lazy('adhoc:ezcred:landing', kwargs={'pk':app.pk})),
			"product_details": {
				"type":"PRIMARY",
				"category": "Education",
				"brand": "bits",
				"model": program.program_code,
				"price": int(app.amount_requested)
			},
			"customer_information": {
				"personal_information": {
					"first_name": first_name,
					"last_name": last_name,
					"date_of_birth": details.date_of_birth.strftime('%d-%m-%Y'),
					"gender":gender,
					"personal_details":{
					 	"mother_name": details.mothers_name.encode("utf-8")
					},
				},
				"addresses": [{
					"type":"PERMANENT",
					"address_line_1": details.address_line_1,
					"address_line_2": details.address_line_2,
					"city": details.city.encode("utf-8"),
					"state": state_choice[details.state],
					"pincode":int(details.pin_code)
				}],
				"phones": [{
					"type": "MOBILE",
					"country_calling_code": details.phone.country_code,
					"number": details.phone.national_number
				}],
				"emails":  [{
					"type": "WORK",
					"email": details.email_id
				}]
			}
		}
	app.request_body_meta = data
	app.save()
	try:
		r = requests.post(url, headers=headers, json=data,auth=(settings.EZCRED_USERNAME,settings.EZCRED_PASSWORD))
		resp_data=eval(json.dumps(r.json())) 
		if r.status_code == 200 and resp_data["return_status"]['status']=="SUCCESS":
			app.lead_id = resp_data['lead_number']
			app.lead_link = resp_data['loan_link']
			app.created_on = timezone.now()
			app.save()
			return HttpResponse(str(resp_data["loan_link"]))
		else:
			raise Exception("Ezcred,error")
	except Exception as e:
		errors_list = {'request_error':resp_data,'exceptions':str(e)}
		MetaEzcredexceptions.objects.create(email=app.email, errors=errors_list)
		failed='http%s://%s%s' % ('s' if request.is_secure() else '',
						request.get_host(),
					reverse_lazy('adhoc:pay-adhoc-fee-view-token-user',kwargs={'pk':ofp.pk}))
		return HttpResponse(failed)



class EzcredRedirectView(TemplateView):
	template_name = 'adhoc/ezcred/landing_page.html'

	def get_context_data(self, **kwargs):
		context = super(EzcredRedirectView, self).get_context_data(**kwargs)
		context['ezcred'] = AdhocEzcredApplication.objects.get(pk=kwargs['pk'])
		return context


