from django import template
import os
from registrations.models import *
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.db.models import Q
from django.contrib.auth import get_user_model
from application_specific.specific_user import *
register = template.Library()

@register.filter(name='get_specific_program')
def get_specific_program(email):
	s_e_d = ProgramDomainMapping.objects.filter(Q(email = email)|
		Q(email_domain__iexact = email.split('@')[1])).exists()
	if s_e_d:
		pg = specific_pg(email)
		return pg.program_name
	else:return False

@register.filter(name='is_employee_number')
def is_employee_number(email):
	s_e_d = ProgramDomainMapping.objects.filter(Q(email = email)|
		Q(email_domain__iexact = email.split('@')[1])).exists()
	return True if s_e_d else False




@register.filter(name='document_exist')
def document_exist(email):
	user = get_user_model().objects.get(email__iexact=email)
	pg = StudentCandidateApplication.objects.get(login_email=user).program
	return True if ProgramDocumentMap.objects.filter(program=pg).exists() else False

@register.simple_tag
def specific_location(query):
    query=query.values('location_name')
    q = [x['location_name'] for x in query]
    return ', '.join(q)


@register.filter(name='document_path')
def document_path(path=None):
	return path if path else 'guidelines_document/default.html'

@register.filter(name='is_image')
def is_image(path):
	return True if path else False
