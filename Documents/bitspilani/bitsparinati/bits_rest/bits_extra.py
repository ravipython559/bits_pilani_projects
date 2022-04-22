from registrations.models import *
from django.db.models import *

def student_id_generator(login_email=None):
	app = StudentCandidateApplication.objects.get(login_email__email=login_email)
	selected_program = app.program
	is_transfer_program = False

	try:
		ae = ApplicantExceptions.objects.get(applicant_email = app.login_email.email,
			program = app.program )
		ae = ae.transfer_program if ae.transfer_program else None
		selected_program = ae if ae else selected_program
		is_transfer_program = True if ae else False

	except ApplicantExceptions.DoesNotExist:
		ae = None

	pfa = PROGRAM_FEES_ADMISSION.objects.get(
		program= selected_program,
		fee_type = '1',
		latest_fee_amount_flag = True,
		#admit_year = app.admit_year #not yet decided to keep or not
	)

	cs = CandidateSelection.objects.get(application = app,)

	max_id = CandidateSelection.objects.filter(
		Q(student_id__contains = app.admit_year) & 
		Q(student_id__contains=pfa.program.program_code),
		# Q(application__program = selected_program) |
		# Q(admitted_to_program = selected_program),
		).exclude(student_id__isnull =True).aggregate(Max('student_id'))

	pg_code = pfa.program.program_code
	student_max_id = int(max_id['student_id__max'][-3:]) if max_id['student_id__max'] else 0
	student_max_id = pfa.stud_id_gen_st_num if pfa.stud_id_gen_st_num > student_max_id else student_max_id
	if student_max_id >= 999 :
		for x in filter(lambda x: x != '', pfa.program.alternative_program_code.split(',')) :
			max_id = CandidateSelection.objects.filter(
				Q(student_id__contains = app.admit_year) & Q(student_id__contains = x),
				).exclude(student_id__isnull =True).aggregate(Max('student_id'))

			student_max_id = int(max_id['student_id__max'][-3:]) if max_id['student_id__max'] else 0
			if student_max_id < 999 :
				pg_code = x
				break
		else:student_id = None

	if student_max_id < 999:
		student_id = '{0}{1}{2:03d}'.format(app.admit_year,pg_code,student_max_id + 1)
	if is_transfer_program:
		cs.admitted_to_program = ae
	# cs.old_student_id = cs.student_id
	cs.save()
	if student_id:
		try:
			std_id1= CandidateSelection.objects.get(student_id=student_id)
			if std_id1:
				max_id = CandidateSelection.objects.filter(
					Q(student_id__contains = app.admit_year) & 
					Q(student_id__contains=pfa.program.program_code),
					# Q(application__program = selected_program) |
					# Q(admitted_to_program = selected_program),
					).exclude(student_id__isnull =True).aggregate(Max('student_id'))
				pg_code = pfa.program.program_code
				student_max_id = int(max_id['student_id__max'][-3:]) if max_id['student_id__max'] else 0
				student_max_id = pfa.stud_id_gen_st_num if pfa.stud_id_gen_st_num > student_max_id else student_max_id
				if student_max_id >= 999 :
					for x in filter(lambda x: x != '', pfa.program.alternative_program_code.split(',')) :
						max_id = CandidateSelection.objects.filter(
							Q(student_id__contains = app.admit_year) & Q(student_id__contains = x),
							).exclude(student_id__isnull =True).aggregate(Max('student_id'))

						student_max_id = int(max_id['student_id__max'][-3:]) if max_id['student_id__max'] else 0
						if student_max_id < 999 :
							pg_code = x
							break
					else:student_id = None

				if student_max_id < 999:
					student_id = '{0}{1}{2:03d}'.format(app.admit_year,pg_code,student_max_id + 1)
		except:
			'''no changes required'''
			pass 

	return student_id