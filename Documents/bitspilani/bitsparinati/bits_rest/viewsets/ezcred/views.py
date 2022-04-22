from django.shortcuts import render,HttpResponseRedirect,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests

from django.shortcuts import render, redirect
from registrations.models import *
from bits_rest.models import *
import json, ast
from .forms import ezcredApplicationForm
from registrations.review_views import AdmissionFeeView
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse_lazy
from .utils import complete_admission_process
from django.utils.decorators import method_decorator

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from adhoc.models import *
from registrations.models import OtherFeePayment

class ApplicationCreateView(AdmissionFeeView, CreateView):
	model = EzcredApplication
	form_class = ezcredApplicationForm
	prefix = 'ezcred'

	def form_invalid(self, form):
		return self.render_to_response(self.get_context_data(ezcred_form=form))

	def form_valid(self, form):
		return super(ApplicationCreateView, self).form_valid(form)

	def get_success_url(self):
		return reverse_lazy('bits_rest:ezcred:api', kwargs={'pk':self.object.pk})




class Ezcred(TemplateView):
	template_name = 'ezcred/payment.html'
	def get_context_data(self, **kwargs):
		context = super(Ezcred, self).get_context_data(**kwargs)
		context['pk'] = kwargs['pk']
		return context

@csrf_exempt
def apicall(request,**kwargs):
	data = json.loads(request.body)
	app = EzcredApplication.objects.get(id=data['pk'])
	url=("%s%s"%(settings.EZCRED_URL,"/lead/v2"))
	resp_data = { }
	headers = {
            "Content-Type" : "application/json",
			}
	details = StudentCandidateApplication.objects.get(login_email__email=request.user.email)
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
							reverse_lazy('bits_rest:ezcred:landing', kwargs={'pk':app.pk})),
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
		MetaEzcredexceptions.objects.create(email=request.user.email, errors=errors_list)
		lead_insert = EzcredApplication.objects.get(application__login_email__email=request.user.email)
		if not lead_insert.lead_id:
			lead_insert.delete()
		failed='http%s://%s%s' % ('s' if request.is_secure() else '',
							request.get_host(),
						reverse_lazy('registrationForm:pay-fee-adm'))
		return HttpResponse(failed)



class EzcredRedirectView(TemplateView):
	template_name = 'ezcred/landing_page.html'

	def get_context_data(self, **kwargs):
		context = super(EzcredRedirectView, self).get_context_data(**kwargs)
		context['ezcred'] = EzcredApplication.objects.get(pk=kwargs['pk'])
		return context


@method_decorator([require_POST, csrf_exempt,], name='dispatch')
class CallBackView(View):
	def post(self, request, *args, **kwargs):
		received_json_data = json.loads(request.body)
		error_list = []

		try:
			with transaction.atomic():
				check_adhoc_exists = AdhocEzcredApplication.objects.filter(lead_id=received_json_data["lead_number"]).exists()

				if check_adhoc_exists:
					app = AdhocEzcredApplication.objects.get(lead_id=received_json_data["lead_number"])
					sca_status = StudentCandidateApplication.objects.get(login_email__email=app.email)
					callback_meta = app.callback_meta or []
					callback_meta.append(received_json_data)
					app.callback_meta = callback_meta
					app.status = received_json_data["status"]
					if sca_status.application_status == settings.APP_STATUS[9][0]:
						if received_json_data['status']== "ACTIVE":
							app.approved_or_rejected_on = timezone.now()
							app.amount_approved = received_json_data["disbursal_data"]["disbursal_amount"]

						if received_json_data['status'] == "DISBURSED":
							app.approved_or_rejected_on = timezone.now()
							complete_admission_process(app.email)

							ofp = OtherFeePayment.objects.get(program=app.program, fee_type=app.fee_type, email=app.email)
							ofp.paid_on = timezone.now()
							ofp.transaction_id = app.order_id,
							ofp.payment_bank = 'Ezcred'
							ofp.save()
						elif received_json_data['status'] == 'DISBURSAL_FAILED':
							app.approved_or_rejected_on = timezone.now()

					app.save()

				else:
					app = EzcredApplication.objects.get(lead_id=received_json_data["lead_number"])
					callback_meta = app.callback_meta or []
					callback_meta.append(received_json_data)
					app.callback_meta = callback_meta
					app.status = received_json_data["status"]
					if app.application.application_status == settings.APP_STATUS[9][0]:
						if received_json_data['status']== "ACTIVE":
							app.approved_or_rejected_on = timezone.now()
							app.amount_approved = received_json_data["disbursal_data"]["disbursal_amount"]

						if received_json_data['status'] == "DISBURSED":
							app.approved_or_rejected_on = timezone.now()
							complete_admission_process(app.application.login_email.email)
							ApplicationPayment.objects.create(
								payment_id=app.order_id,
								payment_amount=app.amount_requested,
								payment_date=timezone.now(),
								payment_bank='Ezcred',
								transaction_id=app.order_id,
								application=app.application,
								fee_type='1',
								insertion_datetime=timezone.now()
							)

						elif received_json_data['status'] == 'DISBURSAL_FAILED':
							app.approved_or_rejected_on = timezone.now()

					app.save()

		except Exception as e:
			error_list.append(str(e))

		if error_list:
			context={
					"return_status":{
							"status":"FAILURE",
							"errors":[{
								"error_code":500,
								"message": ','.join(error_list) if error_list else 'bits ezcred callback was hit...',
									}]
							}
						}
		else:
			context = {"return_status": {
						"status": "SUCCESS"
						}
					}
		return JsonResponse(context)

