from django import template
from registrations.models import *
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.db.models import Q
import datetime
from dateutil.relativedelta import relativedelta
register = template.Library()



@register.simple_tag
def program_display(id):
	return Program.objects.get(id=id).program_name


@register.simple_tag
def show_application_status(value):
	try:
		cs = CandidateSelection.objects.get(
			application__student_application_id = value )
	except CandidateSelection.DoesNotExist :
		sca = StudentCandidateApplication.objects.get(
			student_application_id = value
			)
		return sca.student_application_id
	else:
		return cs.new_application_id if cs.new_application_id else \
		 cs.application.student_application_id
