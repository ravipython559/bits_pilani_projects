
from csv_export.views import CSVExportView
from master.models import *
from functools import reduce
from .csv_field_headers import *
from .ajax.views import HallTicketAttendanceAjaxView
import operator
from django.db.models import Max, Q, Case, When, F, Value, CharField, BooleanField, Subquery
from django.db.models.functions import Concat
from master.utils.extra_models.querysets import get_search_filter,get_student_details,get_attenlist_halltcktissue
from django.http import StreamingHttpResponse
import csv

class CSVHallTicketAttendanceAjaxView(HallTicketAttendanceAjaxView):
	def render_to_response(self, context, **response_kwargs):
		writer = csv.writer(Echo())
		headers = [col.header for col in self.columns]
		response = StreamingHttpResponse((writer.writerow(row) for row in headers + context['aaData']), 
			content_type="text/csv")
		response['Content-Disposition'] = 'attachment; filename="hall_ticket_issue_status.csv"'
		return response

class BaseStudentRegExportCSV(CSVExportView):
	model = StudentRegistration
	fields = STUDENT_REGISTRATION_FIELD
	filename = 'student_reg_list'
	specify_separator = False
	field_headers = STUDENT_REGISTRATION_HEADERS
	search_fields = STUDENT_REGISTRATION_SEARCH_FIELDS

	def get_header_name(self, model, field_name):
		return self.field_headers[field_name].title()

	def get_filter_queryset(self, filter_params=None):
		filter_exists = reduce(lambda x,y: x or y, map(lambda x:x[1], filter_params.items()), False)
		sum_filter = filter_exists and reduce(operator.and_, (
				Q(**{k: v})
					for (k, v) in filter_params.items() if v is not None
			)
		)
		return self.queryset.filter(sum_filter) if sum_filter else self.queryset

	def get_queryset(self):
		self.queryset = get_student_details()
		filter_dict = {}
		filter_dict['pg_code'] = self.request.GET.get('program') or None
		filter_dict['semester'] = self.request.GET.get('semester') or None
		query = self.get_filter_queryset(filter_params=filter_dict)
		search = self.request.GET.get('search') or None
		query = get_search_filter(query, search, *self.search_fields) if search else query
		return query