from registrations.models import *
from table import Table
from table.utils import A, mark_safe
from table.columns import Column
from table.columns import LinkColumn, Link, DatetimeColumn
from django.utils.html import format_html
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from table.utils import Accessor
from django.utils.html import escape
from dateutil.parser import parse
from datetime import datetime
from django.utils import timezone
from registrations.tables import *
import copy

from registrations.tables import ( waiver_report_table, milestone_report_table,
	base_filter_paging as BFA,
	prog_change_report_paging as PCRPTable, ApplcantExceptionTable as AdminAET )
import pytz

class ApplcantExceptionTable(AdminAET):
	class Meta(AdminAET.Meta):
		ajax_source = reverse_lazy('sub_reviewer:app-exp')


def RA_table(program=None,status=None,pg_type=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='sub_reviewer:sub-review-application-details', 
			args=(A('id'),)
			),])


		student_id = FilterColumn( field = 'student_id', header = 'Student ID' )

		finalName = Column( field = 'full_name', header = 'Name' )

		created_on_datetime = DTColumn( field = 'created_on_datetime', 
			header = 'Applied On' )

		last_updated = DTColumn( field = 'last_updated', 
			header = 'Last Action / Update On',searchable = False )

		pg_name = Column( field='pg_name', header = 'Program Applied for' )
		
		application_status = Column( field = 'application_status', header = 'Application Status' )

		comment = CommentColumn(header = 'Super Reviewer Escalation Comments', 
			sortable = False,
			searchable = False)


		
		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('sub_reviewer:table_data',kwargs={
			'pg':program or 0,
			'st':status or 'n',
			'pg_typ': pg_type or 'n',
			})

	return SCATable


def WR_table(admit_batch=None, ajax_url=None,):
	class SCATable(waiver_report_table()):
		class Meta(waiver_report_table().Meta):
			ajax_source = reverse_lazy('sub_reviewer:waiver-report-ajax',
				kwargs={'b_id':admit_batch or 0},)
	return SCATable

def M_table(admit_batch=None, program=None,pg_type=None, ajax_url=None,):
	class SCATable(milestone_report_table()):
		class Meta(milestone_report_table().Meta):
			ajax_source = reverse_lazy('sub_reviewer:milestone-report-ajax',kwargs={'b_id':admit_batch or 0,'p_id':program or 0,'p_type': pg_type or 0,},)
	return SCATable

def PCRP_table(admit_batch=None, ajax_url=None,):
	BaseSCATable = PCRPTable()
	class SCATable(BaseSCATable):
		class Meta(BaseSCATable.Meta):
			ajax_source = reverse_lazy('sub_reviewer:prog-change-report-ajax',
				kwargs={'b_id':admit_batch or 0},)
	return SCATable