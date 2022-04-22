from master.ajax.views import HallTicketAttendanceAjaxView
from django.views.generic.list import BaseListView
from django.http import StreamingHttpResponse
from djqscsv import render_to_csv_response
from table.tables import TableDataMap
from ema import default_settings as S
from master.models import ExamSlot
import csv


class CSVHallTicketAttendanceAjaxView(HallTicketAttendanceAjaxView):

	hall_ticket_csv_value =[
		'student_name',
		'course_code',
		'exam_type_name',
		'exam_slot_name',
		'exam_venue_name',
		'photo',
		'venue_short_name',
		]

	hall_ticket_csv_header={
		'student_name':'Student ID/Studnt Name',
		'course_code':'Course Code/ Course Name',
		'exam_type_name':'Exam Type',
		'exam_slot_name':'Exam Slot',
		'exam_venue_name':'Exam Venue',
		'photo':'Photo',
		'venue_short_name': 'Hall Ticket',
		}

	def hall_ticket_serializer_map(self):
		default_es = ExamSlot.objects.get(slot_name=S.EXAM_SLOT_NAME)
		default_string = '%s %s %s' %(default_es.slot_day, default_es.slot_date, default_es.slot_name)
		return {
			'photo':(lambda x: 'Yes' if x else ' '),
			'exam_slot_name':(lambda x: '-' if x == default_string else x),
			'venue_short_name': (lambda x: ' ' if x==S.VENUE_SHORT_NAME else 'Yes'),
		}

	def get(self, request, *args, **kwargs):
		self.query_data = {}
		self.columns = TableDataMap.get_columns(self.token)
		self.query_data['sSearch'] = request.GET.get("sSearch")
		return BaseListView.get(self, request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(BaseListView, self).get_context_data(**kwargs)
		queryset = context["object_list"]
		return {'queryset':self.filter_queryset(queryset)}

	def render_to_response(self, context, **response_kwargs):
		return render_to_csv_response(context['queryset'].values(*self.hall_ticket_csv_value),
			append_datestamp=True,
			field_header_map=self.hall_ticket_csv_header,
			field_order=self.hall_ticket_csv_value,
			field_serializer_map=self.hall_ticket_serializer_map(),
			filename='hallticket_issue_status',
		)