from django.shortcuts import render
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
from bits_rest.models import EduvanzApplication
from .forms import ApplicationForm
from .decorators import check_eduvanz_status
from .utils import complete_admission_process
from registrations.models import (StudentCandidateApplication, 
	PROGRAM_FEES_ADMISSION, EDUVANZ_FEE_TYPE, ApplicationPayment)
from registrations.review_views import AdmissionFeeView
import requests
import json

@method_decorator([check_eduvanz_status,], name='dispatch')
class ApplicationCreateView(AdmissionFeeView, CreateView):
	model = EduvanzApplication
	form_class = ApplicationForm
	prefix = 'eduvanz'

	def form_invalid(self, form):
		return self.render_to_response(self.get_context_data(eduvanz_form=form))

	def form_valid(self, form):
		return super(ApplicationCreateView, self).form_valid(form)

	def get_success_url(self):
		return reverse_lazy('bits_rest:eduvanz:api', kwargs={'pk':self.object.pk})

class EduvanzRedirectView(TemplateView):
	template_name = 'eduvanz/landing_page.html'

	def get_context_data(self, **kwargs):
		context = super(EduvanzRedirectView, self).get_context_data(**kwargs)
		context['eduvanz'] = EduvanzApplication.objects.get(pk=kwargs['pk'])
		return context

class Eduvanz(TemplateView):
	template_name = 'eduvanz/payment.html'

	def get_context_data(self, **kwargs):
		app = EduvanzApplication.objects.get(pk=kwargs['pk'])
		context = super(Eduvanz, self).get_context_data(**kwargs)
		context['EDUVANZ_URL'] = settings.EDUVANZ_URL
		context['eduvanzdict'] = {
			'meta_data': app.order_id,
			'userName': settings.EDUVANZ_USERNAME,
			'password': settings.EDUVANZ_PASSWORD,
			'redirect_url': 'http%s://%s%s' % ('s' if self.request.is_secure() else '',
				self.request.get_host(), 
				reverse_lazy('bits_rest:eduvanz:landing', kwargs={'pk':app.pk})
			),
			'requestParam[client_institute_id]':settings.EDUVANZ_CLIENT_INSTITUTE_ID,
			'requestParam[client_course_id]':app.application.program.program_code,
			'requestParam[client_location_id]':settings.EDUVANZ_CLIENT_LOCATION_ID,
			'requestParam[course_amount]':app.amount_requested,
			'requestParam[loan_amount]':app.amount_requested,
			'requestParam[applicant][email_id]':app.application.login_email.email,
			'requestParam[applicant][dob]':app.application.date_of_birth.strftime('%Y-%m-%d'),
			'requestParam[applicant][mobile_number]':app.application.mobile.national_number,
			'requestParam[applicant][kyc_address_country]':settings.EDUVANZ_KYC_ADDRESS_COUNTRY,
			'requestParam[applicant][kyc_address_pin]':app.application.pin_code,
			'requestParam[applicant][first_name]':app.application.full_name,
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
					app = EduvanzApplication.objects.get(order_id=d['meta_data'])
					callback_meta = app.callback_meta or []
					callback_meta.append(d)
					app.callback_meta = callback_meta
					app.status_code = d['current_stage_code']
					app.lead_id = d['lead_id']

					if app.application.application_status == settings.APP_STATUS[9][0]:
						
						if d['current_stage_code'] == 'ELS301':
							app.approved_or_rejected_on = timezone.now()
							app.amount_approved = d['disbursal_amount']
							complete_admission_process(app.application.login_email.email)
							ApplicationPayment.objects.create(
								payment_id=app.order_id,
								payment_amount=app.amount_requested,
								payment_date=timezone.now(),
								payment_bank='Eduvanz',
								transaction_id=app.order_id,
								application=app.application,
								fee_type='1',
								insertion_datetime=timezone.now()
							)

						elif d['current_stage_code'] == 'ELS402':
							app.approved_or_rejected_on = timezone.now()

					app.save()

			except Exception as e:
				error_list.append(str(e))

		context = {
			'status': 'fail' if error_list else 'success',
			'message': ','.join(error_list) if error_list else 'bits eduvanz callback was hit...',
			'error_code': 'es_500' if error_list else '',
			'error': 'Internal Server Error' if error_list else 'NA',
			'response_time_stamp': str(timezone.now())
		}

		return JsonResponse(context)


