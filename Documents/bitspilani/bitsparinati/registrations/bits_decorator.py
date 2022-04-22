from .models import (StudentCandidateApplication,
	ExceptionListOrgApplicants,ProgramDomainMapping,
	ProgramDomainMapping as PDM,Reviewer,CandidateSelection)
from django.db.models import Q
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from application_specific.specific_user import *
from django.http import Http404

def applicant_status_permission(status=None):
	def decorator(view_func):
		def _wrapped_view_func(request, *args, **kwargs):
			if status:
				get_params = {'login_email':request.user}
				if isinstance(status, list) or isinstance(status, tuple):
					get_params['application_status__in'] = status
				else:
					get_params['application_status'] = status
				try:
					query = StudentCandidateApplication.objects.get(**get_params)
				except StudentCandidateApplication.DoesNotExist:
					return HttpResponseRedirect(reverse('registrationForm:applicantData'))
				else:
					return view_func(request, *args, **kwargs)
			else:
				try:
					query = StudentCandidateApplication.objects.get(login_email=request.user)
				except StudentCandidateApplication.DoesNotExist:
					return view_func(request, *args, **kwargs)
				else:
					return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		return _wrapped_view_func
	return decorator

def applicant_status_edit_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			query = StudentCandidateApplication.objects.get(login_email=request.user,
							application_status__in=[settings.APP_STATUS[16][0],
							settings.APP_STATUS[12][0],
							])
		except StudentCandidateApplication.DoesNotExist:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		else:
			return view_func(request, *args, **kwargs)

	return _wrapped_view_func

def payment_exception_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		query = StudentCandidateApplication.objects.get(login_email=request.user,)
		try:
			eloa = ExceptionListOrgApplicants.objects.get(
				Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
				employee_email=request.user.email,
				exception_type='1',
				program=query.program,
				) 
			query.application_status = settings.APP_STATUS[13][0]
			query.save()
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))

		except ExceptionListOrgApplicants.DoesNotExist:
			pass
			
		return view_func(request, *args, **kwargs)
	return _wrapped_view_func

def payment_exception_permission_upload(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		query = StudentCandidateApplication.objects.get(login_email=request.user,)
		try:
			eloa = ExceptionListOrgApplicants.objects.get(
				Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
				employee_email=request.user.email,
				exception_type='1',program=query.program)
			if query.application_status in [settings.APP_STATUS[12][0],settings.APP_STATUS[18][0]]:
				query.application_status = settings.APP_STATUS[13][0]
				query.save()

		except ExceptionListOrgApplicants.DoesNotExist: pass 
		return view_func(request, *args, **kwargs)
	return _wrapped_view_func

def reviewer_login_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev = request.user.reviewer
			if rev.reviewer :
				return HttpResponseRedirect(reverse('registrationForm:review-applicant-data'))
		except :
			return view_func(request, *args, **kwargs)

	return _wrapped_view_func

def reviewer_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev =request.user.reviewer
			#is_payment_reviewer = rev.reviewer and rev.payment_reviewer
			is_payment_reviewer_role = rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[2][0]

			if rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[1][0]:
				return HttpResponseRedirect(reverse('super_reviewer:sr-home'))

			elif is_payment_reviewer_role :
				return HttpResponseRedirect(reverse('payment_reviewer:payments-reviewer'))

			elif rev.user_role == Reviewer.REVIEWER_CHOICES[3][0] :#business-developer
				return HttpResponseRedirect(reverse('business_user:applicantData'))

			elif rev.user_role == Reviewer.REVIEWER_CHOICES[4][0] :#sub-reviewer
				return HttpResponseRedirect(reverse('sub_reviewer:review_applicant_data'))

			if rev.reviewer :
				return view_func(request, *args, **kwargs)
		except Exception as e:
			raise Http404(str(e))
	return _wrapped_view_func

def admission_payment_exception_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:

			query = StudentCandidateApplication.objects.get(login_email=request.user, 
				application_status= settings.APP_STATUS[9][0])

			ExceptionListOrgApplicants.objects.get(
				Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
				employee_email=request.user.email, 
				exception_type='2', 
				program = query.program)

		except StudentCandidateApplication.DoesNotExist:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))

		except ExceptionListOrgApplicants.DoesNotExist:
			return view_func(request, *args, **kwargs)

		return HttpResponseRedirect(reverse('registrationForm:pdf-offer-letter-redirect-direct-upload1'))

	return _wrapped_view_func



