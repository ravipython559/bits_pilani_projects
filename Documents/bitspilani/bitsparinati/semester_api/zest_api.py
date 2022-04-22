from semester_api.models import SemZestEmiTransaction
from django.http import HttpResponsePermanentRedirect
from django.utils import timezone
from bits_rest import zest_statuses as ZS
from bits_rest.zest_api import (APIMixin,
	ZestApi as BaseZestApi, 
	ZestCreateLoan as BaseZestCreateLoan, 
	ZestReport as BaseZestReport,
	ZestCallBack as BaseZestCallBack)
from django.db import IntegrityError, transaction
from semester_api import zest_settings as ZEST 
import json
import requests
import uuid

class ZestApi(BaseZestApi):
	content_type = 'application/json'
	bits_domain = ZEST.BITS_DOMAIN
	error_request = None
	client_id = ZEST.ZEST_CLIENT_ID
	client_secret = ZEST.ZEST_CLIENT_SECRET

class ZestSingleUserMixin(APIMixin):
	auth = None
	model_zest = SemZestEmiTransaction
	content_type = 'application/json'
	bits_domain = ZEST.BITS_DOMAIN
	error_request = None
	client_id = ZEST.ZEST_CLIENT_ID
	client_secret = ZEST.ZEST_CLIENT_SECRET
 
	@property
	def headers(self):
		return {
		'Content-type': self.content_type,
		'Authorization': 'Bearer {}'.format(self.auth.ctx.get('access_token')),
		} 

	def get_merchant_credentials(self, student_id):
		m_id = ZEST.ZEST_CLIENT_ID
		m_sec = ZEST.ZEST_CLIENT_SECRET
		# get_student_id = SemZestEmiTransaction.objects.get(order_id=student_id).student_id
		# if get_student_id:
		if student_id:
			if student_id[4:8] == '17BH':
				m_id = ZEST.HCL_ZEST_CLIENT_ID
				m_sec = ZEST.HCL_ZEST_CLIENT_SECRET
		return dict(client_id=m_id, client_secret=m_sec)

	def __init__(self, student_id=None):
		self.auth = ZestApi(**self.get_merchant_credentials(student_id))

class ZestCreateLoan(ZestSingleUserMixin, BaseZestCreateLoan):
	@property
	def order_id(self):
		return self._order_id

	@order_id.setter
	def order_id(self, value):
		self._order_id = ZEST.ORDER_ID_FORMAT.format(seq=value)

	@property
	def list_of_basket(self):
		basket = {
			'Id': self.student_id,
			'Description': "emi program for {}".format(self.student_id),
			'Quantity': 1,
			'TotalPrice': float(self.basket_amount),
			'Category': 'WILP'
		}
		baskets = [basket,]
		return baskets

	def __init__(self, student_id, email, b_amount, pincode, mobile ):
		super(ZestCreateLoan, self).__init__(student_id)
		self.basket_amount = b_amount
		self.order_id = str(uuid.uuid4())
		self.email = email
		self.student_id = student_id
		self.pincode = pincode
		self.mobile = mobile

	def get_context_data(self):
		context = {}
		context['BasketAmount'] = float(self.basket_amount)
		context['OrderId'] = self.order_id
		context['DeliveryPostCode'] = self.pincode
		context['ReturnUrl'] = ZEST.get_return_url() 
		context['ApprovedUrl'] = ZEST.get_success_url()
		context['MerchantCustomerId'] = self.email
		context['EmailAddress'] = self.email
		context['FullName'] = None
		context['City'] = None
		context['AddressLine1'] = None
		context['AddressLine2'] = None
		context['MobileNumber'] = self.mobile
		context['CallbackUrlBase'] = ZEST.get_callback_url()  
		context['CustomerHasPriorPurchase'] = False
		context['DownpaymentAmount'] = None 
		context['Basket'] = self.list_of_basket
		return context

	def get_or_create(self, req_data,zest_link):
		return self.model_zest.objects.get_or_create(
			student_id=self.student_id,
			order_id=self.order_id,
			customer_id=self.email,
			zest_emi_link=zest_link,
			defaults={ 
				'req_json_data':req_data,
				'requested_on':timezone.localtime(timezone.now()),
			}
		)

	def __call__(self):
		data = self.get_context_data()
		response = self.json_post(ZEST.LOAN_CREATION_URL, json=data, headers=self.headers)
		self.get_or_create(req_data=data, zest_link=response['LogonUrl'])
		return response['LogonUrl']

class ZestReport(ZestSingleUserMixin, BaseZestReport):

	@property
	def zest_objects(self):
		return self.model_zest.objects.filter(student_id=self.student_id).exclude(status__in=ZS.cancelled_status)
		# return self.model_zest.objects.filter(order_id=self.student_id).exclude(status__in=ZS.cancelled_status)

	@property
	def update_complete_process(self):
		return self._activate_loan() 

	def __init__(self, student_id, *args, **kwargs):
		self.student_id = student_id
		super(ZestReport, self).__init__(student_id,*args, **kwargs)

# class ZestCallBack(ZestSingleUserMixin, BaseZestCallBack):
# 	@property
# 	def zest_objects(self):
# 		return self.model_zest.objects.filter(student_id=self.student_id).exclude(status__in=ZS.cancelled_status)
	
# 	@property
# 	def update_complete_process(self):
# 		return self._activate_loan() 

class sem_ZestCallBack(ZestSingleUserMixin):
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
		return self.json_get(url, headers=self.headers)

	def _update_zest_instance_status(self):
		zest = SemZestEmiTransaction.objects.get(order_id=self.order_id)
		order_request = self.user_order(zest.order_id)
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

	def zest_object(self, status):
		self._zest = SemZestEmiTransaction.objects.get(order_id=self.order_id)
		if status:
			self._zest.status = status
			self._zest.save()
		return self._zest

	def __init__(self, order_id, status):
		self.order_id = order_id
		self.zest_status = status
		super(sem_ZestCallBack, self).__init__(order_id)

	def _activate_loan(self):
		loan_activated = False
		call_back_status = self.zest_object(self.zest_status)
		if call_back_status.status in [ZS.Approved, ZS.Active]:
			response = self._delivery_status('d')
			loan_activated = self._active_status()
		return loan_activated 

	@property
	def update_complete_process(self):
		return self._activate_loan() 

	def __call__(self):
		is_process_complete = False
		with transaction.atomic():
			is_process_complete = self.update_complete_process
		return is_process_complete

class ZestDeleteLoan(ZestSingleUserMixin):

	@property
	def zest_cancell_object(self):
		try:
			zest = self.model_zest.objects.get(
				student_id=self.student_id, 
				status__in=ZS.incancelled_status
			)
		except self.model_zest.DoesNotExist as e:
			zest = None
		return zest

	def cancell_zest(self, instance):
		url = ZEST.LOAN_DELETE_URL.format(orderId=instance.order_id)
		response = self.post(url, headers=self.headers)
		instance.__dict__.update(is_cancelled=True, cancelled_on=timezone.now())
		instance.save()
		zr = ZestReport(self.student_id)

	def __init__(self, student_id, *args, **kwargs):
		self.student_id = student_id
		super(ZestDeleteLoan, self).__init__(student_id, *args, **kwargs)

	def __call__(self):
		zr = ZestReport(self.student_id)
		zest_object = self.zest_cancell_object
		cancelled = False
		if zest_object and not zest_object.is_cancelled:
			self.cancell_zest(zest_object)
			cancelled = True

		return cancelled