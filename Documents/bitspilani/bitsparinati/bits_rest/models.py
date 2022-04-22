from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from registrations.models import StudentCandidateApplication, Program
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
import jsonfield
from bits_rest import zest_statuses as ZS 
import binascii
import os
import uuid

# Create your models here.

class MetaAdhocPayment(models.Model):
	email = models.EmailField()
	payment_url_requested_on = models.DateTimeField(blank=True, null=True)
	payment_url_requested_data = jsonfield.JSONField(blank=True, null=True)
	payment_url_response_data = jsonfield.JSONField(blank=True, null=True)

	payment_done_responded_on = models.DateTimeField(blank=True, null=True)
	payment_done_url_requested_data = jsonfield.JSONField(blank=True, null=True) 
	payment_done_url_response_data = jsonfield.JSONField(blank=True, null=True)

	fee_type = models.CharField(max_length=100)
	sequence_number = models.IntegerField()
	adhoc_error = models.TextField(blank=True, null=True) #error while processing

	def __unicode__(self):
		"""Return unicode."""
		return self.email

class ZestEmiTransaction(models.Model):
	ZEST_STATUS_CHOICES = ZS.ZEST_STATUS_CHOICES
	application = models.ForeignKey(StudentCandidateApplication, related_name='%(class)s_1')
	program = models.ForeignKey(Program, related_name='%(class)s_2')
	order_id = models.TextField()
	customer_id = models.TextField()
	requested_on = models.DateTimeField()
	is_application_complete = models.BooleanField(default=False)
	approved_or_rejected_on = models.DateTimeField(blank=True, null=True)
	is_approved = models.BooleanField(default=False)
	is_terms_and_condition_accepted = models.BooleanField(default=False)
	req_json_data = jsonfield.JSONField(blank=True, null=True)
	amount_requested = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	amount_approved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	status = models.CharField(max_length=50, choices=ZEST_STATUS_CHOICES, blank=True, null=True)
	is_cancelled = models.BooleanField(default=False)
	cancelled_on = models.DateTimeField(blank=True, null=True)
	zest_emi_link = models.TextField(null=True, blank=True)
	callback_meta = jsonfield.JSONField(blank=True, null=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.customer_id)

class EduvanzApplication(models.Model):
	INITIAL_STATUS = 'New Loan Application'
	FAILED = 'FAILED'

	EDUVANZ_CHOICES = (
		(None, '-'),
		(INITIAL_STATUS, 'New Loan Application'),
		('ELS101', 'LAF Pending'),
		('ELS102', 'Documents Pending'),
		('ELS201', 'Under Approval'),
		('ELS202', 'Approved'),
		('ELS203', 'Processing Fee Paid'),
		('ELS204', '1st EMI Paid'),
		('ELS205', 'Both Processing Fee & 1st EMI Paid'),
		('ELS206', 'Agreement Signed'),
		('ELS207', 'NACH Received'),
		('ELS208', 'NACH Under Activation Process'),
		('ELS209', 'NACH Activated'),
		('ELS210', 'Disbursal Initiated'),
		('ELS211', 'Down Payment Paid'),
		('ELS212', 'NACH Rejected'),
		('ELS301', 'Disbursed'),
		('ELS401', 'Rejected'),
		('ELS402', 'Dropped'),
		('FAILED', 'Applicant Cancelled'),
	)
	
	application = models.ForeignKey(StudentCandidateApplication, related_name='%(class)s_app')
	order_id = models.CharField(max_length=100, blank=True, null=True)
	is_approved = models.BooleanField(default=False)
	is_terms_and_condition_accepted = models.BooleanField(default=False)
	amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
	amount_approved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	status_code = models.CharField(max_length=25, default=INITIAL_STATUS, choices=EDUVANZ_CHOICES)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True) 
	approved_or_rejected_on = models.DateTimeField(blank=True, null=True)
	lead_id = models.CharField(max_length=25, blank=True, null=True)
	callback_meta = jsonfield.JSONField(blank=True, null=True)
	
	def __unicode__(self):
		return self.order_id

