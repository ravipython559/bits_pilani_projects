from django.shortcuts import render, redirect
from registrations.models import *
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import Http404
from django.db.models import Q

def adm_man_id_wav_chk(view_func):
	def _wrapped_view_func(request, app_id, *args, **kwargs):
		query = StudentCandidateApplication.objects.get(id=int(app_id))
		if query.application_status==settings.APP_STATUS[11][0]:
			return view_func(request, app_id,*args, **kwargs)
		try:
			eloa = ExceptionListOrgApplicants.objects.get(
				Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
				employee_email=query.login_email.email,
				program=query.program,
				exception_type='2')
			return view_func(request, app_id,*args, **kwargs)
		except ExceptionListOrgApplicants.DoesNotExist: pass
		
		return redirect(reverse('bits_admin:applicantData'))

	return _wrapped_view_func

def rev_and_pay_rev_permission(view_func):
	def _wrapped_view_func(request, id, *args, **kwargs):
		if request.user.is_superuser:
			kwargs.update(id=id)
			return view_func(request,*args, **kwargs)
		try:
			rev = request.user.reviewer
			is_payment_reviewer = rev.reviewer and rev.payment_reviewer
			is_payment_reviewer_role = rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[2][0]
			is_business_role = rev.user_role == Reviewer.REVIEWER_CHOICES[3][0]
			

			if is_payment_reviewer:
				return redirect(reverse('registrationForm:review_application_details',kwargs={'application_id':id}))
			elif is_payment_reviewer_role or request.user.is_superuser:
				kwargs.update(id=id)
				return view_func(request,*args, **kwargs)
			elif is_business_role:
				return redirect(reverse('business_user:business_application_details',kwargs={'application_id':id}))
			elif rev.reviewer:
				return redirect(reverse('registrationForm:review_application_details',kwargs={'application_id':id}))

			else :
				raise Http404("No admin Permission")
		except Exception as e:
			raise Http404(str(e))
	return _wrapped_view_func


def archive_view_permission(view_func):
	def _wrapped_view_func(request, pk, run_id, *args, **kwargs):

		if request.user.is_superuser:
			kwargs.update(pk=pk,run_id=run_id)
			return view_func(request, *args, **kwargs)
		try:
			rev = request.user.reviewer
			is_business_role = rev.user_role == Reviewer.REVIEWER_CHOICES[3][0]

			if is_business_role:
				return redirect(reverse('business_user:admin-application-archive-views',kwargs={'pk':pk, 'run_id':run_id,}))
			elif rev.user_role == None:
				return redirect(reverse('reviewer:admin-application-archive-views',kwargs={'pk':pk, 'run_id':run_id,}))
			else :
				raise Http404("No admin Permission")
		except Exception as e:
			raise Http404(str(e))
	return _wrapped_view_func