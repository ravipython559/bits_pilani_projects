from .models import AdhocZestEmiTransaction
from django.http import HttpResponsePermanentRedirect
from django.utils import timezone
from bits_rest import zest_statuses as ZS
from bits_rest.zest_api import (APIMixin,
	ZestApi as BaseZestApi, 
	ZestCreateLoan as BaseZestCreateLoan, 
	ZestReport as BaseZestReport,
	ZestCallBack as BaseZestCallBack)
from django.db import IntegrityError, transaction
from . import zest_settings as ZEST 
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
	model_zest = AdhocZestEmiTransaction
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

	def get_merchant_credentials(self, value):
		zest = value
		table_name = zest.__class__.__name__

		if table_name != 'AdhocZestEmiTransaction':
			m_id = zest.Zest_Program_Map.client_id
			m_sec = zest.Zest_Program_Map.client_secret
			# m_id = ZEST.ZEST_CLIENT_ID
			# m_sec = ZEST.ZEST_CLIENT_SECRET
		else:
			m_id = ZEST.ZEST_CLIENT_ID
			m_sec = ZEST.ZEST_CLIENT_SECRET
		return dict(client_id=m_id, client_secret=m_sec)

	def __init__(self, value):
		self.auth = ZestApi(**self.get_merchant_credentials(value))

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
			'Id': self.email,
			'Description': "emi program for {}".format(self.email),
			'Quantity': 1,
			'TotalPrice': float(self.basket_amount),
			'Category': 'WILP'
		}
		baskets = [basket,]
		return baskets

	def __init__(self, ofp, pincode, mobile):
		super(ZestCreateLoan, self).__init__(ofp)
		self.ofp = ofp
		self.basket_amount = ofp.fee_amount
		self.order_id = str(uuid.uuid4())
		self.email = ofp.email
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
		context['MobileNumber'] = self.mobile.as_e164
		context['CallbackUrlBase'] = ZEST.get_callback_url()  
		context['CustomerHasPriorPurchase'] = False
		context['DownpaymentAmount'] = None 
		context['Basket'] = self.list_of_basket
		return context

	def get_or_create(self, req_data, zest_link=None):
		return self.model_zest.objects.get_or_create(
			email=self.ofp.email,
			order_id=self.order_id,
			customer_id=self.ofp.email,
			program=self.ofp.program,
			fee_type=self.ofp.fee_type,
			zest_emi_link=zest_link,
			defaults={ 
				'req_json_data':req_data,
				'requested_on':timezone.localtime(timezone.now()),
			}
		)

class ZestReport(ZestSingleUserMixin, BaseZestReport):
	@property
	def zest_objects(self):
		return self.model_zest.objects.filter(
			email=self.ofp.email, 
			program=self.ofp.program,
			fee_type=self.ofp.fee_type,
		).exclude(status__in=ZS.cancelled_status)

	@property
	def update_complete_process(self):
		return self._activate_loan() 

	def __init__(self, ofp, *args, **kwargs):
		self.email = ofp.email
		self.ofp = ofp
		super(ZestReport, self).__init__(ofp,*args, **kwargs)

class ZestCallBack(ZestSingleUserMixin, BaseZestCallBack):
	@property
	def zest_objects(self):
		return self.model_zest.objects.filter(
			order_id=self.order_id
		).exclude(status__in=ZS.cancelled_status)
	
	@property
	def update_complete_process(self):
		return self._activate_loan() 

	def __init__(self, ofp, pincode, mobile):
		super(ZestCallBack, self).__init__()