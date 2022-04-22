from __future__ import unicode_literals

from django.db import models
from registrations.models import StudentCandidateApplication, FEE_TYPE_CHOICES
from phonenumber_field.modelfields import PhoneNumberField
from collections import OrderedDict

class PaymentGatewayRecord(models.Model):

	STATUS_GATEWAY = (
		(None,'Choose'),
		('1', 'Uploaded. Pending Review'),
		('2', 'Matched and Approved'),
		('3', 'Fee Mismatch'),
		('4', 'Approved. Transferred to Application Center'),
		('5', 'Rejected'),
		('6', 'Double Payment. Rejected'),
	)

	src_itc_application = models.ForeignKey(StudentCandidateApplication,
		related_name='%(class)s_app')
	tpsl_transaction_id = models.CharField(max_length=20,)
	bank_id = models.PositiveIntegerField()
	bank_name = models.CharField(max_length=50)
	sm_transaction_id = models.CharField(max_length=45,)
	bank_transaction_id = models.CharField(max_length=45,)
	total_amount = models.FloatField()
	charges = models.FloatField()
	service_tax = models.FloatField()
	net_amount = models.FloatField()
	transaction_date = models.DateTimeField()
	src_itc_user_id = models.CharField(max_length=50)
	src_itc_user_name = models.CharField(max_length=50)
	src_itc_mobile = PhoneNumberField()
	uploaded_by = models.CharField(max_length=50)
	uploaded_on_datetime = models.DateTimeField(auto_now_add=True,)
	payment_file_name = models.CharField(max_length=50)
	payment_report_date = models.DateTimeField(blank=True, null=True)
	status = models.CharField(max_length=30, choices = STATUS_GATEWAY )
	missing_in_application_center = models.BooleanField(default = False)
	accepted_rejected_datetime = models.DateTimeField(blank=True, null=True)
	accepted_rejected_by = models.CharField(max_length=50, blank=True, null=True)

	def __unicode__(self):
		return unicode('{0}'.format(self.tpsl_transaction_id))

	class Meta:
		unique_together = ('src_itc_application','tpsl_transaction_id')

class ManualPaymentDataUpload(models.Model):
	PAYMENT_TYPE = FEE_TYPE_CHOICES
	

	STATUS_MAN = (
		(None,'Choose'),
		('1', 'Uploaded. Pending Review'),
		('2', 'Fee Mismatch'),
		('3', 'Approved'),
		('4', 'Rejected'),
		('5', 'Double Payment. Rejected'),
		)

	application = models.ForeignKey(StudentCandidateApplication,
		related_name='%(class)s_app')
	payment_id = models.CharField(max_length=45, unique=True)
	payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE)
	payment_date = models.DateTimeField()
	payment_amount = models.FloatField()
	payment_mode = models.CharField(max_length=30, blank=True, null=True)
	uploaded_by = models.CharField(max_length=50)
	uploaded_on_date = models.DateTimeField(auto_now_add=True,)
	payment_reversal_flag = models.BooleanField()
	status = models.CharField( max_length=30, choices = STATUS_MAN )
	accepted_rejected_datetime = models.DateTimeField(blank=True, null=True)
	accepted_rejected_by = models.CharField(max_length=50, blank=True, null=True)
	upload_filename = models.CharField(max_length=100)

	def __unicode__(self):
		return unicode('{0}'.format(self.payment_id))

	class Meta:
		unique_together = ('application','payment_type')