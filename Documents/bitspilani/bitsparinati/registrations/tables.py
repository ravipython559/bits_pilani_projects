from .models import *
from bits_admin.models import *
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
from bits_admin.tables import ApplcantExceptionTable as AdminAET
from registrations.utils.table.tables import Table as BitsTable
import pytz
from bits_admin.table_filter_column import *

class ApplcantExceptionTable(AdminAET):
	class Meta(AdminAET.Meta):
		ajax_source = reverse_lazy('reviewer:app-exp')


def base_filter_paging(programs=None,status=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''

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
			ajax_source = reverse_lazy('reviewer:table_data',kwargs={
				'pg':programs or 0,
				'st':status or 'n',
				# 'pg_typ': pg_type or 'n',
				})

	return SCATable

def filter_paging(programs=None,status=None,pg_type=None,admit_batch=None):
	''' Applicant Data List with filters for multiple role '''

	class SCATable(Table):
		''' Application Data List Table '''
		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='registrationForm:review_application_details', 
			args=(A('id'),)
			),])

		student_id = FilterColumn( field = 'student_id', header = 'Student ID' )

		admit_batch = FilterColumn( field = 'admit_batch', header = 'Admit Batch')

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
			ajax_source = reverse_lazy('reviewer:table_data',kwargs={
				'pg':programs or 0,
				'st':status or 'n',
				'pg_typ': pg_type or 'n',
				'adm_bat': admit_batch or 'n',
				})

	return SCATable


def bulk_mail_filter_paging(programs=None,location=None):
	''' Send Shortlisted / Rejected Mail List '''

	class SCATable(Table):

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'), 
			viewname='registrationForm:review_application_details', 
			args=(A('id'),)
			),])

		finalName = Column( field = 'full_name', header = 'Name' )

		created_on_datetime = DTColumn( field = 'created_on_datetime', 
			header = 'Applied On' )

		pg_name = Column( field='pg_name', header = 'Program Applied for' )
		
		application_status = Column( field = 'application_status', header = 'Application Status' )

		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('reviewer:bulk_table_data',kwargs={
				'pg':programs or 0,
				'lo':location or 0,
				})


	return SCATable

def ncl_paging( programs = None, admit_batch= None,pg_type=None,):
	''' Newly Admitted Students with filters for Reviewer '''
	
	class SCATable(Table):
		''' Newly Admitted Students Table for Reviewer '''

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
			Link(text=A('app_id'),
			attrs={'target':'_blank'}, 
			viewname='registrationForm:review_application_details', 
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
			header_attrs={'width': '15%'},
			links=[
			Link(text='View',
			viewname='reviewer:name-change-form',
			args=(A('sca_id'),)
			),],sortable = False, searchable = False)

		data_synced_with_sdms = SDMSColumn( field='dps_flag', header= 'Data Synced with SDMS?')

		class Meta(object):
			model = CandidateSelection
			ajax = True
			search_placeholder='Search by Application id or name'
			pagination = True
			ajax_source = reverse_lazy('reviewer:ncl-table-data',kwargs = {
				'pg': programs or 0,'ab':admit_batch or 0,'p_type':pg_type or 0,
				})


	return SCATable

def waiver_report_table(admit_batch=None, ajax_url=None, ):
	class WaiverReportTable(BitsTable):
		''' Fee Waiver Report Table for Reviewer '''

		employee_name = Column( field = 'employee_name', header = 'Name' )
		admit_batch = Column(field = 'adm_batch', header = 'Admit Batch')
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
			extra_model = ExceptionListOrgApplicantsArchived
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(
				'reviewer:waiver-report-ajax',
				kwargs={'b_id':admit_batch or 0}
			)
			
	return WaiverReportTable

def milestone_report_table(admit_batch=None,program=None, pg_type=None, ajax_url=None, ):
	class MilestoneTable(Table):
		''' Milestone Report Table for all user roles '''

		action = LinkColumn(header = 'Application ID',field='app_id', links=[
				Link(text=A('app_id'), 
				viewname='bits_admin:admin-application-views', 
				args=(A('pk'),)
				),])
		program = Column( field = 'program',
			header = 'Program Applied For' )
		admit_batch = Column(field ='admit_batch',header='Admit Batch')
		application_status = Column( field = 'application_status',
			header = 'Current Status' )
		profile_created_date = MilestoneDateColumn( field = 'profile_created_date', header = 'Profile Created Date' )
		pre_selected_rejected_date = MilestoneDateColumn( field = 'pre_selected_rejected_date', header = 'Pre-Selected / Rejected Date' )
		doc_sub_date = DocSubDTColumn( field = 'doc_sub_date', 
			header = 'Document Submitted Date(latest)' )
		off_rej_date = MilestoneDateColumn( field = 'off_rej_date',
			header = 'Offer/Reject Release Date' )
		fee_paym_deadline_date = ColumnMilestone( field = 'fee_paym_deadline_date',
			header = 'Fee Payment Deadline Date' )
		acc_rej_cand_date = MilestoneDateColumn( field = 'acc_rej_cand_date',
			header = 'Acceptance/Rejection by candidate Date' )
		app_fee = BitsFeeDateColumn( header = 'Application Fee Payment Date', fee_type='2' )
		adm_fee_pay_date = BitsFeeDateColumn( header = 'Admission Fee Payment Date', fee_type='1'  )
		fee_waiver = WavColumn( header = 'Fee Waiver',header_attrs={'width':'10%'}, sortable = False, searchable = False )

		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('reviewer:milestone-report-ajax',kwargs={'b_id':admit_batch or 0,'p_id':program or 0, 'p_type': pg_type or 0,})
	return MilestoneTable