class PaytmHistory(models.Model):
	application = models.ForeignKey(StudentCandidateApplication, related_name='%(class)s_app')
	ORDERID = models.CharField('ORDER ID', max_length=100)
	TXNDATE = models.DateTimeField('TXN DATE', default=timezone.now)
	TXNID = models.CharField('TXN ID', max_length=100,)
	BANKTXNID = models.CharField('BANK TXN ID', null=True, blank=True, max_length=100)
	BANKNAME = models.CharField('BANK NAME', max_length=50, null=True, blank=True)
	RESPCODE = models.CharField('RESP CODE', max_length=100)
	PAYMENTMODE = models.CharField('PAYMENT MODE', max_length=10, null=True, blank=True)
	CURRENCY = models.CharField('CURRENCY', max_length=10, null=True, blank=True)
	GATEWAYNAME = models.CharField("GATEWAY NAME", max_length=30, null=True, blank=True)
	MID = models.CharField(max_length=100,)
	RESPMSG = models.TextField('RESP MSG', max_length=250)
	TXNAMOUNT = models.CharField('TXN AMOUNT', max_length=100)
	STATUS = models.CharField('STATUS', max_length=12)

	def __unicode__(self):
		return self.STATUS

class MetaZest(models.Model):
	user = models.ForeignKey(User,related_name='%(class)s_user',)
	errors = jsonfield.JSONField(blank=True, null=True)
	created_on_datetime = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		return unicode(self.created_on_datetime)

class Agent(models.Model):
	username = models.CharField(max_length=45, unique=True)
	password = models.CharField(max_length=128)
	key = models.CharField(max_length=40)
	last_updated_on = models.DateTimeField(auto_now=True)
	timeout = models.DurationField(default=timezone.timedelta(minutes=10))

	def save(self, *args, **kwargs):
		if not self.key:
			self.key = self.generate_key()
		return super(Agent, self).save(*args, **kwargs)

	def generate_key(self):
		return binascii.hexlify(os.urandom(20)).decode()

	def __unicode__(self):
		return unicode(self.username)

class InBoundCall(models.Model):
	agent_id = models.CharField(max_length=45)
	called_on = models.DateTimeField()
	customer_name = models.CharField(max_length=45)
	comment = models.TextField(blank=True, null=True)
	cust_email = models.EmailField()
	city = models.CharField(max_length=45, blank=True, null=True)
	emi_enquiry_flag = models.BooleanField(default=False)
	created_on = models.DateTimeField(auto_now_add=True)
	application = models.ManyToManyField(StudentCandidateApplication, blank=True)

	def __unicode__(self):
		return unicode(self.agent_id)

class InBoundProgramInterested(models.Model):
	bound = models.ForeignKey(InBoundCall, related_name='%(class)s_bound',)
	program = models.CharField(max_length=60)
	data_type = models.CharField(max_length=60)

	def __unicode__(self):
		return unicode(self.data_type)

class InBoundPhone(models.Model):
	bound = models.ForeignKey(InBoundCall, related_name='%(class)s_bound',)
	phone = PhoneNumberField()
	data_type = models.CharField(max_length=60)

	def __unicode__(self):
		return unicode(self.data_type)

class InBoundQuery(models.Model):
	bound = models.ForeignKey(InBoundCall, related_name='%(class)s_bound',)
	query = models.TextField()
	data_type = models.CharField(max_length=60)

	def __unicode__(self):
		return unicode(self.data_type)

class InBoundVOC(models.Model):
	bound = models.ForeignKey(InBoundCall, related_name='%(class)s_bound',)
	content = models.TextField()
	data_type = models.CharField(max_length=60)

	def __unicode__(self):
		return unicode(self.data_type)

class OutBoundCall(models.Model):
	agent_id = models.CharField(max_length=45)
	called_on = models.DateTimeField()
	desposition = models.CharField(max_length=45)
	customer_name = models.CharField(max_length=45)
	cust_email = models.EmailField()
	current_status = models.CharField(max_length=45)
	call_response = models.CharField(max_length=45)
	dialer_status = models.CharField(max_length=45)
	comment = models.TextField(blank=True, null=True)
	emi_enquiry_flag = models.BooleanField(default=False)
	call_type = models.CharField(max_length=45, blank=True, null=True)
	city = models.CharField(max_length=45, blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True)
	program = models.CharField(max_length=60)
	application = models.ManyToManyField(StudentCandidateApplication, blank=True)

	def __unicode__(self):
		return unicode(self.agent_id)

