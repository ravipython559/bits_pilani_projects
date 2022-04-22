from registrations.models import *
from bits_rest.models import ZestEmiTransaction, InBoundCall, OutBoundCall,EzcredApplication, PropelldApplication
from table import Table
from table.utils import A, mark_safe
from table.columns import Column
from table.columns import LinkColumn, Link, DatetimeColumn
from django.utils.html import format_html
from django.core.urlresolvers import reverse_lazy
from django.utils.html import escape
from table.utils import Accessor
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from dateutil.parser import parse
from datetime import datetime
from django.utils import timezone
from registrations.utils.table.tables import Table as BitsTable
import pytz
from .models import *
from .table_filter_column import *


def filter_paging( programs = None, status = None, from_date = None, to_date = None, pg_type = None, admit_batch=None ):
	''' Applicant Data View with filters for Admin '''

	class SCATable(Table):
		''' Application Data View Table '''

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='bits_admin:admin-application-views', 
			args=(A('id'),)
			),])

		student_id = FilterColumn( field = 'student_id', header = 'Student ID' )

		admit_batch = FilterColumn( field = 'admit_batch', header = 'Admit Batch', 
			header_attrs={'width':'8%'} )

		finalName = Column( field = 'full_name', header = 'Name', )

		created_on_datetime = DTColumn( field = 'created_on_datetime', 
			header = 'Applied On' )
		
		last_updated = DTColumn( field = 'last_updated', 
			header = 'Last Action / Update On',searchable = False )

		current_location = Column( field = 'c_l', header = 'Location' )

		pg_name = Column( field='pg_name', header = 'Program Applied for' )

		login_email = Column( field='email', header = 'Email Id' )
		
		application_status = Column( field = 'application_status', 
			header = 'Current Status' )
		waivers = WavColumn( header = 'Waivers',header_attrs={'width':'10%'}, sortable = False, searchable = False )
		
		
		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			search_placeholder='Search by Application id, name, email, location or status'
			ajax_source = reverse_lazy('bits_admin:table_data',kwargs = {
				'pg': programs or 0,
				'st': status or 'n',
				'to_dt': to_date or '00-00-0000',
				'fm_dt': from_date or '00-00-0000',
				'pg_typ': pg_type or 'n',
				'adm_bat': admit_batch or 'n',
				})


	return SCATable


def usr_filter_paging(from_date = None, to_date = None):
	''' User Data View with filters for Admin '''

	class UserTable(Table):
		''' User Data View Table '''

		email = Column( field='email', header = 'Email Id' )

		date_joined = DTColumn( field = 'date_joined', 
			header = 'Created On' )

		pg_name = FilterColumn( field='pg_name', header = 'Program Applied for')

		waivers = WaiverColumn( header = 'Waivers',header_attrs={'width':'10%'}, sortable = False, searchable = False )

		last_login = DTColumn( field = 'last_login', 
			header = 'Last Logged On' )

		last_mail_senton = DTColumn( field = 'last_mail_senton', 
			header = 'Last Follow Up Mail Sent On' )

		mails_count = Column( field = 'mails_count', 
			header = 'Mails Sent Count' )

		app_fee_mail_sent = DTColumn( field = 'app_fee_mail_sent', 
			header = 'Last Followup Application Fee Mail Sent On' )

		app_fee_mail_count = Column( field = 'app_fee_mail_count', 
			header = 'Application Fee Mails Sent Count' )

		program_registered_for = Column(field='program_registered_for',
									header='Program Registered for')

		utm_source_first = Column(field='utm_source_first',
									header='UTM Source First')

		utm_medium_first = Column(field='utm_medium_first',
									header='UTM Medium First')

		utm_campaign_first = Column(field='utm_campaign_first',
			   header='UTM Campaign First')

		utm_source_last = Column(field='utm_source_last',
			   header='UTM Source Last')

		utm_medium_last = Column(field='utm_medium_last',
			   header='UTM Medium Last')

		utm_campaign_last = Column(field='utm_campaign_last',
			   header='UTM Campaign Last')


		class Meta(object):
			model = get_user_model()
			ajax = True
			search_placeholder='Search by email id'
			pagination = True
			ajax_source = reverse_lazy('bits_admin:usr_table_data',
				kwargs = {
				'to_dt': to_date or '00-00-0000',
				'fm_dt': from_date or '00-00-0000',
				})

	return UserTable


