from registrations.models import *
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import Q

def is_waiver_program(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		pg_code =kwargs['pg_code']
		pg = Program.objects.filter(
			Q(
				show_on_page_flag = True,
				active_for_applicaton_flag = True,
				show_to_fee_wvr_appl_flag = True ,
                                program_type__in=['non-specific','cluster']
				)|
			Q(
				exceptionlistorgapplicants_requests_created_101__employee_email=request.user.email,
				exceptionlistorgapplicants_requests_created_101__exception_type__in = ['1','2'],
				show_on_page_flag = True,
				active_for_applicaton_flag = True,
                                program_type__in=['non-specific','cluster']
				)
			).distinct()
		if pg.filter(program_code=pg_code).exists():
			return view_func(request, *args, **kwargs)
		return HttpResponseRedirect(reverse('registrationForm:applicantData'))
	return _wrapped_view_func

def is_waiver(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		pg_code =kwargs['pg_code']
                eloa = ExceptionListOrgApplicants.objects.filter(
                	Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
					employee_email=request.user.email,
					program__program_code = pg_code,
					exception_type__in = ['1','2'] )
                if eloa.exists():
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
			exception_type__in = ['1','2'],
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
							application_status__in=[
							settings.APP_STATUS[12][0],
							settings.APP_STATUS[16][0]
							])
		except StudentCandidateApplication.DoesNotExist:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		else:
			return view_func(request, *args, **kwargs)

	return _wrapped_view_func_main