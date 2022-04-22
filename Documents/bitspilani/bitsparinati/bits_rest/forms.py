from django import forms
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from phonenumber_field.formfields import PhoneNumberField
from .models import EduvanzApplication
import phonenumbers

class PlainTextWidget(forms.Widget):
	def render(self, name, value, attrs=None):
		if value is None:
			value = ''
		final_attrs = self.build_attrs(attrs, name=name)
		return format_html('<span{}>{}</span>',
					flatatt(final_attrs),
					force_text(value))

class AdhocForm(forms.Form):
	full_name = forms.CharField(max_length=100, required=True) 
	mobile = PhoneNumberField(widget=PhoneNumberPrefixWidget(), required=True)
	student_id = forms.CharField(label='Student ID',max_length=100, required=False, widget=PlainTextWidget())
	student_application_id = forms.CharField(label='Application ID',max_length=100, required=False, widget=PlainTextWidget())

	def clean_full_name(self):
		full_name = self.cleaned_data['full_name']
		RegexValidator(regex='^[a-zA-Z\s]+$', message='This field accepts only alphabets')(full_name)
		return full_name

class NonEditableAdhocForm(AdhocForm):
	def __init__(self, *args, **kwargs):
		super(NonEditableAdhocForm, self).__init__(*args, **kwargs)
		self.fields['mobile'].disabled = True
		self.fields['full_name'].disabled = True