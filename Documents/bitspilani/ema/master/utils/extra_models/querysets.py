from django.db.models import (Max, Q, Case, When, F, 
	Value, TextField, CharField, IntegerField, BooleanField, Subquery)
from django.db import models as M
from django.db.models import functions as FUN
from master.models import *
import operator 
import functools
from master.utils.constants import *
from django.db.models.functions import Concat, Substr 
from django.db.models import OuterRef, Subquery, Value
from django_mysql.models import GroupConcat
from datetime import datetime
from ema import default_settings as S
from functools import reduce
import pandas as pd
import numpy as np
from datetime import datetime as dt
from django.utils.dateparse import parse_datetime


def get_instance_or_none(model, **query_kwargs):
	try:
		instance = model.objects.get(**query_kwargs)
	except Exception as e:
		instance = None
	return instance

def get_instance_or_create_with_status(model, **query_kwargs):
	return model.objects.get_or_create(**query_kwargs)

def get_instance_or_create(model, **query_kwargs):
	instance, created = get_instance_or_create_with_status(model, **query_kwargs)
	return instance

def get_instance_or_none_from_qs(model, queryset, **query_kwargs):
	try:
		instance = queryset.get(**query_kwargs)
	except model.DoesNotExist:
		instance = None
	return instance

def get_filter_queryset(model, **query_kwargs):
	return model.objects.filter(**query_kwargs)

def get_filter_values(model, *values, **filter_kwargs):
	return model.objects.filter(**filter_kwargs).values(*values)

def get_all_instances(model):
	return model.objects.all()

def get_student_details():
	student_reg = StudentRegistration.objects.annotate(program_code=Substr('student__student_id', 5, 4))
	# current_exam = CurrentExam.objects.filter(
	# 	is_active=True, 
	# 	program__program_code=OuterRef(OuterRef('program_code')),
	# 	batch=OuterRef(OuterRef('student__batch')),
	# 	semester=OuterRef(OuterRef('semester')),
	# 	)

	# course_exam_schedule = CourseExamShedule.objects.filter(
	# 	course_code=OuterRef('course_code'),
	# 	semester=OuterRef('semester'),
	# 	exam_type__in=Subquery(current_exam.values('exam_type'))
	# 	)

	course_exam_schedule = CourseExamShedule.objects.filter(
		course_code=OuterRef('course_code'),
		)

	return student_reg.annotate(
		stud_id=F('student__student_id'),
		stud_name=F('student__student_name'),
		course_name=Subquery(course_exam_schedule.values('course_name')[:1]),
		sem_name=F('semester__semester_name'),
		pg_code=Substr('student__student_id', 5, 4),
	)

def get_search_filter(queryset, search, *args):
	contains_args = ['{}__icontains'.format(x) for x in args]
	condition = lambda item :reduce(operator.or_, 
		( Q(**{x:item}) for x in contains_args )
	) 
	return queryset.filter(
		reduce(
			operator.and_, 
			( condition(item) for item in search.split())
		)
	)

def get_attendance_data_view(**kwargs):
	user_email = kwargs.get("user_email",None)
	user_role = kwargs.get("user_role",None)
	ea = ExamAttendance.objects.filter(exam_venue=OuterRef('examvenueslotmap__exam_venue'),
		course=OuterRef('courseexamshedule'),
		semester=OuterRef('courseexamshedule__semester'),
		exam_type=OuterRef('courseexamshedule__exam_type'),
		exam_slot=OuterRef('courseexamshedule__exam_slot'),
		)
	queryset = ExamVenueSlotMap.course_exam_schedule.through.objects.filter(
		courseexamshedule__semester__in=Subquery(
			CurrentExam.objects.filter(is_active=True).values('semester')
			),
		).annotate(
		location=F('examvenueslotmap__exam_venue__location__location_name'),
		exam_venue=F('examvenueslotmap__exam_venue__venue_short_name'),
		course=Concat('courseexamshedule__course_code', 
			Value(' : '), 'courseexamshedule__course_name'
			),
		attendance_count=Subquery(ea.values('attendance_count')[:1])
		)

	if kwargs.get('exam_venue'):
		queryset = queryset.filter(examvenueslotmap__exam_venue=kwargs['exam_venue'])

	if kwargs.get('location'):
		queryset = queryset.filter(examvenueslotmap__exam_venue__location=kwargs['location'])

	if kwargs.get('course') and kwargs.get('course') != 'n':
		queryset = queryset.filter(courseexamshedule__course_code=kwargs['course'].split(":")[0])

	if(user_role == 'CO-ORDINATOR'):
		cordinator_location = LocationCoordinator.objects.filter(coordinator_email_id=user_email)

		queryset = queryset.filter(
				examvenueslotmap__exam_venue__location__in=Subquery(cordinator_location.values('location'))
				)
	return queryset


