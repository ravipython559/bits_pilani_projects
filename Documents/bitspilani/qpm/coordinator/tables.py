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

class showemptyColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if data:
			return data
		else:
			return ''

class QPLinkColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if data:
			return mark_safe("""<h6><a href="/coordinator/doc-download-view/{}/{}" target="_blank">QP Uploaded</a></h6>""".format(value.id,'qp_path'))
		else:
			return ' '

class AlternateQPLinkColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if data:
			return mark_safe("""<h6><a href="/coordinator/doc-download-view/{}/{}" target="_blank">QP Updated by Instruction Cell</a></h6>""".format(value.id,'alternate_qp_path'))
		else:
			return ' '

class StatusColumn( Column ):
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


def get_coord_submission_status_table(data=None):
	class CoordSubmissionStatusTable(Table):
		semester_name = Column(field='semester_name', header='Semester', searchable=False)
		exam_type_name = Column(field='exam_type_info', header='Exam Type', searchable=False)
		exam_slot = Column(field='exam_slot_name', header='Exam Slot', searchable=False)
		batch_name = Column(field='batch_name', header='Batch', searchable=False)
		course = Column(field='course_info', header='Course Code and Name')
		submitted_by_faculty  = showemptyColumn(header_attrs={'style': 'height: 26px;width: 63px;'},field='submitted_by_faculty', header='QP Submitted by')
		last_submitted_datetime = DTColumn(field='last_submitted_datetime', header='Submitted Date')
		qp_link = QPLinkColumn(field='qp_path', header='Faculty QP File', sortable=False, searchable=False)
		status = StatusColumn(field='acceptance_flag', header='Status',searchable=False,sortable=False)
		instruction_cell_file = AlternateQPLinkColumn(field='alternate_qp_path', header='Instruction Cell File', sortable=False, searchable=False)

		class Meta:
			attrs = {'class': 'table table-bordered table-striped'}
			model = QpSubmission
			pagination = True
			search_placeholder='Search by Course code, Course name and QP Submitted by'
			ajax = True
			ajax_source = reverse_lazy('coordinator:coord_qp_submission_status_ajax_view',kwargs={
				'data': json.dumps(data) if data else 'n',})

	return CoordSubmissionStatusTable
