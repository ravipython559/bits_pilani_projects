from registrations.models import (StudentCandidateApplication,
	ExceptionListOrgApplicants,Program,Reviewer,
	ProgramDomainMapping as PDM)
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings


def is_super_reviewer(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev =request.user.reviewer
			if rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[1][0]:
				return view_func(request, *args, **kwargs)
			else:
				return HttpResponseRedirect(reverse('auth_logout'))
		except :
			return HttpResponseRedirect(reverse('auth_logout'))

	return _wrapped_view_func