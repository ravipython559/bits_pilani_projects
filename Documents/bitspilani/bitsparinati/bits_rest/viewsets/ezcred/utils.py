from bits_rest.models import EzcredApplication
from bits_rest.bits_extra import student_id_generator
from django_mysql.locks import Lock
from bits_rest.bits_utils import get_admitted_program
from registrations.models import StudentCandidateApplication, CandidateSelection
from django.conf import settings


def get_ezcred_inprogress(email):
	try:
		ea = EzcredApplication.objects.exclude(status__in=['REJECTED','DISBURSAL_FAILED','FAILED',]).get(
			application__login_email__email=email)
	except EzcredApplication.DoesNotExist as e:
		ea = None

	return ea



def get_ezcred_declined(email):
	try:
		ea = EzcredApplication.objects.filter(status__in=['REJECTED','DISBURSAL_FAILED'], application__login_email__email=email)
	except EzcredApplication.DoesNotExist as e:
		ea = None

	return ea


def delete_initiated_application(email):
	EzcredApplication.objects.filter(
		status=EzcredApplication.INITIAL_STATUS, application__login_email__email=email
		).update(status=EzcredApplication.FAILED)


def complete_admission_process(email):
	sca = StudentCandidateApplication.objects.get(login_email__email=email)
	cs = CandidateSelection.objects.get(application=sca)
	sca.application_status = settings.APP_STATUS[11][0]
	sca.save()
	with Lock('bits_student_id_lock'):
		cs.student_id = student_id_generator(login_email=email)
		cs.admitted_to_program = get_admitted_program(email)
		cs.save()
