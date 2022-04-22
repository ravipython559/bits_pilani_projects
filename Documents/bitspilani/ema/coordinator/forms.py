from django import forms
from master.models import *
from master.forms.form_fields import *
from master.forms import forms as master_forms
from django.db.models import F, Value, OuterRef, Subquery

def cordinator_attendence_form(user):
	class LocVenueCourseForm(master_forms.AdminLocVenueCourseCodeForm):

		def __init__(self,*args,**kwargs):
			super().__init__(*args,**kwargs)
			cordinator_location = LocationCoordinator.objects.filter(coordinator_email_id=user.email)
			self.fields['location'].queryset = Location.objects.filter(
				pk__in=Subquery(cordinator_location.values('location'))
			)
	return LocVenueCourseForm