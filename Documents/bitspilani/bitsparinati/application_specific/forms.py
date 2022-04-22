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
from phonenumber_field.widgets import (PhoneNumberPrefixWidget,
	PhoneNumberInternationalFallbackWidget)
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



def showUpFileFormChoice():
    UPCHOICE=[(None,'Choose Document Type')]
    UPCHOICE+=[(x.id,x.document_name)for x in DocumentType.objects.filter(mandatory_document=False)]
    return UPCHOICE


class UploadFileForm(forms.Form):
    file = forms.FileField(required=False,widget=forms.FileInput(attrs={'class':'filecss'}))
    document_id = forms.ChoiceField(choices=showUpFileFormChoice())

    class Media(object):
        js = formset_media_js

    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.fields['document_id'] = forms.ChoiceField(choices=showUpFileFormChoice())

    def clean_file(self):
        prefix = self.prefix
        content = self.cleaned_data.get('file',False)
        if content:
            max_upload_size = 10485760
            if content.size > max_upload_size:
                raise forms.ValidationError(_('Please keep file size under %s. Current file size %s') % (
                    filesizeformat(max_upload_size),filesizeformat(content.size)
                    )
                )
        return content

    def clean_document_id(self):
        if not self.cleaned_data['document_id']:
            raise forms.ValidationError(_('specify document type'))
        return self.cleaned_data['document_id']

class UploadRequiredFileForm(forms.Form):
    document_name = forms.CharField(max_length=254,
        widget=forms.HiddenInput(),)
    file = forms.FileField(required=False,widget=forms.FileInput(attrs={'class':'filecss'}))
    document_id = forms.CharField(max_length=254,widget=forms.HiddenInput())

    def clean_file(self):

        content = self.cleaned_data['file']
        if content:
            max_upload_size = 10485760
            if content.size > max_upload_size:
                raise forms.ValidationError(_('Please keep file size under %s. Current file size %s') % (
                    filesizeformat(max_upload_size),
                    filesizeformat(content.size)
                    ),code='invalid'
                )
        return content


class UploadRequiredEditFileForm(forms.Form):
    document_name = forms.CharField(max_length=254,
        widget=forms.HiddenInput(),)
    file = forms.FileField(widget=forms.FileInput({'class':'filecss'}),required=False)
    document_id = forms.CharField(max_length=254,widget=forms.HiddenInput())
    exist_file =forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)

    def clean_file(self):
        content = self.cleaned_data['file']
        prefix = self.prefix
        exist_id_file="%s-exist_file"%(prefix)
        existing_id=self.data[exist_id_file]

        if content:
            max_upload_size = 10485760
            if content.size > max_upload_size:
                raise forms.ValidationError(_('Please keep file size under %s. Current file size %s') % (
                    filesizeformat(max_upload_size),
                    filesizeformat(content.size)
                    ),code='invalid'
                )
        return content

def showUpchoices():
    UPCHOICE=[(None,'Choose Document Type')]
    UPCHOICE+=[(x.id,x.document_name)for x in DocumentType.objects.filter(mandatory_document=False)]
    return UPCHOICE

class UploadEditFileForm(forms.Form):
    file = forms.FileField(required=False,widget=forms.FileInput(attrs={'class':'filecss'}))
    document_id = forms.ChoiceField(choices=showUpchoices())
    exist_file =forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)

    exist_file_id =forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)

    def __init__(self, *args, **kwargs):
        super(UploadEditFileForm, self).__init__(*args, **kwargs)
        self.fields['document_id'] = forms.ChoiceField(choices=showUpchoices())

    class Media(object):
        js = formset_media_js

    def clean_file(self):
        content = self.cleaned_data['file']
        prefix = self.prefix
        exist_id_name="%s-exist_file_id"%(prefix)
        existing_id=self.data[exist_id_name]
        if content or (existing_id and content):
            max_upload_size = 10485760
            if content.size > max_upload_size:
                raise forms.ValidationError(_('Please keep file size under %s. Current file size %s') % (
                    filesizeformat(max_upload_size),filesizeformat(content.size)
                    )
                )
        return content

    def clean_document_id(self):
        if not self.cleaned_data.get('document_id'):
            raise forms.ValidationError(_('specify document type'))
        return self.cleaned_data['document_id']

class BaseUploadFileEditFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):return

        a=[]
        for form in self.forms:
            content = form.cleaned_data.get('file',False)
            exist_file = form.cleaned_data.get('exist_file_id',False)
            print form.cleaned_data.get('document_id')
            if form.cleaned_data.get('document_id') and \
            not form.cleaned_data.get('DELETE') and (content or exist_file):
                a.append(form.cleaned_data.get('document_id'))

        unique_values(a)

class BaseUploadFileFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):return
        a=[]
        for form in self.forms:
            print form.cleaned_data.get('document_id')
            content = form.cleaned_data.get('file',False)
            if form.cleaned_data.get('document_id') and \
             not form.cleaned_data.get('DELETE') and content:
                a.append(form.cleaned_data.get('document_id'))

        unique_values(a)


class ReviewAcceptedForm(forms.Form):
    doc_type = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    status = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    rejection_reason = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    doc_link = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    doc_name = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)

class ReviewRejectedForm(forms.Form):
    doc_type = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    status = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    rejection_reason = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    doc_link = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    doc_name = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    doc_id = forms.CharField(max_length=254,required=False,
        widget=forms.HiddenInput(),)
    file = forms.FileField(widget=forms.FileInput(attrs={'required':'true','class':'filecss'}))
    x = forms.FloatField(required=False,widget=forms.HiddenInput())
    y = forms.FloatField(required=False,widget=forms.HiddenInput())
    width = forms.FloatField(required=False,widget=forms.HiddenInput())
    height = forms.FloatField(required=False,widget=forms.HiddenInput())
    rotate = forms.FloatField(required=False,widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(ReviewRejectedForm, self).__init__(*args, **kwargs)
        if self.initial and self.initial['doc_type'] == 'APPLICANT PHOTOGRAPH':
            self.fields['file'].widget.attrs['accept'] = 'image/*'

    def clean_file(self):
        content = self.cleaned_data['file']
        if not content:
            raise forms.ValidationError(_('file upload required'))
        return content
