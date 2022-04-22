from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse
from django.utils.translation import get_language
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse_lazy
from registrations.models import (
	StudentCandidateApplication, PROGRAM_FEES_ADMISSION, 
	ApplicationPayment, CandidateSelection, PaytmTransactionStatus,
	)
from registrations.bits_decorator import applicant_status_permission
from django.conf import settings
from bits_rest.bits_extra import student_id_generator
from bits_rest.bits_utils import get_admitted_program
from django_mysql.locks import Lock
from django.utils import timezone
from . import Checksum
import uuid

from bits_rest.models import PaytmHistory
# Create your views here.

@method_decorator([login_required,], name='dispatch')
class Home(TemplateView):
	template_name = 'paytm/home.html'

class Payment(TemplateView):
	template_name = 'paytm/payment.html'

	def get_callback(self):
		raise Exception('require a callback url inherit to its child class')

	def get_context_data(self, **kwargs):
		context = super(Payment, self).get_context_data(**kwargs)
		sca = StudentCandidateApplication.objects.get(login_email=self.request.user)
		data_dict = {
			'MID':settings.PAYTM_MERCHANT_ID,
			'ORDER_ID': str(uuid.uuid4()),
			'TXN_AMOUNT': self.get_amount(),
			'CUST_ID': sca.student_application_id,
			'INDUSTRY_TYPE_ID': settings.PAYTM_INDUSTRY_TYPE_ID,
			'WEBSITE': settings.PAYTM_WEBSITE,
			'CHANNEL_ID':'WEB',
			'MOBILE_NO' : sca.mobile.as_e164,
			'EMAIL' : sca.login_email.email,
			'CALLBACK_URL':self.get_callback(),
		}
		param_dict = data_dict
		param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(
			data_dict, settings.PAYTM_MERCHANT_KEY
		)
		context['paytmdict'] = param_dict
		context['PAYTM_PAYMENT_URL'] = settings.PAYTM_PAYMENT_URL
		PaytmTransactionStatus.objects.create(order_id=data_dict['ORDER_ID'], payment_application_id=data_dict['CUST_ID'],
					email=data_dict['EMAIL'], mobile=data_dict['MOBILE_NO'], request_amount=data_dict['TXN_AMOUNT'],
					created_on=timezone.now(), status='ORDER_ID_CREATED', application=sca)
		return context


@method_decorator([login_required, 
	applicant_status_permission(settings.APP_STATUS[9][0])], name='dispatch')
class AdmissionPaymentView(Payment):

	def get_callback(self):
		return 'http%s://%s%s' % ('s' if self.request.is_secure() else 's', 
			self.request.get_host(), str(reverse_lazy('bits_rest:paytm:adm-response'))
			)

	def get_amount(self):
		sca = StudentCandidateApplication.objects.get(login_email=self.request.user)
		pfa = PROGRAM_FEES_ADMISSION.objects.get(
			program=sca.program, 
			latest_fee_amount_flag=True,
			fee_type='1'
		)
		return pfa.fee_amount

@method_decorator([login_required,
	applicant_status_permission([settings.APP_STATUS[12][0], settings.APP_STATUS[18][0]]),], 
	name='dispatch')
class ApplicationPaymentView(Payment):

	def get_callback(self):
		return 'http%s://%s%s' % ('s' if self.request.is_secure() else 's', 
			self.request.get_host(), str(reverse_lazy('bits_rest:paytm:app-response'))
			)

	def get_amount(self):
		sca = StudentCandidateApplication.objects.get(login_email=self.request.user)
		pfa = PROGRAM_FEES_ADMISSION.objects.get(
			program=sca.program, 
			latest_fee_amount_flag=True,
			fee_type='2'
		)
		return pfa.fee_amount

class CallBack(View):

	def post(self, request, *args, **kwargs):
		data_dict = { k:v for k,v in request.POST.items() }
		verify = Checksum.verify_checksum(
			data_dict, settings.PAYTM_MERCHANT_KEY, 
			data_dict['CHECKSUMHASH']
		)
		
		if verify:
			self.update_models(data_dict)
			return HttpResponseRedirect(reverse_lazy('registrationForm:applicantData'))
		else:
			return HttpResponse("checksum verify failed")

	def get(self, request, *args, **kwargs):
		return HttpResponse(status=200)


