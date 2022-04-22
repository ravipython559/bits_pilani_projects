from adhoc.models import AdhocEzcredApplication
from bits_rest.bits_extra import student_id_generator
from django_mysql.locks import Lock
from bits_rest.bits_utils import get_admitted_program
from registrations.models import StudentCandidateApplication, CandidateSelection
from django.conf import settings


def get_ezcred_inprogress(email):
	try:
		ea = AdhocEzcredApplication.objects.exclude(status__in=['REJECTED','DISBURSAL_FAILED','FAILED',]).get(email=email)
	except AdhocEzcredApplication.DoesNotExist as e:
		ea = None

	return ea



def get_ezcred_declined(email):
	try:
		ea = AdhocEzcredApplication.objects.filter(status__in=['REJECTED','DISBURSAL_FAILED'], email=email)
	except AdhocEzcredApplication.DoesNotExist as e:
		ea = None

	return ea


def delete_initiated_application(email):
	AdhocEzcredApplication.objects.filter(
		status=AdhocEzcredApplication.INITIAL_STATUS, email=email
		).update(status=AdhocEzcredApplication.FAILED)

