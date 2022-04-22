from bits_rest.zest_api import ZestCreateLoan, ZestCallBack, ZestDeleteLoan
import requests
import hashlib
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.generic import TemplateView, View
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from registrations.bits_decorator import applicant_status_permission
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from registrations.models import (ApplicantExceptions, 
	StudentCandidateApplication, CandidateSelection)
from bits_rest.models import ZestEmiTransaction
from registrations.review_views import AdmissionFeeView
from registrations.extra_forms import ZestForm
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import (render, redirect, HttpResponseRedirect)
from bits_rest.zest_utils import (emi_in_progress, emi_in_none, 
	get_merchant_credentials, update_approved_emi)
from bits_rest.models import MetaZest
from django.http import JsonResponse
from bits import zest_settings as ZEST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from bits_rest import zest_statuses as ZS
from django.utils import timezone
from bits_rest.bits_utils import complete_admission_process

@method_decorator([
		login_required, 
		never_cache, 
		applicant_status_permission(settings.APP_STATUS[9][0]),
	],
	name='dispatch'
)
class ZestCreateEMI(AdmissionFeeView):
	errors_list = None
	zest_error_model = MetaZest

	def delete_zest(self, request):
		is_deleted = False
		if 'zest_cancell' in request.POST:
			emi = ZestDeleteLoan(request.user.email)
			emi()
			is_deleted = True
		return is_deleted

	def post(self, request, *args, **kwargs):

		self.object = self.get_object()
		is_deleted = self.delete_zest(request)

		if is_deleted:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))

		form = ZestForm(request.POST, prefix='zest')

		if form.is_valid():
			try:
				update_approved_emi(self.object.login_email.email)
			except Exception as e:
				pass
				
			if emi_in_progress(self.object.login_email.email) or emi_in_none(self.object.login_email.email):
				zest_details = ZestEmiTransaction.objects.filter(application__login_email__email=self.object.login_email.email).latest('requested_on')
				zest_emi_link = zest_details.zest_emi_link
				return HttpResponsePermanentRedirect(zest_emi_link)
			try:
				emi = ZestCreateLoan(request.user.email)
				return emi()
			except Exception as e:
				error = None
				if emi.error_request.status_code == 400:
					error = emi.error_request.json()
				errors_list = {'request_error':str(e), 'zest_error':error, 
				'occured': 'while creation'}
						
				self.zest_error_model.objects.create(user=self.object.login_email, errors=errors_list)

		context = self.get_context_data(form=form, errors_list=self.errors_list, **kwargs)
		return self.render_to_response(context)

@method_decorator([csrf_exempt, never_cache,],name='dispatch')
class ZestCallbackView(View):
	zest_error_model = MetaZest
	model_zest = ZestEmiTransaction
	model_ae = ApplicantExceptions
	key_format = '{o_id}|{sec_key}|{status}'
	sha512 = lambda self, o_id, sec_key, status: hashlib.sha512(
		ZEST.CALLBACK_KEY_FORMAT.format(o_id=o_id, 
			sec_key=sec_key, status=status
			)
		).hexdigest()


	def create_error_logs(self, status_msg, o_id, status, key):
		errors_list = {'zest_error':status_msg, 'occured':'while callback',
			'o_id': o_id, 'status':status, 'key':key}
		self.zest_error_model.objects.create(user=self.ZET.application.login_email, 
			errors=errors_list)

	def post(self, request, *args, **kwargs):
		# o_id = request.POST.get('orderno')
		# status = request.POST.get('status')
		# key = request.POST.get('key')

		import json
		o_id = json.loads(request.body).get('transactionDetails').get('partnerTransactionId')
		status = json.loads(request.body).get('transactionDetails').get('status')
		key = json.loads(request.body).get('transactionDetails').get('key')

		sec_key = ZEST.ZEST_TO_MERCHANT
		key_matched = self.sha512(o_id, sec_key, status)==key

		try:
			self.ZET = self.model_zest.objects.get(order_id=o_id)
		except Exception as e:
				status_type, status_msg = 'failed', str(e)
				return JsonResponse({'status':status_type, 'msg':status_msg})

		status_satisfied = self.ZET.application.application_status==settings.APP_STATUS[9][0]
		if  key_matched and status_satisfied:
			try:
				callback_meta = self.ZET.callback_meta or []
				callback_meta.append(json.loads(request.body))
				self.ZET.callback_meta = callback_meta

				if status == ZS.Active:
						self.ZET.approved_or_rejected_on = timezone.localtime(timezone.now())
						self.ZET.is_terms_and_condition_accepted = True
						self.ZET.is_approved = True
						self.ZET.status = status
						self.ZET.save()
						complete_admission_process(self.ZET.application.login_email.email)

				elif status=='Declined':
					self.ZET.approved_or_rejected_on = timezone.localtime(timezone.now())

				self.ZET.status = status
				self.ZET.save()
				status_type, status_msg = 'success', 'successfully updated'
			except Exception as e:
				status_type, status_msg = 'failed', str(e)
				self.create_error_logs(status_msg, o_id, status, key)

		else:
			status_type = 'failed'
			status_msg = 'sha512 key matched: {}\ncurrent_application_status: {}'.format(
				key_matched, self.ZET.application.application_status)
			self.create_error_logs(status_msg, o_id, status, key)

		return JsonResponse({'status':status_type, 'msg':status_msg})
