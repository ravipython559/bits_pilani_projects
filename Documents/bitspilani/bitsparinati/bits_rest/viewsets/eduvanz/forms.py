from django import forms
from bits_rest.models import EduvanzApplication
from django.utils import timezone
import uuid 

class ApplicationForm(forms.ModelForm):

	def save(self, commit=True):
		instance = super(ApplicationForm, self).save(commit=False)
		previous_record = EduvanzApplication.objects.filter(application=instance.application).last()
		if previous_record:
			if previous_record.status_code=='FAILED' or previous_record.status_code=='New Loan Application':
				previous_record.status_code = 'New Loan Application'
				previous_record.created_on = timezone.now()
				previous_record.save()
				return previous_record
			#ELS401 is Rejected status
			elif previous_record.status_code=='ELS401':
				instance.save()
				instance.order_id = '%sEduvanz%s' % (instance.application.admit_year, instance.id)
				instance.save()
				return instance
		else:
			instance.save()
			instance.order_id = '%sEduvanz%s' % (instance.application.admit_year, instance.id)
			instance.save()
			return instance

	class Meta:
		model = EduvanzApplication
		fields = ('application', 'amount_requested', 'is_terms_and_condition_accepted')
		widgets = {	
			'application': forms.HiddenInput(), 
			'amount_requested': forms.HiddenInput(),
			'is_terms_and_condition_accepted':forms.CheckboxInput(attrs={'required': 'required'}),
		}