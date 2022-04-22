from django import forms
from bits_rest.models import EzcredApplication
import uuid 

class ezcredApplicationForm(forms.ModelForm):
	def save(self, commit=True):
		instance = super(ezcredApplicationForm, self).save(commit=False)
		if not instance.order_id:
			instance.order_id = '%sEzcred%s' % (instance.application.admit_year, 
				EzcredApplication.objects.count()) 
		if commit:
			instance.save()
		return instance
	class Meta:
		model = EzcredApplication
		fields = ('application', 'amount_requested', 'is_terms_and_condition_accepted')
		widgets = {	
			'application': forms.HiddenInput(), 
			'amount_requested': forms.HiddenInput(),
			'is_terms_and_condition_accepted':forms.CheckboxInput(attrs={'required': 'required'}),
		}