def usr_payment_filter_paging(from_date = None, to_date = None, bank = None ):
	''' Payment Data View with filters for Admin '''

	class SCATable(Table):
		''' Payment Data View Table '''

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='bits_admin:admin-application-views', 
			args=(A('id'),)
			),])

		finalName = Column( field = 'full_name', header = 'Name' )

		pg_name = Column( field='full_prog', header = 'Program Applied for' )

		created_on_datetime = DTColumn( field = 'created_on_datetime', 
			header = 'Applied On', searchable=False )

		payment_date = DTColumn( field = 'payment_date', 
			header = 'Payment Date', searchable=False )

		payment_amount = FilterColumn( field='payment_amount',
			header = 'Payment Amount', searchable=False )

		payment_bank = PaymentBankColumn( field='payment_bank',
			header = 'Payment Bank' )

		transaction_id = FilterColumn( field='transaction_id',
			header = 'Transaction ID', searchable=False )


		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			search_placeholder='Search by Application ID or Applicant Name'
			ajax_source = reverse_lazy('bits_admin:pay_app_table_data',
				kwargs = {
				'to_dt': to_date or '00-00-0000',
				'fm_dt': from_date or '00-00-0000',
				'bank': bank or 'n',
				})

	return SCATable



def ncl_paging( programs = None, admit_batch= None,pg_type=None,):
	''' Newly Admitted Students with filters for Admin '''

	class SCATable(Table):
		''' Newly Admitted Students Table for Admin '''

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'),
			attrs={'target':'_blank'}, 
			viewname='bits_admin:admin-application-views', 
			args=(A('sca_id'),)
			),])		

		student_id = Column( field = 'student_id', header = 'Student ID' )

		finalName = Column( field = 'finalName', header = 'Name' )

		applied_on = DTColumn( field = 'applied_on', 
			header = 'Applied On' )

		pg_name = Column( field='pg_name', header = 'Program Applied for' )

		admit_batch = Column(field = 'admit_batch',header = 'Admit Batch')

		verified_student_name = FilterColumn( field='verified_student_name', header = 'BITS Verified Name' )
		
		link = LinkColumn(
			header = 'View Details for Verification' ,
			header_attrs={'width': '16%'},
			links=[
			Link(text='View',
			viewname='bits_admin:nc-form',
			args=(A('sca_id'),)
			),], sortable = False, searchable = False )

		data_synced_with_sdms = SDMSColumn( field='dps_flag', header= 'Data Synced with SDMS?')
		
		
		class Meta(object):
			model = CandidateSelection
			ajax = True
			search_placeholder='Search by Application id or name'
			pagination = True
			ajax_source = reverse_lazy('bits_admin:ncl-tab-data',kwargs = {
				'pg': programs or 0,'ab':admit_batch or 0,'p_type':pg_type or 0,
				})

	return SCATable



class WaiverReportTable(Table):
	''' Fee Waiver Report Table for Admin'''

	employee_name = Column( field = 'employee_name', header = 'Name' )
	employee_email = Column( field = 'employee_email', header = 'Email ID' )
	exception_type = Column( field = 'emp_type', header = 'Fee Waiver Type' )

	org = Column( field = 'org', header = 'Organization')
	program = Column( field = 'program', header = 'Program')
	created_on_datetime = DTColumn( field = 'cod',
		header = 'Created On Datetime', 
		searchable = False )
	application_id = FilterColumn( field = 'app_id',
		header = 'Application ID')
	student_id = FilterColumn( field = 'student_id',
		header = 'Student ID')
	application_status = FilterColumn( field = 'app_status',
		header = 'Current Status')

	class Meta(object):
		model = ExceptionListOrgApplicants
		ajax = True
		pagination = True
		ajax_source = reverse_lazy('bits_admin:waiver-report-ajax',)




