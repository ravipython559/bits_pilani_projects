"""
Django Registrations Application Froms.

It exposes the following Registrations application forms
MyRegForm -- To hide a user name field in registration form of
    Django-Registrations
EducationForm -- Education model form
ExperienceForm -- Experience model form
StudentForm -- Student Candidate Application model form.
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from registration.forms import RegistrationFormUniqueEmail
from djangoformsetjs.utils import formset_media_js
from registrations.models import *
from functools import partial
from phonenumber_field.widgets import PhoneNumberPrefixWidget,PhoneNumberInternationalFallbackWidget
from django.template.defaultfilters import filesizeformat
from django.forms import BaseFormSet
from import_export import resources, fields as i_e_fields, widgets as widg
from django.core.validators import validate_email
from import_export import resources
from phonenumber_field.formfields import PhoneNumberField

import csv
import re
import xlrd
import tempfile
import os
import codecs
import phonenumbers
DateInput = partial(forms.DateInput, {'class': 'datepicker'})

class EducationForm(forms.ModelForm):
    """Education model form."""
    other_degree =forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    other_discipline =forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)

    def clean_other_degree(self):
        other_degree = self.cleaned_data.get('other_degree',False)
        return '' if not other_degree else other_degree

    def clean_other_discipline(self):
        other_discipline = self.cleaned_data.get('other_discipline',False)
        return '' if not other_discipline else other_discipline


    class Meta(object):
        model = StudentCandidateQualification
        exclude = ('application',)

    class Media(object):
        js = formset_media_js


class ExperienceForm(forms.ModelForm):
    start_date = forms.DateField(widget=DateInput(format='%d-%m-%Y'),
                                 input_formats=('%d-%m-%Y',))
    end_date = forms.DateField(widget=DateInput(format='%d-%m-%Y'),
                               input_formats=('%d-%m-%Y',))

    class Meta(object):
        model = StudentCandidateWorkExperience
        exclude = ('application',)

    class Media(object):
        js = formset_media_js

def studentApplication(pg_code):
    pg=Program.objects.get(program_code=pg_code)

    def showExamLocationChoice1(pg):
        exam = [(None,'-- Choose Exam location --')]
        exam += [(x.id,x.location_name)for x in pg.available_in_cities.all()]
        return  exam

    def showExamLocationChoice():
        exam = [(None,'Choose Location')]
        exam += [(x.id,x.location_name)for x in Location.objects.filter(is_exam_location=True)]
        return  exam

    class StudentForm(forms.ModelForm):
        date_of_birth = forms.DateField(widget=DateInput(format='%d-%m-%Y'),
                                        input_formats=('%d-%m-%Y',))
        current_org_employment_date = forms.DateField(
            widget=DateInput(format='%d-%m-%Y'),
            input_formats=('%d-%m-%Y',),required=False)
        phone = forms.CharField(widget=PhoneNumberPrefixWidget(),required=False)
        mobile = forms.CharField(widget=PhoneNumberPrefixWidget(),required=False)
        current_location = forms.ChoiceField(choices=showExamLocationChoice1(pg))
        exam_location = forms.CharField(required=False,widget=forms.HiddenInput())

        program = forms.CharField(widget=forms.HiddenInput(attrs={'value':pg.id}))
        program_display = forms.CharField(widget=forms.TextInput(attrs={
            'value':pg.program_name,
            'readonly':'true'}
            ))

        def clean_current_location(self):
            if not self.cleaned_data['current_location']:
                raise forms.ValidationError(_('error in current location'))
            return Location.objects.get(id=int(self.cleaned_data['current_location']))

        def clean_program(self):
            if not self.cleaned_data['program']:
                raise forms.ValidationError(_('error in program'))
            return Program.objects.get(id=int(self.cleaned_data['program']))

        def __init__(self, *args, **kwargs):
            super(StudentForm, self).__init__(*args, **kwargs)
            self.fields['current_location'] = forms.ChoiceField(choices=showExamLocationChoice1(pg))

        class Meta(object):
            model = StudentCandidateApplication
            exclude = ('application_status', 'admit_year', 'created_on_datetime',
                       'last_updated_on_datetime')

    return StudentForm
