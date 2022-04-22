from master.models import *
from table import Table
from table.columns import Column, LinkColumn, Link
from table.utils import A
from django.urls import reverse_lazy
from master.utils.datatable.columns import *
from django.conf import settings


def get_hallticket_issue_status_table_coordinator(**kwargs):
	class CoordinatorHAllTicketIssueStatusTable(Table):
		student_name = Column(field='student_name', header='Student ID/ Student Name')
		course_code = Column(field='course_code', header='Course Code/ Course Name', sortable=False, searchable=False,)
		exam_type = Column(field='exam_type_name', header='Exam Type')
		exam_slot = ExamSlotColumn(field='exam_slot_name', header='Exam Slot',sortable=False, searchable=False)
		exam_venue = Column(field='exam_venue_name', header='Exam Venue', sortable=False, searchable=False)
		photo = LinkColumn(header='Photo',
			links=[PhotoLink(text='photo', viewname='coordinator:coordinator_router:student-photo-view', args=(A('s_id'),),attrs={'target':'_blank'},),],
			sortable=False, searchable=False, 
		)
		prev_hall_ticket = LinkColumn(header='HallTicket', 
			links=[HallTicketLink(text='hall ticket', viewname='coordinator:coordinator_router:generate-hall-ticket-pdf', args=(A('s_id'),A('semester_id')),attrs={'target':'_blank'},),],
			sortable=False, searchable=False, 
		)

		class Meta:
			attrs = {'class': 'table table-bordered table-striped'}
			model = HallTicket
			pagination = True
			ajax = True
			ajax_source = reverse_lazy('coordinator:coordinator_ajax:halltick-attend-view-ajax', 
				kwargs={
				'loc' : (kwargs.get('location') and kwargs.get('location').pk) or 0,
				'miss' : int(bool(kwargs.get('photo_missing'))),
				'pg' : (kwargs.get('program') and kwargs.get('program').pk) or 0,
				'venue' : (kwargs.get('exam_venue') and kwargs.get('exam_venue').pk) or 0,
				}
			)

	return CoordinatorHAllTicketIssueStatusTable