def mail_logs(from_date = None, to_date = None ):
	''' Follow Up Mail Logs with filters for Admin '''

	class FollowupMailTable(Table):
		''' Follow Up Mail Logs Table '''

		run_id = Column( field = 'run', header = 'Run ID' )

		mail_type = Column( field = 'mail_type', header = 'Mail Type' )

		mail_sent_time = DTColumn( field = 'mail_sent_time', header = 'Mail Sent On',)

		no_of_mails_sent = Column( field='no_of_mails_sent', header = 'No of Mails Sent',)
		
		class Meta(object):
			model = FollowUpMailLog
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('bits_admin:followup-mail-logs-ajax',kwargs = {
				'to_dt': to_date or '00-00-0000',
				'fm_dt': from_date or '00-00-0000',
				})
			search = False

	return FollowupMailTable


class ApplcantExceptionTable(Table):
	''' Applicant List with Internal Program Transfers Table '''

	class FilterColumn( Column ):
		def render(self, value):
			data = Accessor(self.field).resolve(value)
			return escape(data if data else '')

	app_email = Column( field = 'applicant_email', header = 'Application Email ID' )
	pg_app = Column( field = 'pg_app', header = 'Program Applied For' )
	pg_adm = Column( field = 'pg_adm', header = 'Program Admitted To' )
	stud_id = FilterColumn( field = 'stud_id', header = 'Student ID' )
	app_id = Column( field = 'app_id', header = 'Application ID' )
	app_on = DTColumn( field = 'app_on', header = 'Applied On',)
	cur_status = Column( field='cur_status', header = 'Current Status',)
	
	class Meta(object):
		model = ApplicantExceptions
		pagination = True
		ajax_source = reverse_lazy('bits_admin_payment:app-exp')


def arch_filter_paging( programs = None, status = None, from_date = None, to_date = None, pg_type = None, admit_batch=None):
	''' Applicant Data View - Archived Applications with filters in Admin '''

	class SCATable(Table):
		''' Applicant Data View - Archived Applications Table '''
		
		run = Column( field = 'run', header = 'Run' )
		student_id = FilterColumn(field='student_id', header = 'STUDENT ID')

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='bits_admin:admin-application-archive-views', 
			args=[A('pk'), A('run')],
			),])

		finalName = Column( field = 'full_name', header = 'Name' )

		admit_batch = FilterColumn( field = 'admit_batch', header = 'Admit Batch' )

		created_on_datetime = DTColumn( field = 'created_on_datetime', 
			header = 'Applied On', searchable = False  )

		current_location = Column( field = 'current_location', header = 'Location' )

		pg_name = Column( field='pg_app', header = 'Program Applied for')

		email = Column( field='login_email', header = 'Email Id' )
		
		application_status = Column( field = 'application_status', 
			header = 'Current Status' )

		
		class Meta(object):
			model = StudentCandidateApplicationArchived
			ajax = True
			pagination = True
			search_placeholder='Search by Application id, name, email, location or status'
			ajax_source = reverse_lazy('bits_admin:table_archive_data',kwargs = {
				'pg': programs or 0,
				'st': status or 'n',
				'to_dt': to_date or '00-00-0000',
				'fm_dt': from_date or '00-00-0000',
				'pg_typ': pg_type or 'n',
				'adm_bat': admit_batch or 'n',
				})


	return SCATable


def def_doc_paging(programs=None, status=None, admit_batch=None, ajax_url=None, action_url=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''
		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), viewname=action_url, args=(A('id'),)),])

		student_id = FilterColumn( field = 'student_id', header = 'Student ID' )

		admit_batch = FilterColumn( field = 'admit_batch', header = 'Admit Batch', 
			header_attrs={'width':'8%'} )

		finalName = Column( field = 'full_name', header = 'Name' )

		last_updated = DTColumn( field = 'last_updated', 
			header = 'Last Action / Update On',searchable = False )

		current_location = Column( field = 'location', header = 'Location' )

		pg_name = Column( field='pg_name', header = 'Program Applied for', header_attrs={'width':'10%'})
		
		missing_docs = MissingColumn( field='email_id', header = 'Missing Document Name',header_attrs={'width':'20%'})
		
		application_status = Column( field = 'application_status', header = 'Application Status' )

		
		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url, kwargs={
				'pg':programs or 0,
				'st':status or 'n',
				'adm_bat': admit_batch or 'n',
				})

	return SCATable

