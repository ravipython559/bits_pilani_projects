from registrations.models import (ApplicantExceptions, 
	StudentCandidateApplication, CandidateSelection, Program)
from bits_rest.zest_api import ZestReport
from bits_rest.bits_extra import student_id_generator
from bits_rest import zest_statuses as ZS 
from bits import zest_settings as ZEST 
from django.conf import settings
from bits_rest.models import ZestEmiTransaction
from django.db import IntegrityError, transaction

def get_merchant_credentials(zest):
	credentials = {}
	if zest is not None:
		credentials.update(m_id=zest.client_id, m_sec=zest.client_secret)
	else:
		credentials.update(m_id=ZEST.ZEST_CLIENT_ID, m_sec=ZEST.ZEST_CLIENT_SECRET)

	return credentials

def get_admitted_program(sca):
		try:
			ae = ApplicantExceptions.objects.get(program=sca.program,
				applicant_email=sca.login_email.email,
			)
			ae = ae.transfer_program if ae.transfer_program else None
		except ApplicantExceptions.DoesNotExist:
			ae = None
		return ae

def update_approved_emi(email):
	sca = StudentCandidateApplication.objects.get(login_email__email=email)
	cs = CandidateSelection.objects.get(application=sca)
	zr = ZestReport(email)
	is_loan_activate = zr()
	return is_loan_activate

def login_approval_update(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email, 
			application_status=settings.APP_STATUS[9][0])
		emi_query = ZestEmiTransaction.objects.filter(
			application=sca).exclude(status__in=ZS.cancelled_status)
		if emi_query.exists():
			try:
				emi_query.get(status=ZS.Active, is_approved=True, 
					application__application_status=settings.APP_STATUS[11][0])
			except ZestEmiTransaction.DoesNotExist as e:
				update_approved_emi(sca.login_email.email)
	except StudentCandidateApplication.DoesNotExist as e: pass


def emi_in_progress(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email, 
				application_status=settings.APP_STATUS[9][0])
		
		emi = ZestEmiTransaction.objects.filter(application=sca, status__in=ZS.inprogress_status)
		return emi.exists()

	except Exception as e: return False

def emi_in_none(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email, 
				application_status=settings.APP_STATUS[9][0])
		
		emi = ZestEmiTransaction.objects.filter(application=sca, status__isnull=True)
		return emi.exists()

	except Exception as e: return False


def emi_in_decline(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email, 
				application_status=settings.APP_STATUS[9][0])
		emi = ZestEmiTransaction.objects.get(
				application=sca, status=ZS.Declined)
		return True

	except Exception as e: return False

def emi_in_cancellation(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email, 
				application_status=settings.APP_STATUS[9][0])
		emi = ZestEmiTransaction.objects.get(
				application=sca, status__in=ZS.incancelled_status)
		return True

	except Exception as e: return False

def emi_in_approved(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email, 
				application_status=settings.APP_STATUS[9][0])
		emi = ZestEmiTransaction.objects.get(
				application=sca, status=ZS.Approved)
		return True

	except Exception as e: return False

def emi_in_document_complete(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email, 
				application_status=settings.APP_STATUS[9][0])
		emi = ZestEmiTransaction.objects.get(
				application=sca, status=ZS.DocumentsComplete)
		return True

	except Exception as e: return False

def bulk_update_emi():
	#this is for temparory use this will be replaced once we write callback
	emails = ZestEmiTransaction.objects.filter(
		Q(status__in=ZS.inprogress_status)|
		Q(status__isnull=True)
		).values_list('application__login_email__email', flat=True).distinct()
	for email in emails:
		update_approved_emi(email)