class OutBoundProgramInterested(models.Model):
	bound = models.ForeignKey(OutBoundCall, related_name='%(class)s_bound',)
	program = models.CharField(max_length=60)
	data_type = models.CharField(max_length=60)

	def __unicode__(self):
		return unicode(self.data_type)

class OutBoundPhone(models.Model):
	bound = models.ForeignKey(OutBoundCall, related_name='%(class)s_bound',)
	phone = PhoneNumberField()
	data_type = models.CharField(max_length=60)

	def __unicode__(self):
		return unicode(self.data_type)

class OutBoundQuery(models.Model):
	bound = models.ForeignKey(OutBoundCall, related_name='%(class)s_bound',)
	query = models.TextField()
	data_type = models.CharField(max_length=60)

	def __unicode__(self):
		return unicode(self.data_type)

class OutBoundVOC(models.Model):
	bound = models.ForeignKey(OutBoundCall, related_name='%(class)s_bound',)
	content = models.TextField()
	data_type = models.CharField(max_length=60)

	def __unicode__(self):
		return unicode(self.data_type)



class EzcredApplication(models.Model):
	INITIAL_STATUS = 'New Loan Application'
	FAILED = 'FAILED'

	application = models.ForeignKey(StudentCandidateApplication, related_name='%(class)s_app')
	order_id = models.CharField(max_length=100, blank=True, null=True)
	lead_id = models.CharField(max_length=25, blank=True, null=True)
	lead_link = models.CharField(max_length=100, blank=True, null=True)
	is_approved = models.BooleanField(default=False)
	is_terms_and_condition_accepted = models.BooleanField(default=False)
	amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
	amount_approved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	status = models.CharField(max_length=25,default=INITIAL_STATUS,)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)
	approved_or_rejected_on = models.DateTimeField(blank=True, null=True)
	callback_meta = jsonfield.JSONField(blank=True, null=True)
	request_body_meta = jsonfield.JSONField(blank=True, null=True)

	def __unicode__(self):
		return self.order_id


class EzcredApplicationcanceledloans(models.Model):
    email = models.CharField(max_length=100, blank=True, null=True)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    lead_id = models.CharField(max_length=25, blank=True, null=True)
    lead_link = models.CharField(max_length=100, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_terms_and_condition_accepted = models.BooleanField(default=False)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=25)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    approved_or_rejected_on = models.DateTimeField(blank=True, null=True)
    callback_meta = jsonfield.JSONField(blank=True, null=True)
    request_body_meta = jsonfield.JSONField(blank=True, null=True)

    def __unicode__(self):
        return self.order_id

class MetaEzcredexceptions(models.Model):
	email = models.CharField(max_length=100, blank=True, null=True)
	errors = jsonfield.JSONField(blank=True, null=True)
	created_on_datetime = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		return unicode(self.created_on_datetime)


class PropelldApplication(models.Model):
	INITIAL_STATUS = 'New Loan Application'
	FAILED = 'FAILED'

	quote_id = models.CharField(max_length=50, blank=True, null=True)
	application = models.ForeignKey(StudentCandidateApplication, related_name='%(class)s_app')
	program = models.ForeignKey(Program,related_name='%(class)s_requests_created_6',blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True)
	full_name = models.CharField('Full Name',max_length=100)
	email = models.CharField(max_length=100, blank=True, null=True)
	mobile = PhoneNumberField()
	loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=25,default=INITIAL_STATUS,)
	updated_on = models.DateTimeField(auto_now=True)
	disbursed_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	utr_number = models.CharField(max_length=50, blank=True, null=True)
	callback_body_meta = jsonfield.JSONField(blank=True, null=True)
	disbursement_date = models.DateTimeField(blank=True, null=True)

	redirect_url = models.CharField(max_length=300, blank=True, null=True)

	def __unicode__(self):
		return self.quote_id		
