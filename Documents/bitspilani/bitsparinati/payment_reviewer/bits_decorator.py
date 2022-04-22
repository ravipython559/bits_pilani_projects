from registrations.models import *
from .models import *
from django.db.models import Q
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import Http404

def reviewer_or_payment_reviewer_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev = request.user.reviewer
			is_payment_reviewer = rev.reviewer and rev.payment_reviewer
			is_payment_reviewer_role = rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[2][0]

			if is_payment_reviewer or is_payment_reviewer_role :
				return view_func(request, *args, **kwargs)
			else :
				raise Http404("No Permission")
		except :
			raise Http404("No Permission")
	return _wrapped_view_func

def only_payment_reviewer_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev = request.user.reviewer
			#is_payment_reviewer = rev.reviewer and rev.payment_reviewer
			is_payment_reviewer_role = rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[2][0]

			if is_payment_reviewer_role :
				return view_func(request, *args, **kwargs)
			else :
				raise Http404("No Permission")
		except :
			raise Http404("No Permission")
	return _wrapped_view_func


def add_and_view_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev = request.user.reviewer
			is_payment_reviewer = rev.reviewer and rev.payment_reviewer
			is_payment_reviewer_role = rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[2][0]
			is_admin = request.user.is_superuser

			if is_payment_reviewer or is_payment_reviewer_role or is_admin :
				return view_func(request, *args, **kwargs)
			else :
				raise Http404("No Permission")
		except :
			raise Http404("No Permission")
	return _wrapped_view_func

def reconsile_permission(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			rev = request.user.reviewer
			is_payment_reviewer = rev.payment_reviewer or rev.user_role == Reviewer.REVIEWER_CHOICES[2][0]

			if rev.reviewer and is_payment_reviewer:
				return view_func(request, *args, **kwargs)
			else :
				raise Http404("No Permission of payment reviewer")
		except :
			raise Http404("No Permission2 of reviewer")
	return _wrapped_view_func