def redirect_specific_user_application_form(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		pg_code = kwargs.get('pg_code',None)
		s_e = PDM.objects.filter(email = request.user.email).exists()
		s_d = PDM.objects.filter(email_domain__iexact = request.user.email.split('@')[1]).exists()
		#changes said by shantanu for specific program check on 20th Feb 2019 in specific_type
		specific_type = StudentCandidateApplication.objects.filter(login_email=request.user,program__program_type='specific').exists()
		if pg_code:
			specific_type = Program.objects.filter(program_code = pg_code,
							program_type = 'specific').exists()
		if s_e or s_d or specific_type:
			return HttpResponseRedirect(reverse('application_specific:specific_form_add'))
		else:
			return view_func(request, *args, **kwargs)
	return _wrapped_view_func

def redirect_specific_user_edit_application_form(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		pg_code = kwargs.get('pg_code',None)
		s_e = PDM.objects.filter(email = request.user.email).exists()
		s_d = PDM.objects.filter(email_domain__iexact = request.user.email.split('@')[1]).exists()
		#changes said by shantanu for specific program check on 20th Feb 2019 in specific_type
		specific_type = StudentCandidateApplication.objects.filter(login_email=request.user,program__program_type='specific').exists()
		if pg_code:
			specific_type = Program.objects.filter(program_code = pg_code,
							program_type = 'specific').exists()
		if s_e or s_d or specific_type:
			return HttpResponseRedirect(reverse('application_specific:specific_edit_form_add'))
		else:
			return view_func(request, *args, **kwargs)
	return _wrapped_view_func

def specif_viewer_redirect_to(redirect=None):
	def decorator(view_func):
		def _wrapped_view_func(request, *args, **kwargs):
			pg_code = kwargs.get('pg_code',None)
			s_e_d = ProgramDomainMapping.objects.filter(Q(email = request.user.email)|
				Q(email_domain__iexact = request.user.email.split('@')[1])).exists()
			#changes said by shantanu for specific program check on 20th Feb 2019 in specific_type
			specific_type = StudentCandidateApplication.objects.filter(login_email=request.user,program__program_type='specific').exists()
			if pg_code:
				specific_type = Program.objects.filter(program_code = pg_code,
							program_type = 'specific').exists()
			if s_e_d or specific_type:
				return HttpResponseRedirect(reverse(redirect,
					kwargs={'pg_code':pg_code} if pg_code else {}))
			else:
				return view_func(request, *args, **kwargs)
		return _wrapped_view_func
	return decorator

def certification_view_redirect(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		sca = StudentCandidateApplication.objects.get(login_email=request.user)

		if sca.program.program_type == 'certification':
			return HttpResponseRedirect(
					reverse('certificate:student-application-view')
					)
		return view_func(request, *args, **kwargs)	
	return _wrapped_view_func

def pdf_certificate_user(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		sca = StudentCandidateApplication.objects.get(login_email=request.user)

		if sca.program.program_type == 'certification':
			return HttpResponseRedirect(
					reverse('registrationForm:applicantData')
					)
		return view_func(request, *args, **kwargs)	
	return _wrapped_view_func

def if_certificate_redirect(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		pg_code =kwargs['pg_code']
		program = Program.objects.filter(program_code=pg_code, 
			program_type='certification')

		if program.exists():
			return HttpResponseRedirect(reverse('certificate:student-application',
			 kwargs={'pg_code':pg_code}))
		return view_func(request, *args, **kwargs)	
	return _wrapped_view_func

def if_waiver_redirect(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		pg_code =kwargs['pg_code']

		eloa = ExceptionListOrgApplicants.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=request.user.email,
			exception_type__in = ['1','2'],
			program__program_code = pg_code)
		if eloa.exists():
			return HttpResponseRedirect(reverse('application_waiver:waiver_form_add',
			 kwargs={'pg_code':pg_code}))
		return view_func(request, *args, **kwargs)	
	return _wrapped_view_func



def if_certificate_redirect_to_edit(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		query = StudentCandidateApplication.objects.get(login_email=request.user)

		if query.program.program_type == 'certification':
			return HttpResponseRedirect(
				reverse('certificate:student-application-edit',))
		return view_func(request, *args, **kwargs)
	return _wrapped_view_func

def if_waiver_redirect_to_edit(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		query = StudentCandidateApplication.objects.get(login_email=request.user)
		eloa = ExceptionListOrgApplicants.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=request.user.email,
			exception_type__in = ['1', '2'],
			program = query.program)

		if eloa.exists():
			return HttpResponseRedirect(reverse('application_waiver:waiver_form_edit',))
				
		return view_func(request, *args, **kwargs)
	return _wrapped_view_func

def program_cookie(view_func):
	def _wrapped_view_func(request, *args, **kwargs):

		if {'program_code','source_site'}.issubset(request.COOKIES):
			response = HttpResponseRedirect(
				reverse('registrationForm:student-application-pg-source-site',
					kwargs={
						'pg_code':request.COOKIES['program_code'],
						'source_site':request.COOKIES['source_site']
						})
				)
			try:
				SOURCE_SITE = dict(BitsUser.SOURCE_SITE_CHOICES)[request.COOKIES['program_code'].strip()]
				bu = BitsUser.objects.get(user=request.user)
				pg = Program.objects.get(
					program_code=request.COOKIES['program_code'].strip()
					)
				bu.source_program = pg 
				bu.source_site = request.COOKIES['source_site'].strip()
				bu.save()
			except (BitsUser.DoesNotExist, Program.DoesNotExist) as e:
				pass
			except Exception as e:
				pass
			response.delete_cookie('program_code')
			response.delete_cookie('source_site')
			return response

		elif 'program_code' in request.COOKIES:

			specific_type = Program.objects.filter(program_code =request.COOKIES['program_code'],
						program_type = 'specific').exists()

			if specific_type:
				response = HttpResponseRedirect(
				reverse('application_specific:specific_form_add',
					kwargs={
							'pg_code':request.COOKIES['program_code'],
						})
				)

			else:
				response = HttpResponseRedirect(
					reverse('registrationForm:student-application',
						kwargs={
								'pg_code':request.COOKIES['program_code'],
							})
					)

			response.delete_cookie('program_code')
			return response

		elif 'is_adhoc_user' in request.COOKIES:
			response = HttpResponseRedirect(reverse('adhoc:registered-home'))
			response.delete_cookie('is_adhoc_user')
			return response

		return view_func(request, *args, **kwargs)
	return _wrapped_view_func

def media_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		
		if not kwargs['path'].split('/')[0] =='documents':
			return view_func(request, *args, **kwargs)
		
		try:
			rev = request.user.reviewer
			if rev.reviewer :
				return view_func(request, *args, **kwargs)
			else:
				raise Http404("No Permission")
		except:
			if  request.user.is_staff:
				return view_func(request, *args, **kwargs)
			else:
				ap = ApplicationDocument.objects.filter(application__login_email=request.user)
				for x in ap:
					if x.file.path == kwargs['document_root'] + kwargs['path']:
						return view_func(request, *args, **kwargs)
				else :
					raise Http404("No Permission")


	return _wrapped_view_func

def hr_men_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			cs = CandidateSelection.objects.get(
				application__login_email = request.user,
				application__application_status__in = [
				settings.APP_STATUS[11][0],
				settings.APP_STATUS[9][0],
				],)
			if not cs.application.program.hr_cont_req and \
				cs.application.program.mentor_id_req:
				return HttpResponseRedirect(
					reverse('registrationForm:applicantData')
					)
		except ExceptionListOrgApplicants.DoesNotExist:
			return HttpResponseRedirect(
				reverse('registrationForm:applicantData')
				)
		else:
			if not cs.m_email or not cs.hr_cont_email:
				return view_func(request, *args, **kwargs)
			else:
				return HttpResponseRedirect(
					reverse('registrationForm:applicantData')
					)

	return _wrapped_view_func

def man_id_wav_chk(view_func):
	def _wrapped_view_func(request, app_id,*args, **kwargs):
		query = StudentCandidateApplication.objects.get(id=int(app_id))
		if not query.application_status==settings.APP_STATUS[11][0] :

			try:
				ExceptionListOrgApplicants.objects.get(
					Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
					employee_email=query.login_email.email,
					exception_type='2',)

			except ExceptionListOrgApplicants.DoesNotExist:
				return redirect(reverse('registrationForm:review_application_details',
                    kwargs={'application_id':app_id}))

		return view_func(request, app_id,*args, **kwargs)

	return _wrapped_view_func

def reviewer_or_payment_reviewer_permission_report(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev =request.user.reviewer
			
			if rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[1][0]:
				raise Http404("Novvvv Permission")

			if rev.reviewer or rev.user_role == Reviewer.REVIEWER_CHOICES[2][0] :
				return view_func(request, *args, **kwargs)
			else :
				raise Http404("No dfdfdfPermission")
		except :
			raise Http404("No bbbbPermission")
	return _wrapped_view_func

def if_deffer_redirect(view_func):
	def _wrapped_view_func(request, application_id, alert_status=None, *args, **kwargs):
		query = StudentCandidateApplication.objects.get(id=int(application_id))
		application_statuses = [settings.APP_STATUS[6][0], 
			settings.APP_STATUS[9][0], settings.APP_STATUS[11][0]
			]
		is_defered_exist = ApplicationDocument.objects.filter(
			Q(accepted_verified_by_bits_flag=False)|Q(rejected_by_bits_flag=True),
			application=query,
			program_document_map__deffered_submission_flag=True,
			application__application_status__in=application_statuses).exists()
		if is_defered_exist:
			if alert_status:
				return redirect(reverse('reviewer:deferred_application_details_alert',
                    kwargs={'application_id':application_id,'alert_status':alert_status}))
			return redirect(reverse('reviewer:deferred_application_details',
                    kwargs={'application_id':application_id}))


		return view_func(request, application_id, alert_status, *args, **kwargs)

	return _wrapped_view_func