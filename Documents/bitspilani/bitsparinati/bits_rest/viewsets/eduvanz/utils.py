from bits_rest.models import EduvanzApplication
from bits_rest.bits_extra import student_id_generator
from django_mysql.locks import Lock
from bits_rest.bits_utils import get_admitted_program
from registrations.models import StudentCandidateApplication, CandidateSelection
from django.conf import settings

def get_eduvanz_inprogress(email):
	try:
		ea = EduvanzApplication.objects.exclude(status_code__in=['ELS401', 'ELS402', 'FAILED', 'ELS100']).get(
			application__login_email__email=email)
	except EduvanzApplication.DoesNotExist as e:
		ea = None

	return ea

def get_eduvanz_declined(email):
	try:
		# ea = EduvanzApplication.objects.get(status_code='ELS402', application__login_email__email=email)
		ea = EduvanzApplication.objects.filter(status_code='ELS402', application__login_email__email=email).first()
	except EduvanzApplication.DoesNotExist as e:
		ea = None

	return ea

def get_eduvanz_approved(email):
	try:
		ea = EduvanzApplication.objects.get(status_code='ELS301', application__login_email__email=email)
	except EduvanzApplication.DoesNotExist as e:
		ea = None

	return ea

def delete_initiated_application(email):
	EduvanzApplication.objects.filter(
		status_code=EduvanzApplication.INITIAL_STATUS, application__login_email__email=email
		).update(status_code=EduvanzApplication.FAILED)

def complete_admission_process(email):
	sca = StudentCandidateApplication.objects.get(login_email__email=email)
	cs = CandidateSelection.objects.get(application=sca)
	sca.application_status = settings.APP_STATUS[11][0]
	sca.save()
	with Lock('bits_student_id_lock'):
		cs.student_id = student_id_generator(login_email=email)
		cs.admitted_to_program = get_admitted_program(email)
		cs.save()
