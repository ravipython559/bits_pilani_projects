from master.models import *
from table import Table
from table.columns import Column, CheckboxColumn, DatetimeColumn, LinkColumn, Link
from table.utils import A
from table.utils import Accessor
from table.utils import A, mark_safe
from django.urls import reverse_lazy
from django.conf import settings
from django.utils import timezone
from django.utils.html import escape
import json

class CourseCodeNameColumn( Column ):
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		return value.course_code+' - '+value.course_name

class FilterColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)			
		return escape(data if data else '')


class DisabledCheckBoxColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)	
		if data:	
			return mark_safe("""<input type="checkbox"  checked="checked" onclick="return false;">""")
		else:
			return mark_safe("""<input type="checkbox" onclick="return false;">""")

class QPLinkColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)	
		if data:	
			return mark_safe("""<h6><a href="/faculty/doc-download-view/{}/{}" target="_blank">QP Uploaded</a></h6>""".format(value.id,'qp_path'))
		else:
			return ' '

class AlternateQPLinkColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)	
		if data:	
			return mark_safe("""<h6><a href="/faculty/doc-download-view/{}/{}" target="_blank">QP File Instruction</a></h6>""".format(value.id,'alternate_qp_path'))
		else:
			return ' '


class DTColumn( DatetimeColumn ):
	''' Display Date and blank instead of None '''
	def render(self, value):
		date = Accessor(self.field).resolve(value)
		text = timezone.localtime(date).strftime("%d-%m-%Y %I:%M %p") if date else ''
		return escape(text)

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

def faculty_Qp_submissions(data=None):
	class facSubmissionStatusTable(Table):
		semester = Column(field='semester', header='Semester')
		batch = Column(field='batch', header='Batch',searchable=False, sortable=False)
		course_code_name = CourseCodeNameColumn(field='course_code', header='Course Code and  Course Name')
		exam_type_name = Column(field='exam_type_info', header='Exam Type', searchable=False, sortable=False)
		exam_slot = Column(field='exam_slot', header='Exam Slot', searchable=False, sortable=False)
		Accept_reject = Accept_rejectColumn(field='acceptance_flag', header='Status',searchable=False,sortable=False)
		qp_submitted = showemptyColumn(field='submitted_by_faculty', header='QP Submitted by', sortable=False, searchable=False,)
		qp_link = QPLinkColumn(field='qp_path', header='QP Link', sortable=False, searchable=False)
		submission_date_time = DTColumn(field='last_submitted_datetime', header='Submission Date and Time',searchable=False)
		upload_locked = DisabledCheckBoxColumn(field='submission_locked_flag', header='Upload Locked', sortable=False, searchable=False)
		qp_upload_download = DTColumn(field='last_download_datetime', header='QP Download Date and Time',searchable=False)
		alternate_qp_link = AlternateQPLinkColumn(field='alternate_qp_path', header='Instruction Cell QP File', sortable=False, searchable=False)
		alternate_submission_date_time = DTColumn(field='alternate_qp_submit_datetime', header='Instruction File Submitted Date & Time',sortable=False,searchable=False)


		class Meta:
			attrs = {'class': 'table table-bordered table-striped'}
			model = QpSubmission
			pagination = True
			ajax = True
			search = False
			ajax_source = reverse_lazy('faculty:fac_qp_submission_status_ajax_view',kwargs={
				'data': json.dumps(data) if data else 'n',})

	return facSubmissionStatusTable
