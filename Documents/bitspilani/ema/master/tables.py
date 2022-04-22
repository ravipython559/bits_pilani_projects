from master.models import *
from table import Table
from table.columns import Column, LinkColumn, Link
from table.utils import A
from django.urls import reverse_lazy
from master.utils.datatable.columns import *
from django.conf import settings
import re


def stud_reg_view(ajax_url=None,*args, **kwargs):

	class EMATable(Table):
		stud_id = FilterColumn(field = 'stud_id', header = 'Student ID')
		stud_name = FilterColumn(field = 'stud_name', header = 'Student Name')
		course_code = FilterColumn(field = 'course_code', header = 'Course Code')
		course_name = FilterColumn(field = 'course_name', header = 'Course Name')
		sem_name = FilterColumn(field = 'sem_name', header = 'Semester')

		class Meta:
			model = StudentRegistration
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url, kwargs={
				'pg_code' : kwargs.get('pg_code') or 'n',
				'sem' : kwargs.get('semester') or 0,
				})

	return EMATable

def get_attendance_data_view_table(global_js_variable='global_js_variable', bulk_prefix='attendence-', **kwargs):

	class AttendanceDataViewTable(Table):
		location = Column(field='location', header='Location')
		exam_venue = Column(field='exam_venue', header='Exam Venue')
		course = Column(field='course', header='Course')
		planned = PlannedColumn(header='Students Planned', sortable=False, searchable=False,)
		attendance_count = IntegerColumn(global_js_variable, bulk_prefix, field='attendance_count', header='Actual Attendance')

		class Meta:
			model = ExamVenueSlotMap.course_exam_schedule.through
			search = False
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('master:ajax:attendance-data-view', kwargs={
				'loc' : kwargs.get('location').pk if kwargs.get('location') else 0,
				'venue' : kwargs.get('exam_venue').pk if kwargs.get('exam_venue') else 0,
				'course' :  re.compile(r"[^\w:]").sub("",kwargs.get('course')) if kwargs.get('course') else 'n',
			})

	return AttendanceDataViewTable

class ExamTypeColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		check_for_current_exam = CurrentExam.objects.filter(is_active=True,
													semester_id=value.semester_id,
													program__program_code=value.program_code).values_list('exam_type_id',flat=True)
		if value.exam_type_id in check_for_current_exam and value.venue_short_name != '-':
			return data
		else:
			return '-'


class ExamSlotColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		# if value.exam_slot.slot_name == S.EXAM_SLOT_NAME:
		# 	return escape('-')

		check_for_current_exam = CurrentExam.objects.filter(is_active=True,
													semester_id=value.semester_id,
													program__program_code=value.program_code).values_list('exam_type_id',flat=True)
		if value.exam_type_id in check_for_current_exam and value.venue_short_name != '-':
			return data
		else:
			data='-'
		return data

		return escape(data if data else '')


class ExamVenueColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		check_for_current_exam = CurrentExam.objects.filter(is_active=True,
													semester_id=value.semester_id,
													program__program_code=value.program_code).values_list('exam_type_id',flat=True)

		if value.exam_type_id in check_for_current_exam and value.venue_short_name != '-': 
			return data
		else:
			return '-'

def get_hallticket_issue_status_table(**kwargs):
	class HAllTicketIssueStatusTable(Table):
		student_name = Column(field='student_name', header='Student ID/ Student Name')
		course_code = Column(field='course_code', header='Course Code/ Course Name', sortable=False, searchable=False,)
		exam_type = ExamTypeColumn(field='exam_type_name', header='Exam Type')
		exam_slot = ExamSlotColumn(field='exam_slot_name', header='Exam Slot',sortable=False, searchable=False)
		exam_venue = ExamVenueColumn(field='exam_venue_name', header='Exam Venue', sortable=False, searchable=False)

		# photo = LinkColumn(field='photo', header='Photo',
		# 	links=[PhotoLink(text='photo', viewname='administrator:admin_router:student-photo-view', args=(A('s_id'),),attrs={'target':'_blank'},),],
		# 	sortable=False, searchable=False, 
		# )
		prev_hall_ticket = LinkColumn(field='venue_short_name', header='HallTicket', 
			links=[HallTicketLink(text='hall ticket', viewname='administrator:admin_router:generate-hall-ticket-pdf', args=(A('s_id'),A('sem_id')),attrs={'target':'_blank'},),],
			sortable=False, searchable=False, 
		)

		class Meta:
			attrs = {'class': 'table table-bordered table-striped'}
			model = HallTicket
			pagination = True
			ajax = True
			ajax_source = reverse_lazy('master:ajax:hall-ticket-attendance', 
				kwargs={
				'loc' : (kwargs.get('location') and kwargs.get('location').pk) or 0,
				'miss' : int(bool(kwargs.get('photo_missing'))),
				'pg' : (kwargs.get('program') and kwargs.get('program').pk) or 0,
				'venue' : (kwargs.get('exam_venue') and kwargs.get('exam_venue').pk) or 0,
				}
			)

	return HAllTicketIssueStatusTable



def couse_exam_schedule_paging(*args, **kwargs):

	class CESTable(Table):
		semester_name = FilterColumn(field = 'sem_name', header = 'Semester Name')
		course_code = FilterColumn(field = 'course_code', header = 'Course Code', searchable=True)
		course_name = FilterColumn(field = 'course_name', header = 'Course Name', searchable=True)	
		comp_code = FilterColumn(field = 'comp_code', header = 'Comp Code', searchable=True)
		unit = FilterColumn(field = 'unit', header = 'Units')
		exam_details = FilterColumn(field = 'exam_details', header = 'Exam Type')
		slot_details = FilterColumn(field = 'slot_details', header = 'Exam Slot')

		class Meta:
			model = CourseExamShedule
			pagination = True
			ajax = True
			ajax_source = reverse_lazy(kwargs.get('ajax_url'),kwargs = {
				'semester' : kwargs.get('semester') or 0,
				'exam_type': kwargs.get('exam_type') or 0,
				'exam_slot': kwargs.get('exam_slot') or 0,
 			})


	return CESTable