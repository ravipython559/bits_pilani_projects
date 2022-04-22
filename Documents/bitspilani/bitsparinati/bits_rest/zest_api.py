from registrations.models import StudentCandidateApplication, PROGRAM_FEES_ADMISSION, ApplicantExceptions
from bits_rest.models import ZestEmiTransaction
from django.http import HttpResponsePermanentRedirect
from django.utils import timezone
from bits_rest import zest_statuses as ZS
from bits_rest.bits_utils import complete_admission_process
from django.db import IntegrityError, transaction
from bits import zest_settings as ZEST 
import json
import requests
import uuid
from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponseRedirect

class APIMixin(object):
	content_type = 'application/json'
	bits_domain = ZEST.BITS_DOMAIN
	error_request = None
	client_id = ZEST.ZEST_CLIENT_ID
	client_secret = ZEST.ZEST_CLIENT_SECRET

	def get(self, *args, **kwargs):
		request = None
		try:
			request = requests.get(*args, **kwargs)
			request.raise_for_status()
		except Exception as e:
			self.error_request = request
			request.raise_for_status()
		return request

	def json_get(self, *args, **kwargs):
		return self.get(*args, **kwargs).json()

	def post(self, *args, **kwargs):
		request = None
		try:
			request = requests.post(*args, **kwargs)
			request.raise_for_status()
		except Exception as e:
			self.error_request = request
			request.raise_for_status()
		return request

	def json_post(self, *args, **kwargs):
		return self.post(*args, **kwargs).json()

class ZestPlan(APIMixin):
	return_data = None

	def __init__(self, loan_amount, down_pay_amount=None):
		self.loan_amount = loan_amount
		self.down_pay_amount = down_pay_amount
		self.return_data = self.get_plans()

	def get_plans(self):
		data = {'merchantId': self.client_id, 
			'LoanAmount': self.loan_amount,
			'DownpaymentAmount': self.down_pay_amount
		}
		return self.json_get(ZEST.PLAN_URL, params=data)

	def recommended_emi(self):
		return self.return_data['RecommendedEmiOptions']

	def recommended_default_emi(self):
		default_emi = None
		for emi in self.return_data['RecommendedEmiOptions']:
			if emi['IsDefault']: default_emi = emi
		return default_emi

	def other_emi(self):
		return self.return_data['OtherEmiOptions']

	def other_default_emi(self):
		default_emi = None
		for emi in self.return_data['OtherEmiOptions']:
			if emi['IsDefault']: default_emi = emi
		return default_emi

class ZestApi(APIMixin): 
	ctx = None

	def __init__(self, client_id=None, client_secret=None):
		self.client_id = client_id or self.client_id
		self.client_secret = client_secret or self.client_secret
		self.ctx = self.authenticate()

	def authenticate(self):
		data = {'grant_type':ZEST.ZEST_GRANT_TYPE,
			'scope':ZEST.ZEST_SCOPE,
			'client_id':self.client_id,
			'client_secret':self.client_secret
		}
		return self.json_post(ZEST.AUTH_URL, data=data)

class ZestSingleUser(APIMixin):
	auth = None
	model_zest = ZestEmiTransaction
	model_sca = StudentCandidateApplication
	model_ae = ApplicantExceptions

	@property
	def sca(self):
		return self._sca

	@sca.setter
	def sca(self, value):
		self._sca = self.model_sca.objects.get(login_email__email=value)

	@property
	def zest_objects(self):
		return self.model_zest.objects.filter(application=self.sca).exclude(status__in=ZS.cancelled_status)
 
	@property
	def headers(self):
		return {
		'Content-type': self.content_type,
		'Authorization': 'Bearer {}'.format(self.auth.ctx.get('access_token')),
		}

	def get_program(self):
		try:
			ap_exp =self.model_ae.objects.get(
				applicant_email=self.sca.login_email.email,
				program=self.sca.program
			)
			return ap_exp.transfer_program or self.sca.program
		except self.model_ae.DoesNotExist:
			return self.sca.program 


	def get_merchant_credentials(self, value):
		self.sca = value
		self.program = self.get_program()
		zest = self.program.zest
		if zest is not None:
			m_id = zest.client_id.strip()
			m_sec = zest.client_secret.strip()
		else:
			m_id = ZEST.ZEST_CLIENT_ID
			m_sec = ZEST.ZEST_CLIENT_SECRET

		return dict(client_id=m_id, client_secret=m_sec)

	def __init__(self, value):
		self.auth = ZestApi(**self.get_merchant_credentials(value))

