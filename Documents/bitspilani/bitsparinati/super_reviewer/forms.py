from django import forms

from functools import partial
from django.contrib.auth.models import User
from .models import *
from django.conf import settings
from django.utils.safestring import mark_safe

class SuperofferForm(forms.Form):
	full_name = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	application_student_id = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	program_applied_for = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	created_on_datetime = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	es_com = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	su_rev_app = forms.BooleanField(required=False)
	app_id = forms.IntegerField(widget=forms.HiddenInput(),required=False)

class SuperprogramForm(forms.Form):
	full_name = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	application_student_id = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	new_application_id = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	prior_status = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	new_sel_prog = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	created_on_datetime = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	es_com = forms.CharField(max_length=254, required=False,
                               widget=forms.HiddenInput())
	su_rev_app = forms.BooleanField(required=False)
	app_id = forms.IntegerField(widget=forms.HiddenInput(),required=False)
	
class SuperEscCommentForm(forms.Form):
    super_comment = forms.CharField(label='Super Reviewer Comments', 
    	widget=forms.Textarea(attrs={'cols': 70, 'rows': 2,}))