def ezcredcancell(request,**kwargs):
	lead_id = str(request.POST.get('lead_id'))

	app = EzcredApplication.objects.get(lead_id=lead_id)
	if app.callback_meta:
		loan_account_number=app.callback_meta[0]['loan_account_number']
		resp_data={}
		url=("%s%s%s%s"%(settings.EZCRED_URL,"/loan/",loan_account_number,"/cancel"))
		headers = {
	            "Content-Type" : "application/json",
				}
		data={
		   "partner_id":settings.EZCRED_PARTNER_ID,
		   "merchant_id":" "
		}

		r = requests.post(url, headers=headers, json=data,auth=(settings.EZCRED_USERNAME,settings.EZCRED_PASSWORD))
		resp_data=json.dumps(r.json())
		resp_data=json.loads(resp_data)
		if r.status_code==200 and resp_data['success']==True:
			del_rec = EzcredApplication.objects.get(application__login_email__email=request.user.email)
			EzcredApplicationcanceledloans.objects.create(email=request.user.email, order_id=app.order_id,lead_id=app.lead_id,lead_link=app.lead_link,is_approved=app.is_approved,
                                                         is_terms_and_condition_accepted=app.is_terms_and_condition_accepted,amount_requested=app.amount_requested,
                                                         amount_approved=app.amount_approved,status=app.status,created_on=app.created_on,
                                                         updated_on=app.updated_on,approved_or_rejected_on=app.approved_or_rejected_on,
                                                         callback_meta=app.callback_meta,request_body_meta=app.request_body_meta)
			del_rec.delete()
		else:
			MetaEzcredexceptions.objects.create(email=request.user.email, errors=resp_data)
		return HttpResponseRedirect('/registrations/pay-fee-adm-view/')
	else:
		del_rec = EzcredApplication.objects.get(application__login_email__email=request.user.email)
		EzcredApplicationcanceledloans.objects.create(email=request.user.email, order_id=app.order_id,lead_id=app.lead_id,lead_link=app.lead_link,is_approved=app.is_approved,
                                                         is_terms_and_condition_accepted=app.is_terms_and_condition_accepted,amount_requested=app.amount_requested,
                                                         amount_approved=app.amount_approved,status=app.status,created_on=app.created_on,
                                                         updated_on=app.updated_on,approved_or_rejected_on=app.approved_or_rejected_on,
                                                         callback_meta=app.callback_meta,request_body_meta=app.request_body_meta)
		del_rec.delete()
		return HttpResponseRedirect('/registrations/pay-fee-adm-view/')