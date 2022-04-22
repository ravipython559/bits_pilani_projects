from __future__ import unicode_literals
from django.db import models
import jsonfield
from bits_rest import zest_statuses as ZS 
from registrations.models import Program , StudentCandidateApplication
from phonenumber_field.modelfields import PhoneNumberField

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

class AdhocZestEmiTransaction(models.Model):
	ZEST_STATUS_CHOICES = ZS.ZEST_STATUS_CHOICES

	email = models.EmailField()
	program = models.ForeignKey(Program, related_name='%(class)s_prog', blank=True, null=True)
	fee_type = models.CharField(max_length=45, )
	
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
	zest_emi_link = models.TextField(null=True, blank=True)

	is_cancelled = models.BooleanField(default=False)
	cancelled_on = models.DateTimeField(blank=True, null=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.customer_id)

	# class Meta:
	# 	unique_together = ('email','program','fee_type')

class AdhocMetaEmi(models.Model):
	email = models.CharField(max_length=50)
	errors = jsonfield.JSONField(blank=True, null=True)
	created_on_datetime = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.created_on_datetime)

class AdhocEduvanzApplication(models.Model):
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
		(FAILED, 'Applicant Cancelled'),
	)
	
	email = models.EmailField()
	program = models.ForeignKey(Program, related_name='%(class)s_prog', blank=True, null=True)
	fee_type = models.CharField(max_length=45, )
	mobile = PhoneNumberField(blank=True, null=True)
	full_name = models.CharField(max_length=100, blank=True, null=True)
	pin_code = models.CharField(max_length=10, blank=True, null=True)
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

class AdhocEzcredApplication(models.Model):
	INITIAL_STATUS = 'New Loan Application'
	FAILED = 'FAILED'

	email = models.EmailField()
	program = models.ForeignKey(Program, related_name='%(class)s_prog', blank=True, null=True)
	fee_type = models.CharField(max_length=45, )

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

class AdhocPropelldApplication(models.Model):
	INITIAL_STATUS = 'New Loan Application'
	FAILED = 'FAILED'

	quote_id = models.CharField(max_length=50, blank=True, null=True)
	order_id = models.CharField(max_length=100, blank=True, null=True)
	fee_type = models.CharField(max_length=45,blank=True, null=True)
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

		return self.email

		

