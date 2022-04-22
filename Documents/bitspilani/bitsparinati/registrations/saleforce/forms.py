from django import forms
from registrations.models import Program

class SalesForceFilterForm(forms.Form):
	status_choice = (
		(None,'Choose Status'),
		('201 200','Success'),
		('not 201 200','Failure'),
		)
	status = forms.ChoiceField(widget=forms.Select(attrs={'class':'input'}),
		choices=status_choice,
		required=False,
		label = 'Json Status',
	)


class SpecificSummaryDataForm(forms.Form):
	program = forms.ModelChoiceField(
				queryset=Program.objects.filter(program_type='specific'),
				empty_label='----------',
				required=False
				)
