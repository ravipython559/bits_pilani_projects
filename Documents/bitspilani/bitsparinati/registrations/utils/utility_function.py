from registrations.models import ApplicantExceptions

def transfer_program_check(sca):
	try:
		ae = ApplicantExceptions.objects.get(applicant_email = sca.login_email.email,
			program=sca.program,
			transfer_program__isnull=False)

		return not ae.transfer_program.active_for_applicaton_flag

	except ApplicantExceptions.DoesNotExist:
		return not sca.program.active_for_applicaton_flag

def is_transfer_program_admission_active_disable(sca):
	try:
		ae = ApplicantExceptions.objects.get(
			applicant_email=sca.login_email.email,
			program=sca.program,
			transfer_program__isnull=False
		)
		return not ae.transfer_program.active_for_admission_flag

	except ApplicantExceptions.DoesNotExist:
		return not sca.program.active_for_admission_flag


def check_inactive_program_flag(sca, active_field):
	try:
		ae = ApplicantExceptions.objects.get(applicant_email = sca.login_email.email,
			program=sca.program,
			transfer_program__isnull=False)

		return not  getattr(ae.transfer_program, active_field)

	except ApplicantExceptions.DoesNotExist:
		return not getattr(sca.program, active_field)