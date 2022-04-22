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
import pytz
from bits_admin.tables import (filter_paging as FP, arch_filter_paging as AFP)
from registrations.tables import ( waiver_report_table,milestone_report_table, 
	 prog_change_report_paging as PCRPTable, ApplcantExceptionTable as AdminAET ) 

class ApplcantExceptionTable(AdminAET):
	class Meta(AdminAET.Meta):
		ajax_source = reverse_lazy('business_user:app-exp')

def AFP_table(program=None, status=None, from_date=None, to_date=None, pg_type=None, admit_batch=None):
	BaseSCATable = AFP( programs = program, status = status,
	 from_date = from_date, to_date = to_date, pg_type = pg_type, admit_batch=None )
	class SCATable(BaseSCATable):
		class Meta(BaseSCATable.Meta):
			ajax_source = reverse_lazy('business_user:table_archive_data',kwargs={
			'pg': program or 0,
			'st': status or 'n',
			'to_dt': to_date or '00-00-0000',
			'fm_dt': from_date or '00-00-0000',
			'pg_typ': pg_type or 'n',
			'adm_bat': admit_batch or 'n',
			})

	return SCATable

def FP_table(program=None, status=None, from_date=None, to_date=None, pg_type=None, admit_batch=None):
	BaseSCATable = FP( programs = program, status = status,
	 from_date = from_date, to_date = to_date, pg_type = pg_type )
	class SCATable(BaseSCATable):
		
		class Meta(BaseSCATable.Meta):
			ajax_source = reverse_lazy('business_user:table_data',kwargs={
			'pg': program or 0,
			'st': status or 'n',
			'to_dt': to_date or '00-00-0000',
			'fm_dt': from_date or '00-00-0000',
			'pg_typ': pg_type or 'n',
			'adm_bat': admit_batch or 'n',
			})
	return SCATable

def WR_table(admit_batch=None,program=None, ajax_url=None,):
	class SCATable(waiver_report_table()):
		class Meta(waiver_report_table().Meta):
			ajax_source = reverse_lazy('business_user:waiver-report-ajax',
				kwargs={'b_id':admit_batch  or 0},)
	return SCATable

def M_table(admit_batch=None,program=None,pg_type=None ,ajax_url=None,):
	class SCATable(milestone_report_table()):
		class Meta(milestone_report_table().Meta):
			ajax_source = reverse_lazy('business_user:milestone-report-ajax',
			kwargs={'b_id':admit_batch  or 0 ,'p_id':program or 0, 'p_type': pg_type or 0,})
	return SCATable


def PCRP_table(admit_batch=None, ajax_url=None,):
	BaseSCATable = PCRPTable()
	class SCATable(BaseSCATable):
		class Meta(BaseSCATable.Meta):
			ajax_source = reverse_lazy('business_user:prog-change-report-ajax',
				kwargs={'b_id':admit_batch  or 0},)
	return SCATable