# def get_attenlist_halltcktissue(**kwargs):

# 	is_active_student = False
# 	sr = StudentRegistration.objects.annotate(program_code=Substr('student__student_id', 5, 4),)
# 	ce = CurrentExam.objects.filter(is_active=True,)

# 	if kwargs.get('program'):
# 		ce = ce.filter(program=kwargs.get('program'))

# 	if ce.exists():
# 		is_active_student = functools.reduce(operator.or_,
# 		(
# 			Q(
# 				program_code=x.program.program_code,
# 				semester=x.semester,
# 				student__batch=x.batch,
# 				# exam_type=x.exam_type,
# 			) for x in ce.iterator()
# 		)
# 		)
# 	if is_active_student:
# 		sr = sr.filter(is_active_student)


# 	sr = sr.values_list('student',flat=True)

# 	ht = HallTicket.objects.filter(student__in=sr,is_cancel=False).annotate(
# 		program_code=Substr('student__student_id', 5, 4),
# 		s_id=F('student__student_id'),
# 		sem_id=F('semester__pk'),
# 		student_name=Concat('student__student_id', Value(' ('), 'student__student_name', Value(')')),
# 		course_code=Concat('course__course_code', Value(' : '), 'course__course_name'),
# 		exam_type_name=Concat('exam_type__evaluation_type', Value(' '), 'exam_type__exam_type'),
# 		exam_slot_name=Concat('exam_slot__slot_day', Value(' '), 'exam_slot__slot_date', Value(' '), 'exam_slot__slot_name', output_field=CharField()),
# 		exam_venue_name=F('exam_venue__venue_short_name'),
# 		photo=F('student__photo'),
# 		venue_short_name=F('exam_venue__venue_short_name'),
# 	)


# 	if kwargs.get('photo_missing'):
# 		ht = ht.filter(Q(student__photo__isnull=True)|Q(student__photo=''))

# 	if kwargs.get('location'):
# 		ht = ht.filter(exam_venue__location=kwargs.get('location'))

# 	if kwargs.get('exam_venue'):
# 		ht = ht.filter(exam_venue=kwargs.get('exam_venue'))


# 	if is_active_student:
# 		ht = ht.filter(is_active_student)
# 	else:
# 		ht = ht.none()
# 	ht = ht.order_by('student_id')
# 	return ht

