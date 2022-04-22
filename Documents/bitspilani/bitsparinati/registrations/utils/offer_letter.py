from easy_pdf.rendering import render_to_pdf, make_response
from django.http import FileResponse
from django.http import HttpResponse
from django.core.files import File
from django.template import loader, Context
from django.views.generic import TemplateView
from registrations.models import *
from bits_admin.models import *
from django.conf import settings
import datetime
import base64
import uuid
import boto3
import os
import io

def get_prog_context(app, prog):
	return {
		'courseL':FirstSemCourseList.objects.filter(
			program__program_code=prog.program_code,
			admit_year=app.admit_year,
			active_flag=True
		),
		'pgFeeAdm':PROGRAM_FEES_ADMISSION.objects.get(
			program__program_code=prog.program_code,
			fee_type='1',latest_fee_amount_flag=True
			),
		'appfees':PROGRAM_FEES_ADMISSION.objects.get(
			program__program_code=prog.program_code,
			fee_type='2',
			latest_fee_amount_flag=True
		).fee_amount,
	}

def render_offer_letter_content(cs):
	template_name = "offer_letter_pdf.html"
	context = {}
	program_name = cs.application.program.program_name
	context['cs'] = cs.__dict__
	context['cs']['application'] = cs.application
	context['cs']['rejection_by_candidate_reason'] = cs.rejection_by_candidate_reason
	context['cs']['new_sel_prog'] = cs.new_sel_prog
	
	adm_fees = cs.adm_fees

	context['admmf'] = settings.ADMISSION_FEES
	context['is_IOT_dt'] = cs.accepted_rejected_by_candidate and (cs.accepted_rejected_by_candidate.date() <= datetime.date(day=26, month=12, year=2017)) and cs.application.program.program_code=='CIOT'
	template_name = cs.application.program.offer_letter_template or template_name

	try:
		context.update(get_prog_context(cs.application, cs.application.program))
		ap_exp = ApplicantExceptions.objects.get(
			applicant_email=cs.application.login_email.email,
			program = cs.application.program
		)
		template_name = ap_exp.offer_letter or template_name

		if ap_exp.transfer_program:
			context.update(get_prog_context(cs.application, ap_exp.transfer_program))
			template_name = (
				ap_exp.offer_letter or 
				ap_exp.transfer_program.offer_letter_template or 
				cs.application.program.offer_letter_template
			)
			program_name = ap_exp.transfer_program.program_name
				
	except (
		ApplicantExceptions.DoesNotExist, 
		FirstSemCourseList.DoesNotExist,
		PROGRAM_FEES_ADMISSION.DoesNotExist,
		) as e:
		context.update(get_prog_context(cs.application, cs.application.program))

	context['semFees'] = adm_fees - 16500

	context['program_name'] = program_name

	if cs.offer_letter_template:
		template_name = cs.offer_letter_template

	pdf_file_bytes = io.BytesIO(bytes(render_to_pdf(template_name, context, encoding="utf-8")))
	return File(pdf_file_bytes, name='%s-offer-letter.pdf'%(cs.student_id, ))

	# return base64.b64encode(render_to_pdf(template_name, context, encoding="utf-8"))


def render_archieve_offer_letter_content(cs):
	template_name = "offer_letter_pdf.html"
	context = {}
	program_name = cs.application.program.program_name
	context['cs'] = cs
	adm_fees = cs.adm_fees

	context['admmf'] = settings.ADMISSION_FEES
	context['is_IOT_dt'] = (cs.accepted_rejected_by_candidate and cs.accepted_rejected_by_candidate.date() <= datetime.date(day=26, month=12, year=2017)) and cs.application.program.program_code=='CIOT'
	template_name = cs.application.program.offer_letter_template or template_name
	
	try:
		context.update(get_prog_context(cs.application, cs.application.program))
		ap_exp = ApplicantExceptionsArchived.objects.get(
			applicant_email=cs.application.login_email,
			program = cs.application.program.program_code, 
			run=cs.application.run)
		template_name = ap_exp.offer_letter or template_name

		if ap_exp.transfer_program:
			context.update(get_prog_context(
					cs.application, 
					ProgramArchived.objects.get(program_code=ap_exp.transfer_program)
				)
			)
			template_name = (
				ap_exp.offer_letter or 
				ProgramArchived.objects.get(program_code=ap_exp.transfer_program).offer_letter_template or 
				cs.application.program.offer_letter_template
			)
			program_name = ap_exp.transfer_program
				
	except (
		ApplicantExceptionsArchived.DoesNotExist, 
		FirstSemCourseList.DoesNotExist,
		PROGRAM_FEES_ADMISSION.DoesNotExist,
		) as e:
		context.update(get_prog_context(cs.application, cs.application.program))

	if not adm_fees:
		adm_fees = 17000

	context['semFees'] = adm_fees - 16500

	context['program_name'] = program_name

	if cs.offer_letter_template:
		template_name = cs.offer_letter_template

	# return base64.b64encode(render_to_pdf(template_name, context, encoding="utf-8"))

	pdf_file_bytes = io.BytesIO(bytes(render_to_pdf(template_name, context, encoding="utf-8")))
	return File(pdf_file_bytes, name='%s-offer-letter.pdf'%(cs.student_id, ))

from django.http import FileResponse
class BaseOfferLetterView(TemplateView):

	def get_application_document(self, request, pk):
		raise Exception('need to override by child class')

	def render_pdf(self, cs):
		from registrations.utils import storage
		temp_file = storage.document_offer_file(cs)
		content = temp_file.read()
		response = HttpResponse(content, content_type='application/pdf')
		return response

class OfferLetterView(BaseOfferLetterView):
	def get(self, request, app_id, *args, **kwargs):
		cs = CandidateSelection.objects.get(application__student_application_id=app_id)
		return self.render_pdf(cs)

class OfferLetterArchiveView(BaseOfferLetterView):
	def get(self, request, pk, *args, **kwargs):
		cs = CandidateSelectionArchived.objects.get(application__pk=pk)
		return self.render_pdf(cs)

class OfferLetterUserView(BaseOfferLetterView):
	def get(self, request, *args, **kwargs):
		cs = CandidateSelection.objects.get(application__login_email=request.user)
		return self.render_pdf(cs)


def offer_updater():
	## one time code to be run in server
	from django.core.files import File
	import uuid
	import os
	import io
	import base64
	for cs in CandidateSelection.objects.filter(offer_letter_tmp__isnull=False).iterator():
		pdf_file, file_name = base64.b64decode(cs.offer_letter_tmp), '%s_offer_letter.pdf' % (cs.application.student_application_id)
		f = File(io.BytesIO(bytes(pdf_file)), name=file_name)
		cs.offer_letter = f
		cs.offer_letter_tmp = None
		cs.save()
		print cs.offer_letter.name, cs.offer_letter_tmp


def offer_updater_archive():
	## one time code to be run in server
	from django.core.files import File
	import uuid
	import os
	import io
	import base64
	for cs in CandidateSelectionArchived.objects.filter(offer_letter_tmp__isnull=False).iterator():
		pdf_file, file_name = base64.b64decode(cs.offer_letter_tmp), '%s_offer_letter.pdf' % (cs.application.student_application_id)
		f = File(io.BytesIO(bytes(pdf_file)), name=file_name)
		cs.offer_letter = f
		cs.offer_letter_tmp = None
		cs.save()
		print cs.offer_letter.name, cs.offer_letter_tmp