@method_decorator([csrf_exempt,], name='dispatch')
class AdmissionCallBack(CallBack):
	def update_models(self, data_dict):

		with transaction.atomic():
			payment_transaction = PaytmTransactionStatus.objects.get(order_id=data_dict['ORDERID'])
			payment_transaction.resp_json=data_dict
			if data_dict.has_key('TXNAMOUNT'):
				payment_transaction.transaction_amount=data_dict['TXNAMOUNT']
			if data_dict.has_key('MID'):
				payment_transaction.merchant_id=data_dict['MID']
			if data_dict.has_key('TXNDATE'):
				payment_transaction.transaction_date=data_dict['TXNDATE']
			if data_dict.has_key('STATUS'):
				payment_transaction.status=data_dict['STATUS']
			if data_dict.has_key('BANKNAME'):
				payment_transaction.bank_name=data_dict['BANKNAME']
			if data_dict.has_key('PAYMENTMODE'):
				payment_transaction.payment_mode=data_dict['PAYMENTMODE']
			if data_dict.has_key('BANKTXNID'):
				payment_transaction.bank_transaction_id=data_dict['BANKTXNID']
			if data_dict.has_key('TXNID'):
				payment_transaction.transaction_id=data_dict['TXNID']
			if data_dict.has_key('CURRENCY'):
				payment_transaction.currency=data_dict['CURRENCY']
			if data_dict.has_key('RESPMSG'):
				payment_transaction.response_message=data_dict['RESPMSG']
			if data_dict.has_key('GATEWAYNAME'):
				payment_transaction.gateway_name=data_dict['GATEWAYNAME']
			payment_transaction.fee_type='1'
			payment_transaction.save()
			sca = StudentCandidateApplication.objects.get(login_email__email=payment_transaction.email)
			PaytmHistory.objects.create(application=sca, **data_dict)
			if data_dict['STATUS'] == 'TXN_SUCCESS':
				pfa = PROGRAM_FEES_ADMISSION.objects.get(
					program=sca.program, 
					latest_fee_amount_flag=True,
					fee_type='1'
				)
				ApplicationPayment.objects.create(application=sca, 
					fee_type='1',
					payment_amount=pfa.fee_amount,
					payment_bank='paytm',
					payment_id=data_dict['ORDERID'],
					transaction_id=data_dict['BANKTXNID'],
					payment_date=timezone.now()
				)
				sca.application_status = settings.APP_STATUS[11][0]
				sca.save()
				cs = CandidateSelection.objects.get(application=sca)

				with Lock('bits_student_id_lock'):
					cs.student_id = student_id_generator(login_email=sca.login_email.email)
					cs.admitted_to_program = get_admitted_program(sca.login_email.email)
					cs.save()



@method_decorator([csrf_exempt,], name='dispatch')
class ApplicationCallBack(CallBack):
	
	def update_models(self, data_dict):
		
		with transaction.atomic():
			payment_transaction = PaytmTransactionStatus.objects.get(order_id=data_dict['ORDERID'])
			payment_transaction.resp_json=data_dict
			if data_dict.has_key('TXNAMOUNT'):
				payment_transaction.transaction_amount=data_dict['TXNAMOUNT']
			if data_dict.has_key('MID'):
				payment_transaction.merchant_id=data_dict['MID']
			if data_dict.has_key('TXNDATE'):
				payment_transaction.transaction_date=data_dict['TXNDATE']
			if data_dict.has_key('STATUS'):
				payment_transaction.status=data_dict['STATUS']
			if data_dict.has_key('BANKNAME'):
				payment_transaction.bank_name=data_dict['BANKNAME']
			if data_dict.has_key('PAYMENTMODE'):
				payment_transaction.payment_mode=data_dict['PAYMENTMODE']
			if data_dict.has_key('BANKTXNID'):
				payment_transaction.bank_transaction_id=data_dict['BANKTXNID']
			if data_dict.has_key('TXNID'):
				payment_transaction.transaction_id=data_dict['TXNID']
			if data_dict.has_key('CURRENCY'):
				payment_transaction.currency=data_dict['CURRENCY']
			if data_dict.has_key('RESPMSG'):
				payment_transaction.response_message=data_dict['RESPMSG']
			if data_dict.has_key('GATEWAYNAME'):
				payment_transaction.gateway_name=data_dict['GATEWAYNAME']
			payment_transaction.fee_type='2'
			payment_transaction.save()
			sca = StudentCandidateApplication.objects.get(login_email__email=payment_transaction.email)
			PaytmHistory.objects.create(application=sca, **data_dict)
			if data_dict['STATUS'] == 'TXN_SUCCESS':
				pfa = PROGRAM_FEES_ADMISSION.objects.get(
					program=sca.program, 
					latest_fee_amount_flag=True,
					fee_type='2'
				)
				ApplicationPayment.objects.create(application=sca, 
					fee_type='2',
					payment_amount=pfa.fee_amount,
					payment_bank='paytm',
					payment_id=data_dict['ORDERID'],
					transaction_id=data_dict['BANKTXNID'],
					payment_date=timezone.now()
				)
				sca.application_status = settings.APP_STATUS[13][0]
				sca.save()
