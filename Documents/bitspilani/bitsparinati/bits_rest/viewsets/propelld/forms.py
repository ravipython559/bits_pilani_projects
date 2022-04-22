from django import forms
from bits_rest.models import PropelldApplication
import uuid 

class propelldApplicationForm(forms.ModelForm):

	class Meta:
		model = PropelldApplication
		fields = ('loan_amount',)

		widgets = {
			'loan_amount': forms.HiddenInput(),
			}