def elective_selections_paging(programs=None,):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''

		student_id = Column( field = 'stud_id', header = 'Student ID')

		full_name = Column( field = 'full_name', header = 'Name')

		pg_name = Column( field='pg_name', header = 'Program Applied for')

		c_slot = Column( field='c_slot', header = 'Elective Course Slot ID')

		c_id = Column( field='c_id', header = 'Elective Course ID')

		c_unit = Column( field='c_unit', header = 'Course Units')

		c_name = Column( field='c_name', header = 'Elective Course Name')

		class Meta(object):
			model = CandidateSelection
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('bits_admin_payment:view-elective-selections-ajax',
				kwargs={'pg':programs or 0,}
				)

	return SCATable


def emi_report_paging(programs=None, admit_batch=None, status=None,pg_type=None, ajax_url=None, action_url=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(BitsTable):
		''' Application Data List Table '''
		
		action = ExtraLinkColumn(
			ZestEmiTransaction,
			ZestEmiTransactionArchived,
			header = 'Application ID(new ID - old ID)',
			field='app_id', 
			links=[
				Link(
					text=A('app_id'), 
					viewname='bits_admin:admin-application-views', 
					args=(A('sca_id'),)
				),
			],
			extra_links=[
				Link(
					text=A('app_id'), 
					viewname='bits_admin:admin-application-archive-views', 
					args=(A('sca_id'), A('run'))
				),
			],
		)

		admit_batch = FilterColumn( field = 'admit_batch', header = 'Admit Batch', 
			header_attrs={'width':'8%'} )

		student_id = FilterColumn( field='student_id', header='Student ID' )

		full_ame = Column( field='full_name', header='Name' )

		pg_name = Column( field='pg_name', header='Program Applied for', header_attrs={'width':'10%'})
		
		loan_applied_on = DTColumn( field='requested_on', header='Loan Applied On', searchable=False)

		loan_approve_reject = DTColumn( field='approved_or_rejected_on', header='Loan Approval / Rejection Date', searchable=False)

		zest_id = FilterColumn( field='order_id', header='Zest Order ID', header_attrs={'width':'10%'})
		
		loan_status = ZestStatusColumn( field='status', header='Current Loan Status' )
		
		application_status = Column( field='app_status', header='Application Center Status' )
		
		class Meta(object):
			model = ZestEmiTransaction
			extra_model = ZestEmiTransactionArchived
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url,kwargs={
				'pg':programs or 0,
				'b_id': admit_batch or 0,
				'p_type': pg_type or 0,
				'st':status or 'n',
				})

	return SCATable


def def_doc_paging_for_sub_view(programs=None, status=None, admit_batch=None, ajax_url=None, action_url=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''
		action = LinkColumn(header='Application ID', field='app_id', links=[
			Link(text=A('app_id'), viewname=action_url, args=(A('id'),)), ])

		student_id = FilterColumn(field='student_id', header='Student ID')

		admit_batch = FilterColumn(field='admit_batch', header='Admit Batch',
								   header_attrs={'width': '8%'})

		finalName = Column(field='full_name', header='Name')

		last_updated = DTColumn(field='last_updated',
								header='Last Action / Update On', searchable=False)

		current_location = Column(field='location', header='Location')

		pg_name = Column(field='pg_name', header='Program Applied for', header_attrs={'width': '10%'})

		missing_docs = MissingColumnForSubView(field='missing', header='Missing Document Name', header_attrs={'width': '20%'})

		application_status = Column(field='application_status', header='Application Status')

		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url, kwargs={
				'pg': programs or 0,
				'st': status or 'n',
				'adm_bat': admit_batch or 'n',
			})

	return SCATable

doc_sub_paging = lambda *args, **kwargs: def_doc_paging_for_sub_view(*args, **kwargs)

