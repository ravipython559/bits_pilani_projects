from bits_rest import zest_statuses as ZS 
from . import zest_settings as ZEST
from django.conf import settings
from .models import AdhocZestEmiTransaction
from django.db import IntegrityError, transaction
from .zest_api import ZestReport
from registrations.models import OtherFeePayment

def zest_emi_in_progress(ofp):
	emi = AdhocZestEmiTransaction.objects.filter(
		email=ofp.email, 
		status__in=ZS.inprogress_status,
		fee_type=ofp.fee_type,
		program=ofp.program,
	)
	return emi.exists()

def zest_emi_in_none(ofp):
	emi = AdhocZestEmiTransaction.objects.filter(
		email=ofp.email, 
		status__isnull=True,
		fee_type=ofp.fee_type,
		program=ofp.program,
	)
	return emi.exists()


def update_approved_emi(ofp):
	zr = ZestReport(ofp)
	is_loan_activate = zr()
	return is_loan_activate

def login_approval_update(ofp):
	emi_query = AdhocZestEmiTransaction.objects.filter(
		email=ofp.email, 
		program=ofp.program,
		fee_type=ofp.fee_type,
	).exclude(status__in=ZS.cancelled_status)
	
	if emi_query.exists():
		try:
			emi_query.get(status=ZS.Active, is_approved=True,)
			ofp = OtherFeePayment.objects.get(
				email=ofp.email, 
				program=ofp.program,
				fee_type=ofp.fee_type,
			)
			ofp.transaction_id = emi_query.order_id
			ofp.save()
		except AdhocZestEmiTransaction.DoesNotExist as e:
			update_approved_emi(ofp)

def zest_emi_in_decline(ofp):
	try:
		emi = AdhocZestEmiTransaction.objects.get(
			email=ofp.email, 
			program=ofp.program,
			fee_type=ofp.fee_type,
			status=ZS.Declined,
		)
		return True
	except AdhocZestEmiTransaction.DoesNotExist: return False

def zest_emi_in_approved(ofp):
	try:
		emi = AdhocZestEmiTransaction.objects.get(
			email=ofp.email, 
			program=ofp.program,
			fee_type=ofp.fee_type, 
			status=ZS.Approved
		)
		return True

	except AdhocZestEmiTransaction.DoesNotExist: return False

def zest_emi_in_document_complete(ofp):
	try:
		emi = AdhocZestEmiTransaction.objects.get(
			email=ofp.email, 
			program=ofp.program,
			fee_type=ofp.fee_type, 
			status=ZS.DocumentsComplete
		)
		return True

	except AdhocZestEmiTransaction.DoesNotExist: return False