def prog_change_report_paging(admit_batch=None, ajax_url=None,):
	''' Applicant List with Internal Program Transfers Table '''

	class ProgChangeReportTable(BitsTable):

		action = ExtraLinkColumn(
			StudentCandidateApplication,
			StudentCandidateApplicationArchived,
			header = 'Application ID(new ID - old ID)',
			field='app_id', 
			links=[
				Link(
					text=A('app_id'), 
					viewname='bits_admin:admin-application-views', 
					args=(A('pk'),)
				),
			],
			extra_links=[
				Link(
					text=A('app_id'), 
					viewname='bits_admin:admin-application-archive-views', 
					args=(A('pk'), A('run'))
				),
			],
		)

		created_on_datetime = DTColumn( field = 'created_on_datetime', 
			header = 'Applied On' )

		prog_changed_on = DTColumn( field = 'prog_changed_on', 
			header = 'Program Change Done On' )

		admit_batch = Column(field = 'adm_batch', header = 'Admit Batch')

		student_id = FilterColumn( field = 'student_id', header = 'Student ID' )

		old_student_id = FilterColumn( field = 'old_student_id', header = 'Old Student ID' )

		pg_name = PgColumn( field='old_prog', header = 'Program Applied for' )

		new_prog = PgColumn( field='new_prog', header = 'New Program' )

		application_status = Column( field = 'application_status', 
			header = 'Current Status' )
			
		class Meta(object):
			model = StudentCandidateApplication
			extra_model = StudentCandidateApplicationArchived
			ajax = True
			pagination = True
			ajax_source = reverse_lazy(
				'reviewer:prog-change-report-ajax',
				kwargs={'b_id':admit_batch or 0},)
			search = True

	return ProgChangeReportTable

def prog_loc_report( prog=None, loc=None ):
	''' Cluster / Specific Program Location Report '''

	class PLTable(Table):
		full_pg = Column( field = 'full_pg', header = 'Program' )
		loc_name = Column( field = 'loc_name', header = 'Location' )
		sub = Column( field = 'sub', header = 'Submitted' )
		app_fees_paid = Column( field = 'app_fees_paid', 
			header = 'Application Fees Paid' )
		adm_fees_paid = Column( field = 'adm_fees_paid', 
			header = 'Admission Fees Paid' )
		total_status_count = Column( field = 'total_status_count', 
			header = 'Total Status Count' )

		class Meta(object):
			model = StudentCandidateApplication
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('reviewer:prog-loc-report-ajax',kwargs = {
				'prog': prog or 0,
				'loc': loc or 0,
				})

	return PLTable


class StudentCourseReportTable(Table):
	''' Fee Waiver Report Table for Admin'''

	student_id = Column( field = 'student_id', header = 'Student ID' )
	name = Column( field = 'name', header = 'Name' )
	batch = FilterColumn( field = 'batch', header = 'Batch' )
	course1 = CourseColumn( field = 'courses', header = 'Course 1', sortable=False, index=0)
	course2 = CourseColumn( field = 'courses', header = 'Course 2', sortable=False, index=1)
	course3 = CourseColumn( field = 'courses', header = 'Course 3', sortable=False, index=2)
	course4 = CourseColumn( field = 'courses', header = 'Course 4', sortable=False, index=3)
	

	class Meta(object):
		model = CandidateSelection
		ajax = True
		pagination = True
		ajax_source = reverse_lazy('bits_admin:student-course-report-ajax',)

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
			ajax_source = reverse_lazy('reviewer:view-elective-selections-ajax',
				kwargs={'pg':programs or 0,}
				)

	return SCATable

def pgm_adm_report_paging(program_type=None, program=None, admit_batch=None ,ajax_url=None):

	class PARTable(BitsTable):
		
		program = Column( field = 'pgm', header = 'Program', header_attrs={'width': '50%'})

		batch = NumberColumn( field = 'btc', header = 'Batch', header_attrs={'width': '25%'})

		admission_count = NumberColumn( field = 'adm_count', header = 'Admission Count', sortable = False, header_attrs={'width': '25%'})
			
		class Meta(object):
				model = CandidateSelection
				extra_model = CandidateSelectionArchived
				ajax = True
				pagination = True
				search = False
				ajax_source = reverse_lazy(ajax_url,kwargs={
				'pg':program or 0,
				'pg_type':program_type or 'n',
				'adm_btc':admit_batch or 'n'

				})
	return PARTable

