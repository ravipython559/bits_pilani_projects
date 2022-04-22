from django import forms
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from registrations.models import OtherFeePayment
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField
from django.template.loader import render_to_string
from registrations.models import Program
import phonenumbers

class PlainTextWidget(forms.Widget):
	def render(self, name, value, attrs=None, *args, **kwargs):
		if value is None:
			value = ''
		final_attrs = self.build_attrs(attrs, name=name)
		return format_html('<span {}>{}</span>', flatatt(final_attrs), force_text(value))


def showUpchoices():
    UPCHOICE = [(None,'Choose Fee Type')]
    UPCHOICE += [(x['fee_type'], x['fee_type'])for x in OtherFeePayment.objects.values('fee_type').distinct().iterator()]
    return UPCHOICE

class AdhocStartUpForm(forms.ModelForm):
	fee_type = forms.ChoiceField(choices=showUpchoices(), required=True)
	email = forms.EmailField(required=True, label='Enter your e-mail',
		help_text='''
		(For existing students this will be your BITS email ID. If you are an applicant, it will be the email you have used to apply. 
		After entering the email ID, choose the program and then the Fee Type for which you need make the payment.)''')

	def __init__(self, *args, **kwargs):
		super(AdhocStartUpForm, self).__init__(*args, **kwargs)
		initial_email = self.initial.get('email') or None 
		self.fields['email'].widget.attrs={'class':'form-control'}
		self.fields['program'].widget.attrs={'class':'form-control'}
		self.fields['fee_type'].widget.attrs={'class':'form-control'}

		if initial_email:
			self.fields['email'].disabled = True

		if initial_email or kwargs.get('data') :

			email = initial_email or kwargs.get('data')['email'].strip()
			ofp = OtherFeePayment.objects.filter(email=email)

			self.fields['program'].queryset = Program.objects.filter(
				pk__in=ofp.values_list('program__pk', flat=True)
			)

		pg = self.initial.get('program') or (kwargs.get('data') and kwargs.get('data').get('program'))

		if pg:
			self.fields['fee_type'].choices = [(None,'Choose Fee Type')] 
			self.fields['fee_type'].choices += [
				(
					x['fee_type'], x['fee_type']
				) for x in ofp.filter(program=pg).values('fee_type').distinct().iterator()
			]


	def clean_email(self):
		email = self.cleaned_data['email']
		otp = OtherFeePayment.objects.filter(email=email.strip(),)
		if not otp.exists():
			raise ValidationError('You do not have any email entry for paying fees')

		return email

	def clean_program(self):
		program = self.cleaned_data['program']
		if not program:
			raise ValidationError('Please Select Program')

		return program

	def clean_fee_type(self):
		fee_type = self.cleaned_data['fee_type']
		if not fee_type:
			raise ValidationError('Please Select Fee Type')

		return fee_type

	def clean(self):
		if any(self.errors):return

		email = self.cleaned_data['email']
		program = self.cleaned_data['program']
		fee_type = self.cleaned_data['fee_type']

		try:
			otp = OtherFeePayment.objects.get(email=email.strip(), program=program, fee_type=fee_type)
			if otp.transaction_id:
				raise ValidationError('For this payment is already done')

		except OtherFeePayment.DoesNotExist as e:
			raise ValidationError('You do not have any entry for paying fees')


	class Meta(object):
		model = OtherFeePayment
		fields = ('email', 'program', 'fee_type')

def ajax_AdhocStartUpForm(ofp, is_auth_user):
	class AjaxAdhocStartUpForm(AdhocStartUpForm):
		def __init__(self, *args, **kwargs):
			super(AjaxAdhocStartUpForm, self).__init__(*args, **kwargs)
			program = Program.objects.filter(
				pk__in=ofp.values_list('program__pk', flat=True)
			)
			self.fields['program'].queryset = program

			if is_auth_user:
				self.fields['email'].disabled = True
			else:
				self.fields['email'].disabled = False



	return AjaxAdhocStartUpForm


class AdhocForm(forms.Form):
	label_template = 'registrations/label.html'
	full_name = forms.CharField(max_length=100, required=True) 
	mobile = PhoneNumberField(widget=PhoneNumberPrefixWidget(), required=True)
	pin_code = forms.IntegerField(required=True)

	def clean_full_name(self):
		full_name = self.cleaned_data['full_name']
		RegexValidator(regex='^[a-zA-Z\s]+$', message='This field accepts only alphabets')(full_name)
		return full_name

	def __init__(self,*args, **kwargs):
		super(AdhocForm, self).__init__(*args, **kwargs)
		display_text = format_html(render_to_string(self.label_template,{'tac':'https://bits-pilani-wilp.ac.in/emi-option.php',
			'emi_plans':'https://bits-pilani-wilp.ac.in/emi-option.php#semester1'}))
		# display_text = "I have read and understood the Loan Application Process and EMI Plans."
		self.fields['terms_and_condition'] = forms.BooleanField(required=False, label=display_text)

class AdhocZestMixin(object):

	def clean_terms_and_condition(self):
		terms_and_condition = self.cleaned_data['terms_and_condition']
		if not terms_and_condition:
			raise ValidationError('Please select check box if you want to proceed')
		return terms_and_condition

class AdhocZestForm(AdhocZestMixin, AdhocForm): pass

class AdhocPropelldForm(AdhocForm): pass
