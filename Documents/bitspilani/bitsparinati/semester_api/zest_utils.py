from bits_rest import zest_statuses as ZS 
from semester_api import zest_settings as ZEST
from django.conf import settings
from semester_api.models import SemZestEmiTransaction
from django.db import IntegrityError, transaction
from semester_api.zest_api import *

def emi_in_progress(student_id):
	emi = SemZestEmiTransaction.objects.filter(student_id=student_id, status__in=ZS.inprogress_status)
	return emi.exists()

def emi_in_none(student_id):
	emi = SemZestEmiTransaction.objects.filter(student_id=student_id, status__isnull=True)
	return emi.exists()


def update_approved_emi(student_id):
	zr = ZestReport(student_id)
	is_loan_activate = zr()
	return is_loan_activate

def login_approval_update(student_id):
	emi_query = SemZestEmiTransaction.objects.filter(student_id=student_id).exclude(status__in=ZS.cancelled_status)
	if emi_query.exists():
		try:
			emi_query.get(status=ZS.Active, is_approved=True,)
		except SemZestEmiTransaction.DoesNotExist as e:
			update_approved_emi(student_id)

def emi_in_decline(student_id):
	try:
		emi = SemZestEmiTransaction.objects.get(student_id=student_id, status=ZS.Declined)
		return True
	except SemZestEmiTransaction.DoesNotExist: return False

def emi_in_approved(student_id):
	try:
		emi = SemZestEmiTransaction.objects.get(student_id=student_id, status=ZS.Approved)
		return True

	except SemZestEmiTransaction.DoesNotExist: return False

def emi_in_document_complete(student_id):
	try:
		emi = SemZestEmiTransaction.objects.get(student_id=student_id, status=ZS.DocumentsComplete)
		return True

	except SemZestEmiTransaction.DoesNotExist: return False

def emi_in_cancellation(student_id):
	try:
		emi = SemZestEmiTransaction.objects.get(
			student_id=student_id, 
			status__in=ZS.incancelled_status
		)
		return True

	except Exception as e: return False

# def bulk_update_emi():
# 	#this is for temparory use this will be replaced once we write callback
# 	emails = SemZestEmiTransaction.objects.filter(
# 		Q(status__in=ZS.inprogress_status)|
# 		Q(status__isnull=True)
# 		).values_list('application__login_email__email', flat=True).distinct()
# 	for email in emails:
# 		update_approved_emi(email)