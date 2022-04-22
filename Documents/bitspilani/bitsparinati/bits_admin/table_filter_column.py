from registrations.models import *
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
from django.db.models import *
from dateutil.parser import parse
from datetime import datetime
from django.utils import timezone
import pytz
from .models import *
from bits_rest import zest_statuses as ZS
from bits_rest.models import EduvanzApplication

class FilterColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)			
		return escape(data if data else '')


class ZestStatusColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)			
		return escape(dict(ZS.ZEST_DISPLAY_STATUS_CHOICES).get(data, '-'))


class StudIDFilterColumn( Column ):
	''' Query and Display Student ID in archive view and blank instead of None '''
	def render(self, value):
		try:
			stud_id = CandidateSelectionArchived.objects.get(
				application=value.student_application_id,
				run=value.run,
			).student_id
		except CandidateSelectionArchived.DoesNotExist:
			stud_id = ''
		return escape(stud_id or '')

class DTColumn( DatetimeColumn ):
	''' Display DateTime input and blank instead of None '''
	def render(self, value):
		datetime = Accessor(self.field).resolve(value)
		text = timezone.localtime(datetime).strftime("%d-%m-%Y %I:%M %p") if datetime else ''
		return escape(text)

class SDMSColumn( Column ):
	''' Display Yes or No in the place of True oe False '''
	def render(self, value):
		dps_flag = Accessor(self.field).resolve(value)
		if dps_flag == True:
			return escape('Yes')
		else:
			return escape('No')

class MilestoneDateColumn( DatetimeColumn ):
	''' Display Milestone Date and blank instead of None '''
	def render(self, value):
		date = Accessor(self.field).resolve(value)
		text = timezone.localtime(date).strftime("%d/%m/%Y") if date else '-'
		return escape(text)

class ColumnMilestone( DatetimeColumn ):
	''' Display Milestone Date and blank instead of None '''
	def render(self, value):
		date = Accessor(self.field).resolve(value)
		if not date:
			try:
				pld = ProgramLocationDetails.objects.get(program=value.program,
					location=value.current_location)
				text = timezone.localtime(pld.fee_payment_deadline_date).strftime("%d/%m/%Y ")
			except ProgramLocationDetails.DoesNotExist:
				text = '-'
		else:
			text = timezone.localtime(date).strftime("%d/%m/%Y ")

		return escape(text)

