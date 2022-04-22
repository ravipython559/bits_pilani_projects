from bits_rest.models import EduvanzApplication
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, HttpResponseRedirect
from .utils import get_eduvanz_inprogress, get_eduvanz_declined, get_eduvanz_approved

def check_eduvanz_status(view_func):
	def _wrapped_view_func(request, *args, **kwargs): 
		if get_eduvanz_inprogress(request.user.email) or get_eduvanz_approved(request.user.email) or get_eduvanz_declined(request.user.email):
			return HttpResponseRedirect(reverse('registrationForm:applicantData'))
		return view_func(request, *args, **kwargs)
	return _wrapped_view_func