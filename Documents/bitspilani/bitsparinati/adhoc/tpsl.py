from registrations.models import *
from .models import AdhocZestEmiTransaction,AdhocEzcredApplication, AdhocPropelldApplication
from . import zest_settings as ZEST
from .zest_utils import (zest_emi_in_progress, zest_emi_in_none, 
	zest_emi_in_decline,
	update_approved_emi, login_approval_update)
from .zest_api import ZestCreateLoan
from adhoc.eduvanz.utils import get_eduvanz_inprogress, get_eduvanz_declined, get_eduvanz_approved
from adhoc.ezcred.utils import get_ezcred_inprogress,get_ezcred_declined
from adhoc.propelld.utils import get_propelld_inprogress, get_propelld_innew
from bits_admin.models import StudentCandidateApplicationArchived, CandidateSelectionArchived
from django.conf import settings
from django.core import signing
from django.views.generic import FormView, View
from django.views.generic.base import TemplateResponseMixin
from .models import MetaAdhocPayment
from registrations.bits_decorator import *
from dateutil.parser import parse as DATE_PARSE 
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import ModelFormMixin, ProcessFormView
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.db.models import Max
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import HttpResponsePermanentRedirect, JsonResponse
from django.core.urlresolvers import reverse_lazy
import json
import requests
import phonenumbers
import logging
import uuid
import decimal
import re


