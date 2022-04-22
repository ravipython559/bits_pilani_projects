from adhoc.models import AdhocPropelldApplication
import hmac
import hashlib
from bits_rest.bits_extra import student_id_generator
from django_mysql.locks import Lock
from bits_rest.bits_utils import get_admitted_program
from registrations.models import StudentCandidateApplication, CandidateSelection
from django.conf import settings
import hmac
import hashlib

def get_propelld_inprogress(email):
	try:
		# ea = PropelldApplication.objects.exclude(status__in=['DROPPED','REJECTED',]).filter(
		# 	application__login_email__email=email).latest('created_on')

		ea = AdhocPropelldApplication.objects.filter(email=email).latest('created_on')
		if ea.status in ['DROPPED','REJECTED',]:
			ea = None

	except AdhocPropelldApplication.DoesNotExist as e:
		ea = None

	return ea

def get_propelld_innew(email):
	try:
		# ea = PropelldApplication.objects.exclude(status__in=['DROPPED','REJECTED',]).filter(
		# 	application__login_email__email=email).latest('created_on')

		ea = AdhocPropelldApplication.objects.filter(email=email).latest('created_on')
		if ea.status in ['New Loan Application',]:
			ea = None

	except AdhocPropelldApplication.DoesNotExist as e:
		ea = None

	return ea





# def get_PropelldApplication_declined(email):
# 	try:
# 		ea = AdhocPropelldApplication.objects.filter(status__in=['FAILED'], application__login_email__email=email)
# 	except PropelldApplication.DoesNotExist as e:
# 		ea = None

# 	return ea


# def delete_initiated_application(email):
# 	PropelldApplication.objects.filter(
# 		status=PropelldApplication.INITIAL_STATUS, application__login_email__email=email
# 		).update(status=PropelldApplication.FAILED)


def complete_admission_process(email):
	sca = StudentCandidateApplication.objects.get(login_email__email=email)
	cs = CandidateSelection.objects.get(application=sca)
	sca.application_status = settings.APP_STATUS[11][0]
	sca.save()
	with Lock('bits_student_id_lock'):
		cs.student_id = student_id_generator(login_email=email)
		cs.admitted_to_program = get_admitted_program(email)
		cs.save()

def create_sha256_signature(key, message):
	message = message.encode()
	return hmac.new(bytes(key), message, hashlib.sha256).hexdigest()