def pre_sel_paging(programs=None, location=None, ajax_url=None, action_url=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''
		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), viewname=action_url, args=(A('id'),)),])

		full_name = Column( field = 'full_name', header = 'Name' )

		login_email = Column( field='email', header = 'Email Id' )

		current_location = Column( field = 'c_l', header = 'Location' )

		applied_on = MilestoneDateColumn (field = 'created_on_datetime', 
			header = 'Applied On')

		last_updated = MilestoneDateColumn( field = 'last_updated', 
			header = 'Last Action On',searchable = False )

		pg_name = Column( field='pg_name', header = 'Program Applied for', header_attrs={'width':'10%'})
		
		application_status = Column( field = 'application_status', header = 'Application Status' )

		pre_selected_rejected_date = MilestoneDateColumn (field = 'pre_selected_rejected_on_datetime', 
			header = 'Pre Selected / Rejected On')
		
		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			search_placeholder='Search by Application id, name, email, location or status'
			ajax_source = reverse_lazy(ajax_url, kwargs={
				'pg':programs or 0,
				'loc':location or 0,
				})

	return SCATable

class GroupConcatColumn(Column):
	def render(self, obj):
		text = Accessor(self.field).resolve(obj)
		if text:
			return format_html(text)
		else:
			escape('')

def inbound_call_log_paging(to_date=None, from_date=None):
	class InboundTable(Table):
		agent = Column(header = 'Agent',field = 'agent_id')
		phone = GroupConcatColumn(header = 'Phone', field = 'phone')
		call_date = DTColumn(header = 'Call Date', field = 'called_on')
		# time_slot = Column(header = 'Time Slot', field = '')
		customer_name = Column(header = 'Customer Name', field = 'customer_name' )
		email = Column(header = 'Email ID', field = 'cust_email')
		program_interested = GroupConcatColumn(header = 'Program Interested', field = 'program_interested')
		query = GroupConcatColumn(header = 'Query', field = 'query')
		voc = GroupConcatColumn(header = 'VOC', field = 'voc')
		application = GroupConcatColumn(header = 'Application', field = 'app')

		class Meta:
			model = InBoundCall
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('bits_admin:inbound-ajax',kwargs={
					'to_dt' : to_date or '00-00-0000',
					'fm_dt' : from_date or '00-00-0000',
					})
			
	return InboundTable

def outbound_call_log_paging(to_date=None, from_date=None):
	class OutBoundTable(Table):
		agent = Column(header = 'Agent',field = 'agent_id')
		phone = GroupConcatColumn(header = 'Phone', field = 'phone')
		call_date = DTColumn(header = 'Call Date', field = 'called_on')
		disposition = Column(header = 'Disposition', field = 'desposition')
		customer_name = Column(header = 'Customer Name', field = 'customer_name' )
		email = Column(header = 'Email ID', field = 'cust_email')
		program_interested = GroupConcatColumn(header = 'Program Interested', field = 'program_interested')
		query = GroupConcatColumn(header = 'Query', field = 'query')
		voc = GroupConcatColumn(header = 'VOC', field = 'voc')
		application = GroupConcatColumn(header = 'Application', field = 'app')

		class Meta:
			model = OutBoundCall
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('bits_admin:outbound-ajax',kwargs={
					'to_dt' : to_date or '00-00-0000',
					'fm_dt' : from_date or '00-00-0000',
					})
	return OutBoundTable


