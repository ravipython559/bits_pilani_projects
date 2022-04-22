from registrations.models import *
from django.db.models import *
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from application_specific.specific_user import *
from django.http import Http404

def sub_reviewer_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev =request.user.reviewer
			if rev.user_role == Reviewer.REVIEWER_CHOICES[4][0] :#sub-reviewer
				return view_func(request, *args, **kwargs)
		except Exception as e:
			raise Http404('sub reviewer {0}'.format(e))
	return _wrapped_view_func


def sub_reviewer_update_permission(view_func):
	def _wrapped_view_func(request, application_id=None, *args, **kwargs):
		status = [settings.APP_STATUS[0][0], 
			settings.APP_STATUS[2][0], 
			settings.APP_STATUS[1][0], 
			settings.APP_STATUS[17][0],]
		try:
			sca = StudentCandidateApplication.objects.get(pk = application_id)
			if sca.application_status in status :
				return view_func(request, application_id=application_id, *args, **kwargs)
			else:
				return redirect(reverse('sub_reviewer:sub-review-application-details-view',
                    kwargs={'application_id':application_id}))
		except StudentCandidateApplication.DoesNotExist as e:
			raise Http404('sub reviewer {0}'.format(e))
	return _wrapped_view_func