from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from registrations.models import *
from django.conf import settings

def is_certificate_redirect(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		pg_code =kwargs['pg_code']
		program = Program.objects.filter(program_code=pg_code, 
			program_type='certification')
		try:
			StudentCandidateApplication.objects.get(login_email=request.user)
		except StudentCandidateApplication.DoesNotExist:
			if program.exists(): return view_func(request, *args, **kwargs)
		return HttpResponseRedirect(reverse('registrationForm:applicantData'))
	return _wrapped_view_func

def is_certificate_redirect_to_edit(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			sca = StudentCandidateApplication.objects.get(
				login_email=request.user,
				application_status__in=[settings.APP_STATUS[16][0],
								settings.APP_STATUS[12][0],])
			if sca.program.program_type=='certification':
				return view_func(request, *args, **kwargs)
		except StudentCandidateApplication.DoesNotExist: pass	
		return HttpResponseRedirect(reverse('registrationForm:applicantData'))
	return _wrapped_view_func

def is_certificate_redirect_to_admin_rev_edit(view_func):
	def _wrapped_view_func(request ,pk, *args, **kwargs):
		sca = StudentCandidateApplication.objects.get(pk=pk)
		if sca.program.program_type=='certification':
			return view_func(request, *args, **kwargs)
		return HttpResponseRedirect(reverse('registrationForm:applicantData'))
	return _wrapped_view_func