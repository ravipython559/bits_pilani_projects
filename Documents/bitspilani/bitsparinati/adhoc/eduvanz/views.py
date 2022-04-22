from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone
from django.core.urlresolvers import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, View
from django.db import IntegrityError, transaction
from django.conf import settings
from adhoc.models import AdhocEduvanzApplication, AdhocMetaEmi
from registrations.models import OtherFeePayment
from adhoc.bits_decorators import is_transaction_done
from adhoc.tpsl import AdhocMixin, BaseAdhocView
from adhoc.eduvanz.utils import (get_eduvanz_inprogress, 
	get_eduvanz_declined, get_eduvanz_approved, 
	delete_initiated_application)
from adhoc.zest_utils import zest_emi_in_progress
from django.views.decorators.cache import never_cache
from .forms import ApplicationForm
import requests
import json
import uuid

@method_decorator([never_cache, is_transaction_done], name='dispatch')	
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
		delete_initiated_application(self.object)

		if (
			not get_eduvanz_inprogress(self.object) and 
			not get_eduvanz_declined(self.object) and 
			# not zest_emi_in_progress(self.object) and 
			not get_eduvanz_approved(self.object)
			):
		
			ae = AdhocEduvanzApplication.objects.create(
				mobile=mobile, pin_code=pin_code, order_id=str(uuid.uuid4().hex),
				email=self.object.email, program=self.object.program, full_name=full_name,
				fee_type=self.object.fee_type, amount_requested=self.object.fee_amount,
			)

			return redirect(reverse_lazy('adhoc:eduvanz:api', kwargs={'pk':ae.pk}))
		else:
			return redirect('https://eduvanz.com/sign')

class EduvanzRedirectView(TemplateView):
	template_name = 'adhoc/eduvanz/landing_page.html'

	def get_context_data(self, **kwargs):
		context = super(EduvanzRedirectView, self).get_context_data(**kwargs)
		context['eduvanz'] = AdhocEduvanzApplication.objects.get(pk=kwargs['pk'])
		return context

class Eduvanz(TemplateView):
	template_name = 'adhoc/eduvanz/payment.html'

	def get_context_data(self, **kwargs):
		app = AdhocEduvanzApplication.objects.get(pk=kwargs['pk'])
		ofp = OtherFeePayment.objects.get(program=app.program, fee_type=app.fee_type, email=app.email)
		context = super(Eduvanz, self).get_context_data(**kwargs)
		context['EDUVANZ_URL'] = settings.ADHOC_EDUVANZ_URL
		context['eduvanzdict'] = {
			'meta_data': app.order_id,
			'userName': settings.ADHOC_EDUVANZ_USERNAME,
			'password': settings.ADHOC_EDUVANZ_PASSWORD,
			'redirect_url': 'http%s://%s%s' % ('s' if self.request.is_secure() else '',
				self.request.get_host(), 
				reverse_lazy('adhoc:eduvanz:landing', kwargs={'pk':app.pk})
			),
			'requestParam[client_institute_id]':settings.ADHOC_EDUVANZ_CLIENT_INSTITUTE_ID,
			'requestParam[client_course_id]':app.program.program_code,
			'requestParam[client_location_id]':settings.ADHOC_EDUVANZ_CLIENT_LOCATION_ID,
			'requestParam[course_amount]':app.amount_requested,
			'requestParam[loan_amount]':app.amount_requested,
			'requestParam[applicant][email_id]':app.email,
			'requestParam[applicant][mobile_number]':app.mobile.national_number,
			'requestParam[applicant][kyc_address_country]':settings.ADHOC_EDUVANZ_KYC_ADDRESS_COUNTRY,
			'requestParam[applicant][kyc_address_pin]':app.pin_code,
			'requestParam[applicant][first_name]':app.full_name,
		}

		return context	

@method_decorator([require_POST, csrf_exempt,], name='dispatch')
class CallBackView(View):
	def post(self, request, *args, **kwargs):
		received_json_data = json.loads(request.body)
		error_list = []

		for d in received_json_data['els_response']:
			try:
				with transaction.atomic():
					app = AdhocEduvanzApplication.objects.get(order_id=d['meta_data'])
					callback_meta = app.callback_meta or []
					callback_meta.append(d)
					app.callback_meta = callback_meta
					app.status_code = d['current_stage_code']
					app.lead_id = d['lead_id']
						
					if d['current_stage_code'] == 'ELS301':
						app.approved_or_rejected_on = timezone.now()
						app.amount_approved = d['disbursal_amount']
						ofp = OtherFeePayment.objects.get(program=app.program, fee_type=app.fee_type, email=app.email)
						ofp.paid_on = timezone.now()
						ofp.transaction_id = d['meta_data']
						ofp.payment_bank = 'Eduvanz'
						ofp.save()

					elif d['current_stage_code'] == 'ELS402':
						app.approved_or_rejected_on = timezone.now()

					app.save()
					

			except Exception as e:
				error_list.append(str(e))

		context = {
			'status': 'fail' if error_list else 'success',
			'message': ','.join(error_list) if error_list else 'adhoc eduvanz callback was hit...',
			'error_code': 'es_500' if error_list else '',
			'error': 'Internal Server Error' if error_list else 'NA',
			'response_time_stamp': str(timezone.now())
		}

		return JsonResponse(context)