class DocSubDTColumn( Column ):
	''' Display Doc submitted DateTime and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)

		if isinstance(data, datetime):
			return escape(data.strftime("%d/%m/%Y ") if data else '-')
		return escape(parse(data).strftime('%d/%m/%Y ') if data else '-')

class BaseBitsFeeDateColumn( Column ):
	''' set a particular fee type adm or app '''
	def __init__(self, fee_type=None, *args, **kwargs):
		self.fee_type = fee_type
		super(BaseBitsFeeDateColumn,self).__init__(*args, **kwargs)	
		
class BitsFeeDateColumn( BaseBitsFeeDateColumn ):
	''' Query and Display respective payment datetime for milestone report in admin and reviewer and blank instead of None. '''
	def render(self, value):
		try:
			ap = ApplicationPayment.objects.get(application = value, fee_type=self.fee_type)
		except ApplicationPayment.DoesNotExist:
			return escape('-')
		try:
			return escape(timezone.localtime(ap.payment_date).strftime("%d/%m/%Y") if ap.payment_date else '-')
		except :
			return escape(ap.payment_date.strftime("%d/%m/%Y") if ap.payment_date else '-')


class ProgramColumn(Column):
	''' Query and Display program code in applicant archive view '''
	def render(self, value):
		pg = Accessor(self.field).resolve(value)
		try:
			program=str(Program.objects.get(program_code=pg))
		except Program.DoesNotExist:
			program = pg
		return escape(program)

class PgColumn(Column):
	''' Display pg string in uppper case '''
	def render(self, value):
		tmp=Accessor(self.field).resolve(value)
		return escape(tmp.upper())



class CommentColumn(Column):
	''' Display reviewer and super-rev comments as link in applicant list reviewer'''
	def render(self, value):
		if not value.su_comment and not value.rev_comment: return ''
		
		return format_html(
			"""
			<a id='esc_comm'  
			onclick='popD("Escalation Comments: {0} <br> &nbsp&nbsp Super Reviewer Comments: {1}");'
			>Comment</a>
			""".format(value.rev_comment, value.su_comment)
			)
class WavColumn(Column):
	''' Query and Display Fee Waiver type and blank instead of None in admin Milestone reports and Applicant Data view '''
	def render(self, value):
		eloa=ExceptionListOrgApplicants.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=value.login_email.email,program=value.program
			).values_list('exception_type',flat=True)
		return format_html(' and '.join(map(lambda x:dict(FEE_TYPE_CHOICE)[x].capitalize(),eloa)))


class WaiverColumn(Column):
	''' Query and Display Fee Waiver type and blank instead of None in admin user data view '''
	def render(self, value):
		eloa=ExceptionListOrgApplicants.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=value.email,program__program_code=value.pg_code
			).values_list('exception_type',flat=True)
		return format_html(' and '.join(map(lambda x:dict(FEE_TYPE_CHOICE)[x].capitalize(),eloa)))

class DeffColumn(Column):
	''' 
	Query and display missing documents and blank instead of None in admin deffered doc ddata view
	'''
	def render(self, value):
		adl = ApplicationDocument.objects.filter(application=value).values_list('document__document_name', flat=True)
		pdml = ProgramDocumentMap.objects.filter(
			program = value.program, deffered_submission_flag=True).values_list('document_type__document_name', flat=True)
		doc = list(set(pdml) - set(adl))
		return escape(', '.join(doc))

class MissingColumn(Column):
	''' Display missing documents'''

	def get_deff_offer_status(self, email):
		ad = ApplicationDocument.objects.filter(application__login_email__email=email)
		list_docs_submitted = []
		for each_ad in ad:
			list_docs_submitted.append(each_ad.document.id)
		sca = StudentCandidateApplication.objects.get(login_email__email=email)
		pdm = ProgramDocumentMap.objects.filter(program__program_code=sca.student_application_id[1:5])
		deff_docs_ids = []
		for each_pdm in pdm:
			if each_pdm.deffered_submission_flag == True:
				deff_docs_ids.append(each_pdm.document_type.id)

		if len(deff_docs_ids) == 0:
			return []

		def_docs_not_submitted = []
		def_docs_submitted = []
		for each in deff_docs_ids:
			if each not in list_docs_submitted:
				def_docs_not_submitted.append(each)
			else:
				def_docs_submitted.append(each)

		# submitted deff doc but got deferred for later submission or rejected
		def_doc_submitted_rejected_deff = []
		for each_ad in ad:
			if each_ad.document.id in def_docs_submitted:
				if each_ad.reload_flag == True and each_ad.exception_notes == 'Deferred':
					def_doc_submitted_rejected_deff.append(each_ad.document.id)
				if each_ad.rejected_by_bits_flag == True:
					def_doc_submitted_rejected_deff.append(each_ad.document.id)
				if each_ad.file == '':
					def_doc_submitted_rejected_deff.append(each_ad.document.id)

		return def_docs_not_submitted+def_doc_submitted_rejected_deff

	def render(self, value):
		# docs=Accessor(self.field).resolve(value)
		my_str=""
		def_docs = self.get_deff_offer_status(value.login_email.email)
		if def_docs:
			doc_names = []
			for doc in def_docs:
				doc_typ = DocumentType.objects.get(id=doc)
				doc_names.append(doc_typ.document_name)
			my_str = ",".join(doc_names)

		return escape(my_str)

class MissingColumnForSubView(Column):
	''' Display missing documents'''
	def render(self, value):
		docs=Accessor(self.field).resolve(value)
		return format_html(', <br>'.join(docs.split(',')))

class NumberColumn(Column):
	''' right align column containing numbers'''
	def render(self, value):
		docs=Accessor(self.field).resolve(value)
		return format_html('<p style="text-align:right">'+str(docs)+'</p>')

class CourseColumn(Column):

	def __init__(self, index=None, *args, **kwargs):
		super(CourseColumn, self).__init__(*args, **kwargs)
		self.index = index

	def render(self, value):
		courses=Accessor(self.field).resolve(value)
		course = '-'
		try:
			course = courses[self.index]
		except: pass
		return escape(course)

class ExtraLinkColumn(LinkColumn):
	def __init__(self, model, extra_model, header=None, links=None, extra_links=None, delimiter='&nbsp', field=None, **kwargs):
		super(ExtraLinkColumn, self).__init__(header=header, links=links, delimiter=delimiter, field=field, **kwargs)
		self.extra_links = extra_links
		self.model = model
		self.extra_model = extra_model

	def render(self, obj):

		if obj._meta.model_name == self.model._meta.model_name:
			return self.delimiter.join([link.render(obj) for link in self.links])

		elif obj._meta.model_name == self.extra_model._meta.model_name:
			return self.delimiter.join([link.render(obj) for link in self.extra_links])

class EduvStatusColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		#for eduvanz archived data beacuse it is char field with no status choices.
		if value.__class__.__name__=="EduvanzApplicationArchived":
			edu_status = dict(EduvanzApplication.EDUVANZ_CHOICES)
			try:
				data = edu_status[value.status_code]
			except:
				data='-'
		return escape(data if data else '')

class PropelldStatusColumn( Column ):
	''' Display input and blank instead of None '''
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		return escape(data if data else '')

from registrations.models import OtherFeePayment
class PaidDateColumn(DatetimeColumn):

	def render(self,value):
		date = Accessor(self.field).resolve(value)
		
		ofp = OtherFeePayment.objects.filter(program=value.program,fee_type=value.fee_type,email=value.email)
		
		if ofp:
			if value.__class__.__name__=="AdhocEduvanzApplication":
				if ofp[0].paid_on and value.status_code == 'ELS301':
					text = timezone.localtime(ofp[0].paid_on).strftime("%d-%m-%Y %I:%M %p")
				else:
					text = '-'
		else:
			text = '-'
		return escape(text)

class PaymentBankColumn(Column):
	def render(self, value):
		data = Accessor(self.field).resolve(value)
		if data:
			if data.isnumeric(): #to check if the unicode field value is an integer
				text = 'Tech Process'
			else:
				text = data
		else:
			text = ''
		return escape(text)
