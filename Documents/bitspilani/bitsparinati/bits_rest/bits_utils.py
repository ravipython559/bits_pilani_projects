from registrations.models import (ApplicantExceptions, 
	StudentCandidateApplication, CandidateSelection, ApplicationPayment, PROGRAM_FEES_ADMISSION)
from bits_rest.models import ZestEmiTransaction
from bits_rest.bits_extra import student_id_generator
from django.conf import settings
from bits_rest import zest_statuses as ZS
from django.utils import timezone
from django_mysql.locks import Lock

def get_admitted_program(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email)
		ae = ApplicantExceptions.objects.get(program=sca.program,
			applicant_email=sca.login_email.email,
		)
		ae = ae.transfer_program if ae.transfer_program else None
	except (ApplicantExceptions.DoesNotExist, StudentCandidateApplication.DoesNotExist) as e:
		ae = None
	return ae


def complete_admission_process(email):
	sca = StudentCandidateApplication.objects.get(login_email__email=email)
	cs = CandidateSelection.objects.get(application=sca)
	sca.application_status = settings.APP_STATUS[11][0]
	sca.save()
	with Lock('bits_student_id_lock'):
		cs.student_id = student_id_generator(login_email=email)
		cs.admitted_to_program = get_admitted_program(email)
		cs.save()
	insert_application_payment(sca)
	return True

def insert_application_payment(sca):
	zest = ZestEmiTransaction.objects.get(application=sca, status=ZS.Active)
	ApplicationPayment.objects.create(
		payment_id=zest.order_id,
		payment_amount=zest.req_json_data['BasketAmount'],
		payment_date=timezone.localtime(timezone.now()),
		payment_bank='Zest',
		transaction_id=zest.order_id,
		application=sca,
		fee_type='1',
		insertion_datetime=timezone.localtime(timezone.now())
	)