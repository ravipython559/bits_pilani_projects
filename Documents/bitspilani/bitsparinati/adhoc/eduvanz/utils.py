from adhoc.models import AdhocEduvanzApplication
from bits_rest.bits_utils import get_admitted_program
from registrations.models import OtherFeePayment
from django.conf import settings

def get_eduvanz_inprogress(ofp):
	try:
		ea = AdhocEduvanzApplication.objects.exclude(
			status_code__in=['ELS401', 'ELS402', 'ELS301', 'FAILED']
		).get(email=ofp.email, program=ofp.program, fee_type=ofp.fee_type)
	except AdhocEduvanzApplication.DoesNotExist as e:
		ea = None

	return ea

def get_eduvanz_declined(ofp):
	try:
		ea = AdhocEduvanzApplication.objects.get(status_code='ELS402', 
			email=ofp.email, program=ofp.program, fee_type=ofp.fee_type
		)
	except AdhocEduvanzApplication.DoesNotExist as e:
		ea = None

	return ea

def get_eduvanz_approved(ofp):
	try:
		ea = AdhocEduvanzApplication.objects.get(status_code='ELS301', 
			email=ofp.email, program=ofp.program, fee_type=ofp.fee_type
		)
	except AdhocEduvanzApplication.DoesNotExist as e:
		ea = None

	return ea

def delete_initiated_application(ofp):
	AdhocEduvanzApplication.objects.filter(
		status_code=AdhocEduvanzApplication.INITIAL_STATUS, 
		email=ofp.email, program=ofp.program, fee_type=ofp.fee_type
	).update(status_code=AdhocEduvanzApplication.FAILED)