def get_attenlist_halltcktissue(self,**kwargs):
	is_active_student = False
	student_generated = []
	left_join=pd.DataFrame()
	final_dict={}
	ce = CurrentExam.objects.filter(is_active=True,)
	# When the user select the multiple programs

	if kwargs.get('program'):
		if kwargs.get('program')[0]=='undefined':
			pass

		else:
			ce = ce.filter(program__in=kwargs.get('program'))
		
	if ce.exists():
		is_active_student = functools.reduce(operator.or_,
		(
			Q(
				program_code=x.program.program_code,
				semester=x.semester,
				student__batch=x.batch,
				exam_type=x.exam_type,
			) for x in ce.iterator()
		)
		)


	ht = HallTicket.objects.filter(is_cancel=False).annotate(
		program_code=Substr('student__student_id', 5, 4),
		s_id=F('student__student_id'),
		sem_id=F('semester__pk'),
		student_name=Concat('student__student_id', Value(' ('), 'student__student_name', Value(')')),
		stud_email_id=Concat('student__student_id', Value('@wilp.bits-pilani.ac.in')),
		stud_personal_email=F('student__personal_email'),
		stud_personal_phone=F('student__personal_phone'),
		stud_name = F('student__student_name'),
		semester_name=F('semester__semester_name'),
		batch_name=F('student__batch__batch_name'),
		course_code=Concat('course__course_code', Value(' : '), 'course__course_name'),
		exam_type_name=Concat('exam_type__evaluation_type', Value(' '), 'exam_type__exam_type'),
		ex_type=F('exam_type__exam_type'),
		exam_slot_name=Concat('exam_slot__slot_day', Value(' '), 'exam_slot__slot_date', Value(' '), 'exam_slot__slot_name', output_field=CharField()),
		exam_slot_name_dt_first=Concat('exam_slot__slot_date', Value(' '), 'exam_slot__slot_day', Value(' '), 'exam_slot__slot_name', output_field=CharField()),
		exam_venue_name=F('exam_venue__venue_short_name'),
		photo=F('student__photo'),
		venue_short_name=F('exam_venue__venue_short_name'),
		custom_order=Case(
						When(Q(exam_slot__slot_name__contains="FN") | Q(exam_slot__slot_name__contains="FORENOON"), then=Value(1)),
						When(Q(exam_slot__slot_name__contains="AN") | Q(exam_slot__slot_name__contains="AFTERNOON"), then=Value(2)),
						output_field=IntegerField(),
						)
	)
	ht=ht.exclude(exam_slot_id=1)

	if ce.exists():
		is_student_reg = functools.reduce(operator.or_,
		(
			Q(
				program_code=x.program.program_code,
				semester=x.semester,
				student__batch=x.batch,
				# exam_type=x.exam_type,
			) for x in ce.iterator()
		)
		)

	sr = StudentRegistration.objects.annotate(program_code=Substr('student__student_id', 5, 4),
											student_reg=Concat('student__student_id', Value(' ('), 'student__student_name', Value(')')),
											st_name=F('student__student_name'),
											st_email_id=Concat('student__student_id', Value('@wilp.bits-pilani.ac.in')),
											sem_name=F('semester__semester_name'),
											st_personal_email = F('student__personal_email'),
											c_code=F('course_code'),
											st_personal_phone=F('student__personal_phone'),
											b_name=F('student__batch__batch_name'),
											).order_by('student__student_id')

	

	if self.request.GET.get('search'):
		search_name=CourseExamShedule.objects.filter(course_name__icontains=self.request.GET.get('search').strip()).values_list('course_code',flat=True)
		sr = sr.filter(Q(student_reg__icontains=self.request.GET.get('search').strip())|Q(course_code__icontains=self.request.GET.get('search').strip())|Q(course_code__in=search_name))
		ht = ht.filter(Q(student_name__icontains=self.request.GET.get('search').strip())|Q(s_id__icontains=self.request.GET.get('search').strip())|Q(course_code__icontains=self.request.GET.get('search').strip())).order_by('exam_slot__slot_date', 'custom_order')

	# To remove students from hallticket table(current exam)
	if is_active_student:
		ht = ht.filter(is_active_student)
	else:
		ht = ht.none()
	
	# To remove students from student registration table (current exam)
	if is_active_student:
		sr = sr.filter(is_student_reg)
	else:
		sr = sr.none()

	stu = pd.DataFrame(list(sr.values()))
	ht = ht.order_by('student__student_id')


	if ht and sr:
		student_generated = list(set(list(ht.values_list('student_name',flat=True))))
		stu = stu[~stu['student_reg'].isin(student_generated)]

	if ht:
		hall = pd.DataFrame(list(ht.values()))
		if stu.empty:
			pass
		else:	
			left_join = pd.merge(stu,hall,on=['student_id','course_code'],how='outer',indicator=True)
	else:
		left_join = stu

	if ht and stu.empty:
		hall = pd.DataFrame(list(ht.values()))
		left_join = pd.merge(stu,hall,on=['student_id','course_code'],how='outer',indicator=True)
	else:
		pass
	# We are only sending hallticket content whenthe user chosen exam_type,location,date,exam_slot because 
	# these values will not be present in student registration table
	if kwargs.get('exam_type'):
		ht = ht.filter(exam_type_id=self.request.GET.get('exam_type')).order_by('exam_slot__slot_date', 'custom_order')
		left_join = pd.DataFrame(list(ht.values()))
			
	if kwargs.get('location'):
		ht = ht.filter(exam_venue__location=kwargs.get('location')).order_by('exam_slot__slot_date', 'custom_order')
		left_join = pd.DataFrame(list(ht.values()))

	if kwargs.get('exam_venue'):
		ht = ht.filter(exam_venue=kwargs.get('exam_venue')).order_by('exam_slot__slot_date', 'custom_order')
		left_join = pd.DataFrame(list(ht.values()))
		
	if kwargs.get('exam_slot'):
		ht = ht.filter(exam_slot_id=self.request.GET.get('exam_slot')).order_by('exam_slot__slot_date', 'custom_order')

		left_join = pd.DataFrame(list(ht.values()))	
	if kwargs.get('date'):
		
		ht = ht.filter(created_on__gt=parse_datetime(self.request.GET.get('date'))).order_by('exam_slot__slot_date', 'custom_order')
		left_join = pd.DataFrame(list(ht.values()))	
	
	left_join = left_join.replace(np.nan, '-') 
	final_dict = left_join.to_dict('records')
	return final_dict



def get_date_day_or_empty(date_str, format = '%Y-%m-%d', display_format = "%A"):
	try:
		date_day = datetime.strptime(date_str, format).date().strftime(display_format)
	except Exception as e:
		date_day = ''
	return date_day