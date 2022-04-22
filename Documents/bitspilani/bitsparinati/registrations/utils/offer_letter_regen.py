from registrations.utils import offer_letter as ol
from registrations.models import *

def get_program_data(cs,prog):

	pld = ProgramLocationDetails.objects.get(
			program=prog,
			location=cs.application.current_location
		)
	pfa = PROGRAM_FEES_ADMISSION.objects.get(program=prog,
			fee_type='1',
			latest_fee_amount_flag=True
		)

	return pfa, pld 


def regen_offer(sca):
	cs = CandidateSelection.objects.get(application=sca)
	if cs.offer_letter:
		template_name = cs.application.program.offer_letter_template
		try:
			pfa,pld=get_program_data(cs,cs.application.program)
			ap_exp = ApplicantExceptions.objects.get(applicant_email=cs.application.login_email.email,
				program = cs.application.program)
			template_name = ap_exp.offer_letter or template_name

			if ap_exp.transfer_program:
				pfa,pld=get_program_data(cs,ap_exp.transfer_program)
				template_name = (
						ap_exp.offer_letter or 
						ap_exp.transfer_program.offer_letter_template or 
						cs.application.program.offer_letter_template
				)
									
		except (
				ApplicantExceptions.DoesNotExist,
				PROGRAM_FEES_ADMISSION.DoesNotExist,
				ProgramLocationDetails.DoesNotExist,
				) as e:
				pfa,pld=get_program_data(cs,cs.application.program)

		cs.fee_payment_deadline_dt = pld.fee_payment_deadline_date
		cs.orientation_dt = pld.orientation_date
		cs.lecture_start_dt = pld.lecture_start_date
		cs.orientation_venue = pld.orientation_venue
		cs.lecture_venue = pld.lecture_venue
		cs.admin_contact_person = pld.admin_contact_person
		cs.acad_contact_person = pld.acad_contact_person
		cs.admin_contact_phone = pld.admin_contact_phone
		cs.acad_contact_phone = pld.acad_contact_phone
		cs.adm_fees = pfa.fee_amount
		cs.offer_letter_generated_flag = True
		cs.offer_letter_regenerated_dt = timezone.now()
		cs.offer_letter_template = template_name
		cs.offer_letter = ol.render_offer_letter_content(cs)
		cs.save()