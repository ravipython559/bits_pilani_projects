from django import template
from registrations.models import *
from bits_admin.models import *
from datetime import datetime
from django.contrib.auth import get_user_model
import json
from django.core.urlresolvers import reverse_lazy
from django.conf import settings 
from datetime import date
from datetime import  timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Max
from django_countries import countries

register = template.Library()

@register.simple_tag
def archive_program_check():
	return Program.objects.filter(active_for_applicaton_flag=False).exists()

@register.simple_tag
def sca_exists_check(f_date,t_date,programs):
	sca = StudentCandidateApplication.objects.filter(
		program__active_for_applicaton_flag = False
		)
	
	if programs: sca = sca.filter( program__id__in = programs )
	from_date = datetime.strptime(f_date,'%d-%m-%Y') if f_date else None
	to_date = datetime.strptime(t_date,'%d-%m-%Y') if t_date else None

	if from_date: sca = sca.filter( 
		created_on_datetime__gte = datetime(
			from_date.year,from_date.month,from_date.day,00,00,00
			) 
		)
	if to_date: sca = sca.filter( 
		created_on_datetime__lte = datetime(
			to_date.year,to_date.month,to_date.day,23,59,59
			) 
		)

	return get_user_model().objects.filter(id__in = sca.values_list('login_email', flat = True)).exists()

@register.inclusion_tag('bits_admin/archive_filter.html')
def archive_filter(a_data):
	return a_data

@register.simple_tag
def get_stud_id(pk):
	try:
		sca = StudentCandidateApplicationArchived.objects.get(pk = pk )
		cs = CandidateSelectionArchived.objects.get(application=sca,run=sca.run)
	except (StudentCandidateApplicationArchived.DoesNotExist,CandidateSelectionArchived.DoesNotExist) as e:
		return '' 
	return cs.student_id if cs.student_id else ''
	
@register.filter(name='studID_exists')
def studID_exists(app_id):
	try:
		app = StudentCandidateApplicationArchived.objects.get(id=int(app_id))
		cs = CandidateSelectionArchived.objects.get(
			application=app,
			run=app.run,
		)
	except (CandidateSelectionArchived.DoesNotExist,TypeError):
		return False

	return True if cs.student_id else False

@register.simple_tag
def display_y_m_d_arch(pk):
	sca=StudentCandidateApplicationArchived.objects.get(pk=pk)
	exp=StudentCandidateWorkExperienceArchived.objects.filter(application = sca, run=sca.run)
	tmp = timedelta(days=0)
	for x in exp:
		tmp += x.end_date - x.start_date
	tmp += sca.last_updated_on_datetime.date() - sca.current_org_employment_date
	d = date.fromordinal(tmp.days)
	return '{0} Years {1} Months {2} days'.format(d.year-1,d.month-1,d.day-1)

@register.simple_tag
def gender_display(key):
	return dict(GENDER_CHOICES).get(key,"")

@register.simple_tag
def nationality_display(key):
	return dict(NATIONALITY_CHOICES).get(key,"")

@register.simple_tag
def state_display(key):
	return dict(STATE_CHOICES).get(key,"")

@register.simple_tag
def country_display(key):
	return dict(countries).get(key,"")

@register.simple_tag
def pg_display(pg):
        try:
            return Program.objects.get(program_code=pg).program_name
        except Program.DoesNotExist: return pg

@register.simple_tag
def emp_status_display(key):
	return dict(EMPLOYMENTSTATUS_CHOICES).get(key,"")

@register.simple_tag
def fee_pay_display(key):
	return dict(FEEPAYMENT_CHOICES).get(key,"")

@register.simple_tag
def qual_display(degree):
	try:
		cat_name = Degree.objects.get(
		degree_short_name=degree)
	except Degree.DoesNotExist:
		return ""
	return cat_name.qualification_category.category_name

@register.simple_tag
def duration_display(key):
	return dict(DURATION_CHOICES).get(key,"")

@register.simple_tag
def division_display(key):
	return dict(DIVISION_CHOICES).get(key,"")

@register.simple_tag
def flag_display(key):
	return dict(PARALLEL_CHOICES).get(key,"")

@register.simple_tag
def level_display(key):
	return dict(LEVEL_CHOICES).get(key,"")