class ZestCreateLoan(ZestSingleUser):
	pfa = PROGRAM_FEES_ADMISSION
	loan_amount = None
	down_pay_amount = None
	errors_list = None

	@property
	def order_id(self):
		return self._order_id

	@order_id.setter
	def order_id(self, value):
		self._order_id = ZEST.ORDER_ID_FORMAT.format(year=self.sca.admit_year, seq=value,)

	@property
	def plan(self):
		return (ZestPlan(self.loan_amount, down_pay_amount=self.down_pay_amount) 
			if self.loan_amount else None)

	@property
	def list_of_basket(self):
		basket = {
			'Id': self.program.program_code,
			'Description': str(self.program),
			'Quantity': 1,
			'TotalPrice': float(self.basket_amount),
			'Category': 'WILP'
		}
		baskets = [basket,]
		return baskets

	@property
	def basket_amount(self):
		return self._basket_amount

	@basket_amount.setter
	def basket_amount(self, b_amount):
		amount = b_amount
		if self.loan_amount is None and b_amount is None:
			pfa = self.pfa.objects.get(
				program=self.program, 
				latest_fee_amount_flag=True,
				fee_type='5'
			)
			amount = pfa.fee_amount
		plan = self.plan
		self._basket_amount = (plan.return_data['BasketAmount'] if plan is not None else amount)

	def __init__(self, email, d_p_amount=None, l_amount=None, b_amount=None):
		super(ZestCreateLoan, self).__init__(email)
		self.loan_amount = l_amount
		self.down_pay_amount = d_p_amount
		self.basket_amount = b_amount
		self.order_id = str(uuid.uuid4())


	def get_or_create(self, req_data, zest_link):
		return self.model_zest.objects.get_or_create(
			application=self.sca,
			order_id=self.order_id,
			customer_id=self.sca.login_email.email,
			zest_emi_link=zest_link,
			defaults={'program':self.program, 
				'req_json_data':req_data,
				'requested_on':timezone.localtime(timezone.now()),
			}
		)

	def get_context_data(self):
		context = {}
		context['BasketAmount'] = float(self.basket_amount)
		context['OrderId'] = self.order_id
		context['DeliveryPostCode'] = self.sca.pin_code
		context['ReturnUrl'] = ZEST.get_return_url() 
		context['ApprovedUrl'] = ZEST.get_success_url()
		context['MerchantCustomerId'] = self.sca.login_email.email
		context['EmailAddress'] = self.sca.login_email.email
		context['FullName'] = self.sca.full_name
		context['City'] = self.sca.city
		context['AddressLine1'] = self.sca.address_line_1
		context['AddressLine2'] = self.sca.address_line_2
		context['MobileNumber'] = self.sca.mobile.as_e164
		context['CallbackUrlBase'] = ZEST.get_callback_url()  
		context['CustomerHasPriorPurchase'] = False
		context['DownpaymentAmount'] = None 
		context['Basket'] = self.list_of_basket
		return context

	def __call__(self):
		data = self.get_context_data()
		response = self.json_post(ZEST.LOAN_CREATION_URL, json=data, headers=self.headers)
		self.get_or_create(req_data=data, zest_link=response['LogonUrl'])
		return HttpResponsePermanentRedirect(response['LogonUrl'])

class OrderReportMixin(object):
	status_choice = dict(d='Delivered', r='Refused')

	def _delivery_status(self, status):
		post_url = ZEST.DELIVERY_REPORT_URL.format(orderId=self.order_id)
		try:
			return self.post(post_url, 
			json={'DeliveryStatus':self.status_choice[status]},
			headers=self.headers)
		except Exception as e: 
			pass

	def user_order(self, o_id):
		url = ZEST.ORDER_STATUS_URL.format(orderId=o_id)
		try:
			return self.json_get(url, headers=self.headers)
		except Exception as e: 
			pass


	def _update_zest_instance_status(self, zest=None):
		zest = zest or self.zest_object
		order_request = self.user_order(zest.order_id)

		# if zest.__class__.__name__!='SemZestEmiTransaction':
		if order_request['OrderStatus'] == 'Declined':
			if zest.status != 'Declined':
				callback_meta = zest.callback_meta or []
				callback_meta.append(order_request)
				zest.callback_meta = callback_meta
				zest.approved_or_rejected_on = timezone.localtime(timezone.now())

		if order_request['OrderStatus'] in ZS.cancelled_status:
			if zest.status not in ZS.cancelled_status:
				callback_meta = zest.callback_meta or []
				callback_meta.append(order_request)
				zest.callback_meta = callback_meta

		if order_request['OrderStatus'] == ZS.Active:
			if zest.status != ZS.Active:
				callback_meta = zest.callback_meta or []
				callback_meta.append(order_request)
				zest.callback_meta = callback_meta

		zest.status = order_request['OrderStatus']
		zest.save()
		return zest

	def _active_status(self):
		loan_activated = False
		zest = self._update_zest_instance_status() 
		if zest.status == ZS.Active:
			zest.approved_or_rejected_on = timezone.localtime(timezone.now())
			zest.is_terms_and_condition_accepted = True
			zest.is_approved = True
			zest.save()
			loan_activated = True
		return loan_activated

