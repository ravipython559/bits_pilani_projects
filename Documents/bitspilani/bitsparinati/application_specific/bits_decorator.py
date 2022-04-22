from registrations.models import (StudentCandidateApplication,
	ExceptionListOrgApplicants,Program,
	ProgramDomainMapping as PDM)
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import Q


def is_specific_user(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		s_e = PDM.objects.filter(email = request.user.email).exists()
		s_d = PDM.objects.filter(email_domain__iexact = request.user.email.split('@')[1]).exists()
		#changes said by shantanu for specific program check on 20th Feb 2019 in specific_type
		specific_type=StudentCandidateApplication.objects.filter(login_email=request.user,program__program_type='specific').exists()
		pg_code = kwargs.get('pg_code',None)
		if pg_code:
			specific_type = Program.objects.filter(program_code = pg_code,
							program_type = 'specific').exists()
		if s_e or s_d or specific_type:
			return view_func(request, *args, **kwargs)
		else:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
	return _wrapped_view_func


def is_specific_program(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		pg_code = kwargs.get('pg_code',None)
		try:
			Program.objects.get(program_code=pg_code,
				active_for_applicaton_flag = True,
				show_on_page_flag = True,
                                program_type='specific')
		except Program.DoesNotExist:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))

		s_e = PDM.objects.filter(email = request.user.email)
		s_d = PDM.objects.filter(email_domain__iexact = request.user.email.split('@')[1])
		#changes said by shantanu for specific program check on 20th Feb 2019 in specific_type
		specific_type = StudentCandidateApplication.objects.filter(login_email=request.user,program__program_type='specific').exists()
		pg_code = kwargs.get('pg_code',None)
		if pg_code:
			specific_type = Program.objects.filter(program_code = kwargs.get('pg_code',None),
							program_type = 'specific').exists()
		if s_e.exists() and s_e.filter(program__program_code=pg_code).exists():
			return view_func(request, *args, **kwargs)
		elif s_d.exists() and s_d.filter(program__program_code=pg_code).exists():
			return view_func(request, *args, **kwargs)
		elif specific_type:
			return view_func(request, *args, **kwargs)	
		else:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
	return _wrapped_view_func


def application_edit_permission(view_func):
	def _wrapped_view_func_main(request, *args, **kwargs):
		query = StudentCandidateApplication.objects.get(login_email=request.user)
		eloa = ExceptionListOrgApplicants.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=request.user.email,
			exception_type__in=['1','2'],
			program = query.program,
			)
		if query.program.program_type=='certification':
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		if eloa.exists():
			try:
				StudentCandidateApplication.objects.get(login_email=request.user,
					application_status__in =[
					settings.APP_STATUS[0][0],
					settings.APP_STATUS[1][0],
					settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0],
					settings.APP_STATUS[4][0],
					settings.APP_STATUS[5][0],
					settings.APP_STATUS[6][0],
					settings.APP_STATUS[7][0],
					settings.APP_STATUS[8][0],
					settings.APP_STATUS[9][0],
					settings.APP_STATUS[10][0],
					settings.APP_STATUS[11][0],
					settings.APP_STATUS[15][0],

					])
			except StudentCandidateApplication.DoesNotExist:
				return view_func(request, *args, **kwargs)

		try:
			StudentCandidateApplication.objects.get(login_email=request.user,
							application_status__in=[settings.APP_STATUS[12][0],
							settings.APP_STATUS[16][0]
							])
		except StudentCandidateApplication.DoesNotExist:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		else:
			return view_func(request, *args, **kwargs)

	return _wrapped_view_func_main