def eduv_report_paging(programs=None, status=None,admit_batch=None,pg_type=None, ajax_url=None, action_url=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(BitsTable):
		''' Application Data List Table '''
		
		action = ExtraLinkColumn(
			EduvanzApplication,
			EduvanzApplicationArchived,
			header = 'Application ID(new ID - old ID)',
			field='app_id', 
			links=[
				Link(
					text=A('app_id'), 
					viewname='bits_admin:admin-application-views', 
					args=(A('sca_id'),)
				),
			],
			extra_links=[
				Link(
					text=A('app_id'), 
					viewname='bits_admin:admin-application-archive-views', 
					args=(A('sca_id'), A('run'))
				),
			],
		)

		admit_batch = FilterColumn( field = 'admit_batch', header = 'Admit Batch', 
			header_attrs={'width':'8%'} )

		student_id = FilterColumn( field='student_id', header='Student ID' )

		lead_id = Column( field='lead_id', header='Eduvanz Lead ID' )

		full_ame = Column( field='full_name', header='Name' )

		pg_name = Column( field='pg_name', header='Program Applied for', header_attrs={'width':'10%'})
		
		loan_applied_on = DTColumn( field='created_on', header='Loan Applied On', searchable=False)

		approved_or_rejected = DTColumn( field='approved_or_rejected_on', header='Loan Approval / Rejection Date', searchable=False)
		
		last_updatedd= DTColumn( field='updated_on', header='Last Status Update Date', searchable=False)

		eduvanz_id = FilterColumn( field='order_id', header='Eduvanz Order ID', header_attrs={'width':'10%'})
		

		
		loan_status = EduvStatusColumn( field='status_code', header='Current Loan Status' )
		
		application_status = Column( field='app_status', header='Application Center Status' )
		
		class Meta(object):
			model = EduvanzApplication
			extra_model = EduvanzApplicationArchived
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url,kwargs={
				'pg':programs or 0,
				'st':status or 'n',
				'b_id': admit_batch or 0,
				'p_type': pg_type or 0,
				})

	return SCATable

def ezcred_report_paging(programs=None, admit_batch=None, status=None,pg_type=None,ajax_url=None, action_url=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''
		
		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), viewname=action_url, args=(A('sca_id'),)),])

		admit_batch = FilterColumn( field = 'adm_batch', header = 'Admit Batch', 
			header_attrs={'width':'8%'} )

		student_id = FilterColumn( field='stud_id', header='Student ID' )

		full_name = Column( field='full_name', header='Name' )

		pg_name = Column( field='pg_full', header='Program Applied for', header_attrs={'width':'10%'})
		
		loan_applied_on = DTColumn( field='created_on', header='Loan Applied On', searchable=False)

		ezcred_id = FilterColumn( field='order_id', header='Ezcred Order ID', header_attrs={'width':'10%'})
		
		loan_status = EduvStatusColumn( field='status', header='Current Loan Status' )
		
		application_status = Column( field='app_status', header='Application Center Status' )
		
		class Meta(object):
			model = EzcredApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(ajax_url,kwargs={
				'pg':programs or 0,
				'b_id': admit_batch or 0,
				'p_type': pg_type or 0,
				'st':status or 'n',
				})

	return SCATable



def propelld_report_paging(programs=None, admit_batch=None, status=None,pg_type=None,ajax_url=None, action_url=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''
		
		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), viewname=action_url, args=(A('sca_id'),)),])

		admit_batch = FilterColumn( field = 'adm_batch', header = 'Admit Batch', 
			header_attrs={'width':'8%'} )

		student_id = FilterColumn( field='stud_id', header='Student ID' )

		full_name = Column( field='fullname', header='Name' )

		pg_name = Column( field='pg_full', header='Program Applied for', header_attrs={'width':'10%'})
		
		loan_applied_on = DTColumn( field='created_on', header='Loan Applied On', searchable=False)
		last_updte = DTColumn( field='updated_on', header='Last Status Update Date', searchable=False)
		loan_disbur_date = DTColumn( field='disbursement_date', header='Loan Disbursement Date', searchable=False)

		propelld_id = FilterColumn( field='quote_id', header='Propelld Quote ID', header_attrs={'width':'10%'})
		
		loan_status = EduvStatusColumn( field='status', header='Current Loan Status' )
		
		application_status = Column( field='app_status', header='Application Center Status' )

		utr_num = Column( field='utr_number', header='UTR Number' )

		
		class Meta(object):
			model = PropelldApplication
			pagination = True
			ajax = True
			ajax_source = reverse_lazy(ajax_url,kwargs={
				'pg':programs or 0,
				'b_id': admit_batch or 0,
				'p_type': pg_type or 0,
				'st':status or 'n',
				})

	return SCATable