class ZestReport(ZestSingleUser, OrderReportMixin):

	@property
	def zest_object(self):
		try:
			zest = self.zest_objects.get(status__in=[ZS.Approved, ZS.Active])
			self.order_id = zest.order_id
		except self.model_zest.DoesNotExist as e:
			zest = None
			self.order_id = None
		return zest 

	def _update_zest_status_of_application(self): 
		for zest in self.zest_objects.iterator():
			try:
				updated_zest = self._update_zest_instance_status(zest)
			except Exception as e: 
				print "fix me. do something amazing here {}".format(e)

	def _activate_loan(self):
		loan_activated = False
		if self.zest_object is not None:
			response = self._delivery_status('d')
			loan_activated = self._active_status()
		return loan_activated

	@property
	def update_complete_process(self):
		return (self._activate_loan() and complete_admission_process(self.sca.login_email.email))

	def __call__(self):
		self._update_zest_status_of_application()
		is_process_complete = False
		with transaction.atomic():
			is_process_complete = self.update_complete_process
		return is_process_complete

class ZestCallBack(ZestSingleUser, OrderReportMixin):

	@property
	def zest_object(self):
		return self._zest

	@zest_object.setter
	def zest_object(self, status):
		self._zest = self.zest_objects.get(order_id=self.order_id)
		if status:
			self._zest.status = status
			self._zest.save()
		return self._zest

	@property
	def sca(self):
		return self._sca

	@sca.setter
	def sca(self, value):
		zest = self.zest_objects.get(order_id=value)
		self._sca = zest.application

	def __init__(self, order_id, status):
		self.order_id = order_id
		self.zest_object = status
		super(ZestCallBack, self).__init__(order_id)

	def _activate_loan(self):
		loan_activated = False
		if self.zest_object.status in [ZS.Approved, ZS.Active]:
			response = self._delivery_status('d')
			loan_activated = self._active_status()
		return loan_activated 

	@property
	def update_complete_process(self):
		return (self._activate_loan() and complete_admission_process(self.sca.login_email.email))

	def __call__(self):
		is_process_complete = False
		with transaction.atomic():
			is_process_complete = self.update_complete_process
		return is_process_complete


class ZestDeleteLoan(ZestSingleUser):

	@property
	def zest_cancell_object(self):
		try:
			zest = self.model_zest.objects.get(
				application=self.sca, 
				status__in=ZS.incancelled_status
			)
		except self.model_zest.DoesNotExist as e:
			zest = None
		return zest

	def cancell_zest(self, instance):
		url = ZEST.LOAN_DELETE_URL.format(orderId=instance.order_id)
		response = self.post(url, headers=self.headers)
		if response.status_code==200:
			instance.__dict__.update(status='MerchantCancelled',is_cancelled=True, cancelled_on=timezone.now())
		else:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		callback_meta = instance.callback_meta or []
		resp_dict = {}
		resp_dict['headers'] = response.headers
		resp_dict['status'] = response.status_code
		resp_dict['url'] = response.url
		callback_meta.append(resp_dict)
		instance.callback_meta = callback_meta
		instance.save()
		# zr = ZestReport(self.sca.login_email.email)

	def __call__(self):
		# zr = ZestReport(self.sca.login_email.email)
		zest_object = self.zest_cancell_object
		cancelled = False
		if not zest_object.is_cancelled:
			self.cancell_zest(zest_object)
			cancelled = True

		return cancelled