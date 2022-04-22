from registrations.models import OtherFeePayment, CandidateSelection
from django.db.models import Q
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from application_specific.specific_user import *
from django.http import Http404, HttpResponseBadRequest
from bits_rest.models import ZestEmiTransaction
from bits_rest.zest_utils import emi_in_approved, emi_in_progress, emi_in_none
from bits_rest.viewsets.eduvanz.utils import get_eduvanz_inprogress, get_eduvanz_declined, get_eduvanz_approved
from bits_rest import zest_statuses as ZS 

def is_adhoc_payment(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		try:
			otf = OtherFeePayment.objects.get(email=request.user.email,)
			if otf.transaction_id:
				return render(request, 'bits_rest/adhoc_bad_request.html', {'otf':otf},)
		except OtherFeePayment.DoesNotExist:
			return render(request, 'bits_rest/no_adhoc_payment.html',)
		try:
			return view_func(request, *args, **kwargs)
		except Exception as e:
			return render(request, 'bits_rest/500.html', {
				'payment_error':"""
				{0} (This error occurs mostly due to interruption in payment process)
				""".format(str(e))},) 
	return _wrapped_view_func


def check_emi_status(view_func):
	def _wrapped_view_func(request, *args, **kwargs): 
		sca = StudentCandidateApplication.objects.get(login_email=request.user)
		if emi_in_approved(request.user.email) or get_eduvanz_approved(request.user.email) or sca.application_status==settings.APP_STATUS[11][0]:
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		return view_func(request, *args, **kwargs)
	return _wrapped_view_func


def check_cross_payment(view_func):
	def _wrapped_view_func(request, *args, **kwargs):
		if emi_in_progress(request.user.email) or emi_in_none(request.user.email) or get_eduvanz_inprogress(request.user.email):
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		return view_func(request, *args, **kwargs)
	return _wrapped_view_func