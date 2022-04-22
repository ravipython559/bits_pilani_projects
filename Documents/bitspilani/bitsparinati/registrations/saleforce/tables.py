from bits_admin.table_filter_column import *
from registrations.models import SaleForceLeadDataLog
from table import Table
from table.columns import Column, CheckboxColumn, DatetimeColumn, LinkColumn, Link
from table.utils import Accessor
from table.utils import A, mark_safe
from django.utils.html import escape

class get_applicationid_or_email( Column ):
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		data=data['records'][0]
		if 'Application_ID__c' in data.keys():
			return escape(data['Application_ID__c'])
		elif 'Application_Id__c' in data.keys():
			return escape(data['Application_Id__c'])
		else:
			return escape(data['Email'])

class responsecheck( Column ):
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		k=""
		for i in data.keys():
			if i=='error':
				k=data['error']
		text = k if k else ''
		return escape(text) 

class statuscheck( Column ):
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if data:
			data=int(data)
			if data in (200,201):
				data="Success"
			else:
				data="Failure"

		return escape(data) 

class insertupdate( Column ):
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		data=int(data)
		if data==1:
			data="Insert"
		else:
			data="Update"
		return escape(data) 


def salesforce_data_log(status=None):
	class DataLogTable(Table):

		s_id = Column( field = 'pk', header = 'ID', searchable=False)

		application_id = get_applicationid_or_email( field = 'dataset', header = 'Application ID')

		insert_update = insertupdate( field = 'is_inserted', header = 'Insert / Update', searchable=False)

		created_on = DTColumn(field = 'created_on', header = 'Created On', searchable=False)

		sent_to_sf_on = DTColumn(field = 'sent_to_sf_on', header = 'Sent to SF on', searchable=False)

		status = statuscheck( field = 'status', header = 'Status', searchable=False)

		dataset = LinkColumn(field='dataset', header='JSON', links=[
			Link(text='File',
			viewname='registrationForm:saleforce:file_download',
			args=(A('pk'),A('reference_id'),),
			),], searchable=False)

		response = responsecheck( field = 'response', header = 'Error Code' , searchable=False)

		class Meta(object):
			attrs = {'class': 'table table-bordered table-striped'}

	return DataLogTable

def specific_program_summary_data(program=None):

	class SpecificSummaryTable(Table):

		program = Column( field = 'specific_program_id', header = 'Program', searchable=True)
		admit_batch = Column( field = 'admit_batch', header = 'Admit Batch', searchable=False)
		admit_sem_cohort = Column( field = 'admit_sem_cohort', header = 'Admit Sem Cohort', searchable=False)
		application_count = Column( field = 'application_count', header = 'Application Count', searchable=False)
		full_submission_count = Column( field = 'full_submission_count', header = 'Full Submission Count', searchable=False)
		offered_count = Column( field = 'offered_count', header = 'Offered Count', searchable=False)
		admission_count = Column( field = 'admission_count', header = 'Admission Count', searchable=False)
		reject_count = Column( field = 'reject_count', header = 'Reject Count', searchable=False)
		last_updated_datetime = DTColumn( field = 'last_updated_datetime', header = 'Last Updated', searchable=False)

		class Meta(object):
			model = SpecificAdmissionSummary
			attrs = {'class': 'table table-bordered table-striped'}
			ajax = True
			pagination = True
			ajax_source = reverse_lazy('registrationForm:saleforce:specific_report_ajax',kwargs={
                'program':program or 'n'
                })

	return SpecificSummaryTable

def saleforcelogcleanuptable():

	class SaleForceLogCleanupTable(Table):

		logdel_start_datetime = DTColumn( field = 'logdel_start_datetime', header = 'Log Deletion Start Time', searchable=False)
		logdel_end_datetime = DTColumn( field = 'logdel_end_datetime', header = 'Log Deletion End Time', searchable=False)
		sf_lead_rows_deleted = Column( field = 'sf_lead_rows_deleted', header = 'Lead Data Log Count', searchable=False)
		sf_document_rows_deleted = Column( field = 'sf_document_rows_deleted', header = 'Document Data Log Count', searchable=False)
		sf_qualification_rows_deleted = Column( field = 'sf_qualification_rows_deleted', header = 'Qualification Data Log Count', searchable=False)
		sf_workexp_rows_deleted = Column( field = 'sf_workexp_rows_deleted', header = 'Work Experience Data Log Count', searchable=False)

		class Meta(object):
			model = SaleForceLogCleanup
			attrs = {'class': 'table table-bordered table-striped'}
			ajax = False
			pagination = True
			search=False

	return SaleForceLogCleanupTable	