class BaseAdhocView(SingleObjectMixin, FormView):

	model = OtherFeePayment
	payment_url = settings.PAYMENT_URL

	def get(self, request, *args, **kwargs):
		self.object = self.get_object()
		return super(BaseAdhocView, self).get(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		return super(BaseAdhocView, self).post(request, *args, **kwargs)

	def get_initial(self):
		self.sca = self.get_sca()
		self.cs = self.get_cs()
		return self.initial.copy() if not self.sca else {
			'mobile': self.sca.mobile,
			'pin_code': self.sca.pin_code, 
			'full_name': self.sca.full_name,
		}

	def create_log(self):
		seq = self.meta_ofp_model.objects.filter(
			email=self.object.email
		).aggregate(seq=Max('sequence_number'))['seq']

		self.ofp_log, created = self.meta_ofp_model.objects.get_or_create(
			email=self.object.email, 
			sequence_number = (seq or 0) + 1, 
			fee_type=self.object.fee_type, 
			payment_url_requested_on = timezone.now()
		)

		return self.ofp_log

	def update_log(self, field_name=None, value=None):
		setattr(self.ofp_log, field_name, value)
		self.ofp_log.save()

	def get_payment_context_data(self):
		context = {}
		context['email'] = self.object.email
		context['amount'] = str(self.object.fee_amount)
		context['merchantTxnRefNumber'] = "C{0}T{1}".format(self.object.pk, uuid.uuid4().hex)
		context['itc'] = '{0}-{1}'.format(self.object.pk, self.object.program.program_code)
		context['custID'] = self.object.email
		context['requestType'] = self.request_type
		return context

	def get_context_data(self, *args, **kwargs):
		self.sca = self.get_sca()
		self.cs = self.get_cs()
		context = super(BaseAdhocView, self).get_context_data(*args, **kwargs)
		context.update(self.get_payment_context_data())
		login_approval_update(self.object)
		check_ofp = self.model.objects.filter(email=self.object).latest('created_on')
		zest_progress = zest_emi_in_progress(self.object)
		eduvanz = get_eduvanz_inprogress(self.object) 
		ezcred = get_ezcred_inprogress(self.object)
		context['zest_emi_in_progress'] = zest_progress
		context['zest_emi_in_decline'] = zest_emi_in_decline(self.object)
		context['get_eduvanz_inprogress'] = eduvanz
		context['get_eduvanz_declined'] = get_eduvanz_declined(self.object)
		context['get_eduvanz_approved'] = get_eduvanz_approved(self.object)
		context['get_ezcred_inprogress'] = ezcred
		context['get_ezcred_declined'] = get_ezcred_declined(self.object)
		zest_details = AdhocZestEmiTransaction.objects.filter(email=self.object).values()
		if zest_details:
			context['zest_emi_link'] = zest_details[0]['zest_emi_link']
		ezcred_details = AdhocEzcredApplication.objects.filter(email=self.object).values()
		if ezcred_details:
			context['ezcred_link']=ezcred_details[0]['lead_link']
			context['lead_id'] = ezcred_details[0]['lead_id']
			context['ezcred_status'] = ezcred_details[0]['status']
		propelld_values = AdhocPropelldApplication.objects.filter(email=self.object.email).values()
		if propelld_values:
			propelld_details = propelld_values[len(propelld_values)- 1]
			context['propelld_link'] = propelld_details['redirect_url']
			context['propelld_status'] = propelld_values[len(propelld_values)- 1]['status']
		else:
			propelld_details = None
	
		context["enable_ABFL_flag"] = check_ofp.enable_ABFL_flag
		context["enable_eduvenz_flag"] = check_ofp.enable_eduvenz_flag
		context["enable_zest_flag"] = check_ofp.enable_zest_flag
		context["enable_propelld_flag"] = check_ofp.enable_propelld_flag
		context['emi_enabled'] = check_ofp.enable_ABFL_flag or check_ofp.enable_eduvenz_flag or check_ofp.enable_zest_flag
		context['count'] = check_ofp.enable_ABFL_flag and check_ofp.enable_eduvenz_flag and check_ofp.enable_zest_flag
		context['feeType'] = self.object.fee_type
		context['sca'] = self.sca
		context['cs'] = self.cs
		context['ofp'] = self.object
		context['get_propelld_inprogress'] =  get_propelld_inprogress(self.object.email)
		context['get_propelld_innew'] = get_propelld_innew(self.object.email)
		return context

	def get_json_dump_data(self, form):
		mobile = form.cleaned_data['mobile'].as_e164
		full_name = form.cleaned_data['full_name']
		context = self.get_payment_context_data()
		context['customerName'] = full_name
		context['mobileNumber'] = mobile[1:]
		return json.dumps(context)

	def api_post_request(self, form):
		json_data = self.get_json_dump_data(form)
		self.update_log(field_name='payment_url_requested_data', value=json_data)
		req = requests.post(self.payment_url, data=json_data, headers=self.json_headers)
		req.raise_for_status()
		return req.json()

	def post_api_call(self, form):

		try:
			requested_data = self.api_post_request(form)
			self.update_log(field_name='payment_url_response_data', value=requested_data)

			if len(requested_data['responseMessage']) > 10:
				return HttpResponsePermanentRedirect(requested_data['responseMessage'])
			raise Exception('TPSL Response Message: {0}'.format(requested_data['responseMessage']))

		except Exception as e:
			self.update_log(field_name='adhoc_error', value=str(e))
			return render(self.request, self.error_template_name, {'payment_error':str(e)},)

	def form_valid(self, form):
		self.create_log()
		return self.post_api_call(form)

class AdhocMixin(object):
	sca = None
	cs = None
	ofp = None
	ofp_log = None
	request_type = 'ADC'
	json_headers = {'Content-type': 'application/json'}
	sca_model = StudentCandidateApplication
	cs_model = CandidateSelection
	sca_archive_model = StudentCandidateApplicationArchived
	cs_archive_model = CandidateSelectionArchived
	ofp_model = OtherFeePayment
	meta_ofp_model = MetaAdhocPayment

	@property
	def student_application_id(self):
		return  self.sca and self.sca.student_application_id

	def get_arch_sca(self):
		try:
			sca = self.sca_archive_model.objects.get(
				login_email=self.object.email,
				program__program_code=self.object.program.program_code
			)
		except self.sca_archive_model.DoesNotExist:
			sca = None
		return sca

	def get_sca(self):
		try:
			sca = self.sca_model.objects.get(
				login_email__email=self.object.email,
				program=self.object.program,
			)
		except self.sca_model.DoesNotExist:
			sca = self.get_arch_sca()
		return sca

	def get_arch_cs(self):
		try:
			cs = self.cs_archive_model.objects.get(application__student_application_id=self.student_application_id)
		except self.cs_archive_model.DoesNotExist:
			cs = None 
		return cs

	def get_cs(self):
		if self.sca:
			try:
				cs = self.cs_model.objects.get(
					application__login_email__email=self.object.email
				)
			except self.cs_model.DoesNotExist:
				cs = self.get_arch_cs()
			return cs
		return None

class BaseAdhocReturn(View):
	success_payment_status = '0300'
	payment_response_url = settings.PAYMENT_RESPONSE_URL 

	def get_adhoc_log(self):
		seq = self.meta_ofp_model.objects.filter(
			email=self.object.email
		).aggregate(seq=Max('sequence_number'))['seq']
		self.ofp_log, created = self.meta_ofp_model.objects.get_or_create(
			email=self.object.email, 
			sequence_number=seq or 1, 
			fee_type=self.object.fee_type, 
			payment_done_responded_on=timezone.now(),
		)
		return self.ofp_log

	def extract_string(self, search):
		for x in self.client_data:
			if x.startswith(search): return x.replace(search, '')
		else:
			return None 

	def extract_data(self,response_msg=None):

		self.sca = self.get_sca()
		self.cs = self.get_cs()
		self.client_data = re.sub('[{}]', ',', response_msg[7].split('=')[1]).split(',') 
		ctx = {}
		ctx['mobile'] = self.extract_string('mob:') 
		ctx['full_name'] = self.extract_string('custname:')
		ctx['student_id'] = self.cs.student_id if self.cs else None
		ctx['student_application_id'] = self.sca.student_application_id if self.sca else None
		ctx['paid_on'] = DATE_PARSE(response_msg[8].split('=')[1], dayfirst=True)
		ctx['transaction_id'] = response_msg[5].split('=')[1]
		ctx['payment_bank'] = response_msg[4].split('=')[1]
		ctx['gateway_total_amount'] = decimal.Decimal(response_msg[6].split('=')[1])
		ctx['gateway_net_amount'] = decimal.Decimal(response_msg[6].split('=')[1]) - self.object.fee_amount
		return ctx

	def update_log(self, field_name=None, value=None):
		setattr(self.ofp_log, field_name, value)
		self.ofp_log.save()

	def update_ofp(self, response_msg=None):
		context_to_update = self.extract_data(response_msg)
		for key,value in context_to_update.items():
			setattr(self.object, key, value)
		self.object.save()

	def api_request_context(self):
		return json.dumps({'responseMsg': self.request.POST['msg'], 'responseType': self.request_type})

	def api_post_request_data(self):
		json_context = self.api_request_context()
		req = requests.post(self.payment_response_url, data=json_context, headers=self.json_headers)
		req.raise_for_status()
		data = req.json()
		response_msg = data['responseMessage'].split('|')
		payment_status = response_msg[0].split('=')[1]
		return payment_status, response_msg, data, json_context

	def user_payment_data(self, user_meta_data):
		key_value = lambda k,v:(k,v)
		user_data_list = user_meta_data.replace('{',',').replace('}',',').split(',')
		user_data_dict = dict(key_value(*x.split(':')) for x in user_data_list if x )

		return user_data_dict

	def set_ofp(self, user_payment_data):
		pk = user_payment_data['itc'].split('-')[0]
		self.object = OtherFeePayment.objects.get(pk=pk)
		
	def post(self, request, *args, **kwargs):
	
		try:
			payment_status, response_msg, response_data, json_context = self.api_post_request_data()
			user_payment_data = self.user_payment_data(response_msg[7].split('=')[1])
			self.set_ofp(user_payment_data)
			self.get_adhoc_log()
			self.update_log(field_name='payment_done_url_requested_data', value=json_context)

			if payment_status == self.success_payment_status:
				self.update_ofp(response_msg=response_msg)
				self.update_log(field_name='payment_done_url_response_data', value=response_data)
				return render(request, self.template_name, {'ofp':self.object},)
			raise Exception('TPSL Response Message: payment failed status code - {0}'.format(payment_status))
		except Exception as e:
			self.update_log(field_name='adhoc_error', value=str(e))

			return render(request, self.error_template_name, {'payment_error':str(e), 'redirect':reverse_lazy('adhoc:home')}, )

class ZestMixin(object):

	def post(self, request, *args, **kwargs):


		self.object = self.get_object()
		if zest_emi_in_progress(self.object) or zest_emi_in_none(self.object):
			zest_details = AdhocZestEmiTransaction.objects.filter(email=self.object.email)
			if zest_details:
				if zest_details[0].zest_emi_link:
					return HttpResponsePermanentRedirect(zest_details[0].zest_emi_link)
				else:
					return HttpResponsePermanentRedirect(ZEST.ZEST_PORTAL_LINK)
			else:
				return HttpResponsePermanentRedirect(ZEST.ZEST_PORTAL_LINK)
			
		return super(ZestMixin, self).post(request, *args, **kwargs)

	def post_api_call(self, form):
		mobile = form.cleaned_data['mobile']
		pin_code = form.cleaned_data['pin_code']

		try:
			emi = ZestCreateLoan(self.object, pin_code, mobile)
			return emi()
		except Exception as e:
			error = None
			if emi.error_request.status_code == 400:
				error = emi.error_request.json()
			errors_list = {'request_error':str(e), 'zest_error':error, 'occured': 'while creation'}
					
			self.adhoc_error_model.objects.create(email=self.object.email, errors=errors_list)

		return render(
			self.request, 
			self.error_template_name, 
			{'payment_error':"validation failed"},
		)
