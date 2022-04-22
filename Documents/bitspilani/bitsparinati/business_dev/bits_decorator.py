from registrations.models import *
from django.db.models import *
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from application_specific.specific_user import *
from django.http import Http404

def business_user_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev =request.user.reviewer
			if rev.user_role == Reviewer.REVIEWER_CHOICES[3][0] :#business-user
				return view_func(request, *args, **kwargs)
		except Exception as e:
			raise Http404('sub reviewer {0}'.format(e))
	return _wrapped_view_func