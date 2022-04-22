from table import Table
from table.columns import Column, LinkColumn, Link,DatetimeColumn, CheckboxColumn
from master.models import *
from table.utils import Accessor
from django.utils.html import escape,format_html
from django.urls import reverse_lazy
from table.utils import A, mark_safe
import json
from django.utils import timezone

class DTColumn( DatetimeColumn ):
	''' Display Date and blank instead of None '''
	def render(self, value):
		date = Accessor(self.field).resolve(value)
		text = timezone.localtime(date).strftime("%d-%m-%Y %I:%M %p") if date else ''
		return escape(text)

class QPLinkColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if value.alternate_qp_path or value.qp_path:
			return mark_safe("""<h6><a href="/administrator/qp_path_view_details/{}/" target="_blank">View Accept or Reject Submission</a></h6>""".format(value.id))
		else:
			return mark_safe("""<h6><a href="/administrator/qp_path_view_details/{}/" target="_blank">Upload Instruction Cell QP</a></h6>""".format(value.id))

class DisabledCheckBoxColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)	
		if data:	
			return mark_safe("""<input type="checkbox"  checked="checked" onclick="return false;">""")
		else:
			return mark_safe("""<input type="checkbox" onclick="return false;">""")

class Accept_rejectColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if ((value.qp_path and value.last_submitted_datetime) or (value.alternate_qp_path and value.alternate_qp_submit_datetime)) and value.acceptance_flag == False and value.rejected_flag == False:
			return mark_safe("Pending Review")
		if ((value.qp_path and value.last_submitted_datetime) or (value.alternate_qp_path and value.alternate_qp_submit_datetime)) and value.acceptance_flag == True and value.last_download_datetime:
			return mark_safe("Accepted and Downloaded")
		if ((value.qp_path and value.last_submitted_datetime) or (value.alternate_qp_path and value.alternate_qp_submit_datetime)) and value.acceptance_flag == True and not value.last_download_datetime:
			return mark_safe("Accepted")
		if ((value.qp_path and value.last_submitted_datetime) or (value.alternate_qp_path and value.alternate_qp_submit_datetime)) and value.rejected_flag==True:
			return mark_safe("Sent for Resubmission")
		if (value.qp_path==None or value.qp_path=='') and (value.alternate_qp_path==None or value.alternate_qp_path==''):
			return mark_safe("Pending Submission")
		else:
			return mark_safe("")


class showemptyColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if data:
			return data
		else:
			return ''

class faculty_id_Column( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		return ' : '.join([x for x in value.faculty_id_cancatenate.split(' : ') if x])

def get_submission_status_table(data=None):
	class SubmissionStatusTable(Table):
		semester_name = Column(field='semester_name', header='Semester', searchable=False)
		batch_name = Column(field='batch_name', header='Batch', searchable=False)
		course = Column(field='course_info', header='Course Code and Name')
		exam_type_name = Column(field='exam_type_info', header='Exam Type', searchable=False)
		last_submitted_datetime = DTColumn(field='last_submitted_datetime', header='Submission DateTime')
		faculty_email_id = faculty_id_Column(field='faculty_id_cancatenate', header='Submissions to be Done by')
		submitted_by_faculty  = showemptyColumn(header_attrs={'style': 'height: 26px;width: 63px;'},field='submitted_by_faculty', header='QP Submitted by')
		Accept_reject = Accept_rejectColumn(field='acceptance_flag', header='Status',searchable=False,sortable=False)
		submission_locked_flag = DisabledCheckBoxColumn(field='submission_locked_flag', header='Upload Locked', searchable=False)
		view_details = QPLinkColumn(field='qp_path', header='View Details', sortable=False, searchable=False)

		class Meta:
			attrs = {'class': 'table table-bordered table-striped'}
			model = QpSubmission
			pagination = True
			search_placeholder='Search by Course Code, Course Name and Faculty email id'
			ajax = True
			ajax_source = reverse_lazy('administrator:qp_submission_status_ajax_view',kwargs={
				'data': json.dumps(data) if data else 'n',})

	return SubmissionStatusTable

def get_qp_submissions_download_table(data=None):
	class QPSubmissionsDownloadTable(Table):
		semester_name = Column(field='semester_name', header='Semester', searchable=False)
		batch_name = Column(field='batch_name', header='Batch', searchable=False)
		course = Column(field='course_info', header='Course Code and Name')
		exam_type_name = Column(field='exam_type_name', header='Exam Type', searchable=False)
		faculty_email_id = Column(field='faculty_email_id', header='Faculty Email ID')
		last_submitted_datetime = DTColumn(field='last_submitted_datetime', header='Submission DateTime', searchable=False)
		submission_locked_flag = DisabledCheckBoxColumn(field='submission_locked_flag', header='Upload Locked', searchable=False)
		last_download_datetime = DTColumn(field='last_download_datetime', header='QP Download Date Time', searchable=False)


		class Meta:
			attrs = {'class': 'table table-bordered table-striped'}
			model = QpSubmission
			pagination = True
			search_placeholder='Search by Course Code, Course Name and Faculty email id'
			ajax = True
			ajax_source = reverse_lazy('administrator:qp_submissions_download_ajax_view',kwargs={
				'data': json.dumps(data) if data else 'n',})

	return QPSubmissionsDownloadTable
