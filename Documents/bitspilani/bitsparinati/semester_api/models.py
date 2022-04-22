from __future__ import unicode_literals

from django.db import models
import jsonfield
from bits_rest import zest_statuses as ZS 

# Create your models here.
class SemZestEmiTransaction(models.Model):
	ZEST_STATUS_CHOICES = ZS.ZEST_STATUS_CHOICES
	student_id = models.CharField(max_length=50)
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

class SemMetaZest(models.Model):
	student_id = models.CharField(max_length=50)
	errors = jsonfield.JSONField(blank=True, null=True)
	created_on_datetime = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		"""Return unicode."""
		return unicode(self.created_on_datetime)


class SemPaytmTransactions(models.Model):
	order_id = models.CharField(max_length=100, primary_key=True)
	email = models.CharField(max_length=100, blank=True, null=True)
	student_id = models.CharField(max_length=100, blank=True, null=True)
	created_on = models.DateTimeField(blank=True, null=True)
	transaction_date = models.DateTimeField(blank=True, null=True)
	request_amount = models.CharField(max_length=100, blank=True, null=True)
	transaction_amount = models.CharField(max_length=100, blank=True, null=True)
	mobile = models.CharField(max_length=30, blank=True, null=True)
	transaction_id = models.CharField(max_length=100, blank=True, null=True)
	bank_transaction_id = models.CharField(max_length=100, blank=True, null=True)
	bank_name = models.CharField(max_length=100, blank=True, null=True)
	payment_mode = models.CharField(max_length=100, blank=True, null=True)
	currency = models.CharField(max_length=100, blank=True, null=True)
	gateway_name = models.CharField(max_length=100, blank=True, null=True)
	merchant_id = models.CharField(max_length=100, blank=True, null=True)
	response_message = models.TextField(max_length=500, blank=True, null=True)
	status = models.CharField(max_length=20, blank=True, null=True)
	resp_json = jsonfield.JSONField(blank=True, null=True)
	redirect_url = models.TextField(max_length=500, blank=True, null=True)
