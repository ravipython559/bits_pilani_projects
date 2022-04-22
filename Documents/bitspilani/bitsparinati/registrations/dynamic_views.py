from django.contrib.auth.decorators import login_required
from django.forms.models import (modelformset_factory, 
	inlineformset_factory, formset_factory)
from django.core.urlresolvers import reverse_lazy
from django.template.defaultfilters import mark_safe
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import Http404
from django.db import IntegrityError, transaction
from django.views.generic import TemplateView, FormView,UpdateView,View
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import render
from django.forms.models import formset_factory
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect, Http404
from registrations.models import *
from registrations.tables_ajax import *
from registrations.tables import *
from django.db.models.functions import *
from django.db.models import *
from registrations.models import *
from registrations.forms import *
from registrations.extra_forms import *
from django.db.models import Prefetch
from django.http import FileResponse
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from bits_admin.forms import DobForm
import datetime
import logging
import uuid
import boto3
import os
from django.http import JsonResponse
from django.contrib.staticfiles.storage import staticfiles_storage
from registrations.utils.encoding_pdf import BasePDFTemplateView
from registrations.utils.utility_function import check_inactive_program_flag
from PIL import Image
from django.core.files import File
from tempfile import NamedTemporaryFile
from registrations.utils import offer_letter_regen as olg
import io
from django.http import HttpResponse
import magic

logger = logging.getLogger("main")

class BaseConfirmationFile(FormView):
	model = ApplicationDocument
	app = None
	pdm = ProgramDocumentMap
	dt = DocumentType
	sca = StudentCandidateApplication
	template_name = 'student_document_view.html'
	success_url = reverse_lazy('registrationForm:student-upload-file-view')
	asterick = mark_safe('<span style="color:red">*</span>')
	get_app = lambda self: self.sca.objects.get(login_email=self.request.user)
	get_form_class = lambda self: confirm_update_file_form(self.get_app().pk)

	def get_uploaded_files(self, ad_query=None, pdm_query=None, is_pg_doc=False):
		documents = []
		for doc in ad_query.iterator():
			t={}
			t['doc_type'] = doc.document.document_name
			t['doc_link'] = doc.pk if doc.file else None
			t['doc_name'] = doc.file.name.split("/")[-1] if doc.file else '-'
			if is_pg_doc:
				t['mandatory'] = pdm_query.get(
					document_type__document_name=doc.document.document_name
					).mandatory_flag
			else:
				t['mandatory'] = doc.document.mandatory_document
			documents.append(t)
		return documents

	def get_context_data(self, **kwargs):
		self.app = self.get_app()
		context = super(BaseConfirmationFile, self).get_context_data(**kwargs)
		context['query'] = self.app
		uploadedData = []
		ad = ApplicationDocument.objects.filter(application=self.app
			).order_by('-document__mandatory_document')
		pdm_query = self.pdm.objects.filter(program=self.app.program)
		dt_query = self.dt.objects.all()

		context['documents'] = self.get_uploaded_files(
			ad_query=ad, 
			pdm_query=(pdm_query if pdm_query.exists() else None), 
			is_pg_doc=pdm_query.exists()
		)

		return context

	def form_valid(self, form):
		self.app = self.get_app()
		try:
			with transaction.atomic():
				self.model.objects.filter(application=self.app).update(certification_flag=True)
				self.app.application_status='Application Fee Paid,Documents Uploaded'
				self.app.save()
		except IntegrityError:
			messages.error(request, 'There was an error while uploading')
			raise Http404

		return super(BaseConfirmationFile, self).form_valid(form)

class BaseStudentUpload(TemplateView):
	model = ApplicationDocument
	fields = ('document','file')
	formset_prefix = 'uploadFormset'
	template_name = 'registrations/upload_student.html'
	app = None
	ad_query = None
	pdm = ProgramDocumentMap
	dt = DocumentType
	sca = StudentCandidateApplication
	success_url = reverse_lazy('registrationForm:student-upload-file-view')
	asterick = mark_safe('<span style="color:red">*</span>')
	deffered_text = mark_safe("<span style='color:red'>Will need to be submitted but can be done later</span>")
	get_success_url = lambda self: self.success_url
	get_app = lambda self: self.sca.objects.get(login_email=self.request.user)
	get_formset_prefix = lambda self: self.formset_prefix
	formset_invalid = lambda self, formset: self.render_to_response(self.get_context_data(formset=formset))
	get_application_document = lambda self: self.model.objects.filter(application=self.app)

	def get_specific_ad(self, document_name):
		try:
			ad_query = self.ad_query.get(document__document_name=document_name)
			return {'exist_file_pk': ad_query.pk, 'exist_file': ad_query.file,'rej_reason':ad_query.rejection_reason}
		except self.model.DoesNotExist:
			return {'exist_file_pk': None, 'exist_file': None, 'rej_reason':None}

	def get_formset_class(self):
		self.app = self.get_app()
		self.formset_class = formset_factory(UploadFileForm, can_delete=False, extra=0,)
		return self.formset_class

	def get_formset(self, formset_class=None):
		if formset_class is None:
			formset_class = self.get_formset_class()
		return formset_class(**self.get_formset_kwargs())

	def get_formset_kwargs(self):
		kwargs = {
			'initial': self.get_formset_initial(),
			'prefix': self.get_formset_prefix(),
		}

		if self.request.method in ('POST', 'PUT'):
			kwargs.update({
				'data': self.request.POST,
				'files': self.request.FILES,
			})
		return kwargs

	def get_formset_initial(self):
		self.app = self.get_app()
		self.ad_query = self.get_application_document()
		pdm_filter = self.pdm.objects.filter(
			program=self.app.program
			).order_by(
				'-mandatory_flag', 
				'-deffered_submission_flag'
			)
		dt_filter = self.dt.objects.order_by('-mandatory_document')
		partial_important = lambda doc_name:'{0}{1}'.format(doc_name, self.asterick)

		if pdm_filter.exists():
			initial = [ 
				{
					'document' : pdm.document_type.pk ,
					'document_name' : (
						partial_important(pdm.document_type.document_name) 
							if pdm.mandatory_flag else pdm.document_type.document_name
						),
					'file' : self.get_specific_ad(pdm.document_type.document_name)['exist_file'],
					'deffered_text' : self.deffered_text if pdm.deffered_submission_flag else '', 
					'exist_file' : self.get_specific_ad(pdm.document_type.document_name)['exist_file'],
					'exist_file_pk' : self.get_specific_ad(pdm.document_type.document_name)['exist_file_pk'],
				} for pdm in pdm_filter
			]
		else:
			initial = [
				{
				    'document' : dt.pk ,
				    'document_name' : (
				        partial_important(dt.document_name) 
				            if dt.mandatory_document else dt.document_name
				        ),
				    'deffered_text':None,
				    'exist_file' : self.get_specific_ad(dt.document_name)['exist_file'],
				    'exist_file_pk' : self.get_specific_ad(dt.document_name)['exist_file_pk'],
				} for dt in dt_filter
			]

		return initial

	def get_context_data(self, **kwargs):
		self.app = self.get_app()
		context = super(BaseStudentUpload, self).get_context_data(**kwargs)
		context['query'] = self.app
		if 'formset' not in context: context['formset'] = self.get_formset()
		context['formset_prefix'] = self.formset_prefix
		return context

	def post(self, request, *args, **kwargs):
		formset = self.get_formset()
		if formset.is_valid():
			return self.formset_valid(formset)
		else:
			return self.formset_invalid(formset)

	def update_or_create(self, form):
		try:
			pdm = self.pdm.objects.get(program=self.app.program, 
				document_type=form.cleaned_data.get('document'))
		except self.pdm.DoesNotExist:
			pdm = None

		document = form.cleaned_data.get('document')
		upload_file = form.cleaned_data.get('file')
		tmp_file = NamedTemporaryFile(delete=True)

		if 'file' in form.changed_data and document.document_name == 'APPLICANT PHOTOGRAPH':
			x = form.cleaned_data.get('x')
			y = form.cleaned_data.get('y')
			w = form.cleaned_data.get('width')
			h = form.cleaned_data.get('height')
			r = form.cleaned_data.get('rotate')
			with Image.open(upload_file) as image:
				rotated_image = image.rotate(r*(-1),expand=1)
				crop_image = rotated_image.crop((x, y, w+x, h+y))
				resized_image = crop_image.resize((150, 150), Image.ANTIALIAS)
				resized_image.save(tmp_file, format=image.format)
			upload_file = File(tmp_file, name=upload_file.name)

		obj,created = self.model.objects.update_or_create(
			pk=form.cleaned_data.get('exist_file_pk') or None,
			application=self.app,
			defaults={
				'file': upload_file or form.cleaned_data.get('exist_file'),
				'last_uploaded_on': timezone.localtime(timezone.now()),
				'document':document,
				'program_document_map':pdm,
				'rejected_by_bits_flag':False,
				'rejection_reason':None,
				}
			)
		tmp_file.close()

	def formset_valid(self, formset): 
		try:
			with transaction.atomic():
				for form in formset:
					if form.cleaned_data.get('file') or form.cleaned_data.get('exist_file_pk') or form.cleaned_data.get('deffered_text'):
						self.update_or_create(form)
				self.app.application_status = settings.APP_STATUS[14][0]
				self.app.save()
		except IntegrityError:
			messages.error(request, 'There was an error while uploading')
			raise Http404

		return HttpResponseRedirect(self.get_success_url()) 


class BaseFinalUploadFile(TemplateView):
    app = None
    sca = StudentCandidateApplication
    pdm = ProgramDocumentMap
    dt = DocumentType
    ad = ApplicationDocument
    get_app = lambda self: self.sca.objects.get(login_email=self.request.user)

    def get_uploaded_files(self, ad_query=None, pdm_query=None, is_pg_doc=False):
        documents = []
        for doc in ad_query.iterator():
            t={}
            t['doc_type'] = doc.document.document_name
            t['doc_link'] = doc.pk if doc.file else None
            t['doc_name'] = doc.file.name.split("/")[-1] if doc.file else '-'
            if is_pg_doc:
                try:
                    t['mandatory'] = pdm_query.get(
                        document_type__document_name=doc.document.document_name
                        ).mandatory_flag
                except self.pdm.DoesNotExist:
                    t['mandatory'] = False
            else:
                t['mandatory'] = doc.document.mandatory_document
            documents.append(t)
        return documents

    def get_context_data(self, **kwargs):
        self.app = self.get_app()
        context = super(BaseFinalUploadFile, self).get_context_data(**kwargs)
        context['query'] = self.app
        uploadedData = []
        ad = self.ad.objects.filter(application=self.app
            ).order_by('-document__mandatory_document')
        pdm_query = self.pdm.objects.filter(program=self.app.program)
        dt_query = self.dt.objects.all()

        context['documents'] = self.get_uploaded_files(
            ad_query=ad, 
            pdm_query=(pdm_query if pdm_query.exists() else None), 
            is_pg_doc=pdm_query.exists()
        )

        return context


class ReviewerApplicantData(TemplateView):
	def get_context_data(self, program=None, status=None, pg_type=None, admit_batch=None, **kwargs):
		query = StudentCandidateApplication.objects.prefetch_related(
			Prefetch('applicationpayment_requests_created_3',
				queryset=ApplicationPayment.objects.filter(fee_type=1,
					application__application_status=settings.APP_STATUS[11][0]),
				to_attr='adm'),
			).filter(
			application_status__in=[ x[0] for x in settings.APP_STATUS[:12]] + [settings.APP_STATUS[17][0]]
			)
		query = query.filter(program=program) if program else query
		query = query.filter(application_status=status) if status else query
		query = query.filter(program__program_type=pg_type) if pg_type else query
		query = query.filter(admit_batch=admit_batch) if admit_batch else query
		
		query = query.annotate(
			su_comment=F('candidateselection_requests_created_5550__su_rev_com'),
			rev_comment=F('candidateselection_requests_created_5550__es_com'),
			app_id = Case(
				When(candidateselection_requests_created_5550__new_application_id=None, 
					then=Concat('student_application_id',Value(' '))),
				default=Concat('candidateselection_requests_created_5550__new_application_id',Value(' ')),
				output_field=CharField(),
				),
			pg_name = F('program__program_name'),
			student_id = F('candidateselection_requests_created_5550__student_id'),
			last_updated = Case(
				When(application_status__in=[settings.APP_STATUS[0][0],
					settings.APP_STATUS[4][0]], 
					then=Max(F('applicationdocument_requests_created_1__last_uploaded_on'))
					),
				When(application_status__in=[settings.APP_STATUS[5][0],settings.APP_STATUS[7][0]], 
					then=F('candidateselection_requests_created_5550__selected_rejected_on')
					),
				When(application_status__in=[settings.APP_STATUS[6][0],settings.APP_STATUS[8][0]], 
					then=F('candidateselection_requests_created_5550__offer_reject_mail_sent')
					),
				When(application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[10][0]], 
					then=F('candidateselection_requests_created_5550__accepted_rejected_by_candidate')
					),
				When(application_status=settings.APP_STATUS[15][0], 
					then=F('candidateselection_requests_created_5550__es_to_su_rev_dt')
					),
				When(application_status=settings.APP_STATUS[16][0], 
					then=F('candidateselection_requests_created_5550__app_rej_by_su_rev_dt')
					),
				When(application_status__in=[settings.APP_STATUS[1][0],settings.APP_STATUS[2][0],
					settings.APP_STATUS[3][0], settings.APP_STATUS[17][0]],
					then=F('last_updated_on_datetime'),
					),
				When(Q(application_status=settings.APP_STATUS[11][0],
						applicationpayment_requests_created_3__fee_type='1',), # datetime for admission fees paid.
					then=Max('applicationpayment_requests_created_3__payment_date')
					),
				When(application_status__in=[settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]],
					then=F('pre_selected_rejected_on_datetime'),
					),
				default=F('last_updated_on_datetime'),
				output_field=DateTimeField()
				),
			)
		context = super(ReviewerApplicantData, self).get_context_data(**kwargs)
		data={'programs':program, 'status':status, 'pg_type':pg_type, 'admit_batch':admit_batch, }
		SCATable = filter_paging(programs=program,status=status,pg_type=pg_type, admit_batch=admit_batch,)
		context['table'] = SCATable(query)
		context['form2'] = rev_filter_form(data)
		context['scaTotal'] = query.count()
		context['query'] = query
		context['program'] = program
		context['status'] = status
		context['pg_type'] = pg_type
		context['admit_batch'] = admit_batch
		return context 
		

	def get(self, request, *args, **kwargs):
		program = request.GET.get('programs',None)
		status = request.GET.get('status',None)
		pg_type = request.GET.get('pg_type',None)
		admit_batch = request.GET.get('admit_batch',None)
		return super(ReviewerApplicantData, self).get(request, 
			program=program, status=status, pg_type=pg_type, admit_batch=admit_batch,
			*args, **kwargs)


class BaseApplicant(BasePDFTemplateView):

	template_name = "applicantpdf.html"
	pdf_kwargs = {'encoding' : 'utf-8',}

	def get_context_data(self, **kwargs):
		context = super(BaseApplicant, self).get_context_data(
			pagesize="A4",
			title="Hi there!",
			**kwargs)
		sca = StudentCandidateApplication.objects.get(login_email=self.request.user)

		# code to hide employment and mentor details
		sca_attributes = sca.__dict__.keys()
		for x in sca_attributes:
			setattr(sca, '%s_hide' %(x), False)

		rejected_attributes = FormFieldPopulationSpecific.objects.filter(
		program=sca.program,
		show_on_form=False,
		).values_list('field_name', flat=True)

		for x in rejected_attributes:
			setattr(sca, '%s_hide' %(x), True)

		teaching_mode_check = FormFieldPopulationSpecific.objects.filter(program = sca.program,show_on_form=True,
				field_name__in=['teaching_mode','programming_flag','alternate_email_id',]
			).values_list('field_name', flat=True)
		pfa_admit = PROGRAM_FEES_ADMISSION.objects.filter(program=sca.program, fee_type=2)[0]
		context['pfa_admit']=pfa_admit
		context['q'] = sca
		context['qualification'] = StudentCandidateQualification.objects.filter(application=sca)[:5]
		context['qual_count'] = range(context['qualification'].count(),5)
		context['exp'] = StudentCandidateWorkExperience.objects.filter(application=sca)
		context['teaching_mode_check'] = teaching_mode_check
		context['is_specific'] = sca.program.program_type == 'specific'
		if sca.program.application_pdf_template:
			self.template_name = sca.program.application_pdf_template

		return context

def get_prog_context(app,prog,context):

	context['courseL'] = FirstSemCourseList.objects.filter(
		program = prog,
		admit_year=app.admit_year,active_flag=True
		)
	context['pgFeeAdm'] = PROGRAM_FEES_ADMISSION.objects.get(
		program =prog,
		fee_type='1',latest_fee_amount_flag=True
		)
	context['appfees'] = PROGRAM_FEES_ADMISSION.objects.get(
		program =prog,
		fee_type='2',
		latest_fee_amount_flag=True
		).fee_amount

	pld = ProgramLocationDetails.objects.get(
			program = prog,
			location = app.current_location
			)

class BaseOfferLetter (BasePDFTemplateView):
	"""Payment Fee template view."""

	template_name = "offer_letter_pdf.html"

	def get_context_data(self, **kwargs):
		logger.info("{0} invoked funct.".format(self.request.user.email))
		email_id = self.request.user
		context = super(BaseOfferLetter, self).get_context_data(
			pagesize="A4", title="Offer letter", **kwargs)
		app = StudentCandidateApplication.objects.get(
			login_email=self.request.user
			)
		
		context['admmf'] = settings.ADMISSION_FEES
		cs = CandidateSelection.objects.get(application=app)
		program_name = cs.application.program.program_name
		context['cs'] = cs
		adm_fees = cs.adm_fees
		context['admmf'] = settings.ADMISSION_FEES
		context['is_IOT_dt'] = (cs.accepted_rejected_by_candidate.date() <= datetime.date(day=26, month=12, year=2017)) and cs.application.program.program_code=='CIOT'
		template_name = app.program.offer_letter_template
		try:
			get_prog_context(app,app.program,context)
			ap_exp = ApplicantExceptions.objects.get(applicant_email=app.login_email.email,
				program = app.program)
			template_name = ap_exp.offer_letter or template_name
			if ap_exp.transfer_program:
				get_prog_context(app,ap_exp.transfer_program,context)
				template_name = (
					ap_exp.offer_letter or 
					ap_exp.transfer_program.offer_letter_template or 
					app.program.offer_letter_template
				)
				program_name = ap_exp.transfer_program.program_name
					
		except (
			ApplicantExceptions.DoesNotExist, 
			FirstSemCourseList.DoesNotExist,
			PROGRAM_FEES_ADMISSION.DoesNotExist,
			ProgramLocationDetails.DoesNotExist,
			) as e:
			get_prog_context(app,app.program,context)

		context['semFees'] = adm_fees - 16500

		context['program_name'] = program_name

		if cs.offer_letter_template:
			self.template_name = cs.offer_letter_template

		elif template_name:
			self.template_name = template_name

		return context


class BaseDeffDocsUpload(BaseStudentUpload):
	formset_prefix = 'defuploadFormset'
	template_name = 'registrations/deff_docs_upload.html'
	status = mark_safe("<p>To be Submitted</p>")
	success_url = reverse_lazy('registrationForm:applicantData')
	get_success_url = lambda self: self.success_url

	def get_formset_class(self):
		self.app = self.get_app()
		self.formset_class = formset_factory(DeffDocsUploadForm, can_delete=False, extra=0,)
		return self.formset_class

	def get_formset_initial(self):
		self.app = self.get_app()
		self.ad_query = self.get_application_document()
		pdm_filter = self.pdm.objects.filter(
				Q(deffered_submission_flag=True)|Q(mandatory_flag=True
			),
			program=self.app.program
			).exclude(
			document_type__in=ApplicationDocument.objects.filter(
				accepted_verified_by_bits_flag=True,
				application=self.app,
			).exclude(
				Q(file='')|Q(file__isnull=True)
				).values_list('document__pk')
			)

		partial_important = lambda doc_name:'{0}'.format(doc_name,)
		initial = [ 
			{
				'document' : pdm.document_type.pk ,
				'document_name' : (
					partial_important(pdm.document_type.document_name) 
					),
				'file' : self.get_specific_ad(pdm.document_type.document_name)['exist_file'],
				'status' : self.status,
				'exist_file' : self.get_specific_ad(pdm.document_type.document_name)['exist_file'],
				'exist_file_pk' : self.get_specific_ad(pdm.document_type.document_name)['exist_file_pk'],
				'rej_reason':self.get_specific_ad(pdm.document_type.document_name)['rej_reason'],
			} for pdm in pdm_filter
		]

		return initial	
	

	def formset_valid(self, formset): 
		try:
			with transaction.atomic():
				for form in formset:
					file = form.cleaned_data.get('file')
					rej_reason = form.cleaned_data.get('rej_reason')
					if rej_reason and not 'file' in form.changed_data:
						pass
					else:
						self.update_or_create(form)
				self.app.save()
				olg.regen_offer(self.app)
		except IntegrityError:
			raise Http404

		return HttpResponseRedirect(self.get_success_url())



class BaseReviewData(UpdateView):
	model = StudentCandidateApplication
	cs_model = CandidateSelection
	form_class = CandidateAcceptRejectForm
	alert_status = False 
	template_name = 'registrations/review_application_form_view.html'
	pk_url_kwarg = 'application_id'
	formset_prefix = 'doc'

	def get_success_url(self):
		return reverse_lazy('registrationForm:review_application_details', 
				kwargs={'application_id':self.get_object().pk})
		
	def second_form(self):
		SubReviewerApplicationDocumentFormSet = inlineformset_factory(
			StudentCandidateApplication,
			ApplicationDocument,
			form=sub_rev_app_doc(email=self.request.user.email),
			extra=0,
			can_delete=False,
			can_order=False
		)
		return SubReviewerApplicationDocumentFormSet

	def get_initial(self):
		try:
			cs = self.cs_model.objects.get(application=self.get_object())
			bits_reason = cs.bits_rejection_reason
			bits_comment = cs.selection_rejection_comments
		except self.cs_model.DoesNotExist:
			bits_reason = None
			bits_comment = None

		bits_reason = cPickle.loads(str(bits_reason)) if bits_reason else []
		if bits_reason:
			bits_reason = BitsRejectionReason.objects.filter(reason__in = bits_reason).values_list('pk', flat=True)
		else :
			bits_reason = None

		application_status = self.object.application_status 

		if self.object.application_status in [settings.APP_STATUS[3][0], settings.APP_STATUS[4][0],]:
			application_status = settings.APP_STATUS[1][0]
		elif self.object.application_status == settings.APP_STATUS[6][0]:
			application_status = settings.APP_STATUS[5][0]
		elif self.object.application_status==settings.APP_STATUS[8][0]:
			application_status = settings.APP_STATUS[7][0]

		initial = {
			'application_status':application_status,
			'bits_rejection_reason':bits_reason ,
			'selection_rejection_comments':bits_comment}
		return initial

	def get(self, request, application_id, alert_status=None, *args, **kwargs):
		self.alert_status = alert_status and bool(int(alert_status))
		return super(BaseReviewData, self).get(request, application_id, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(BaseReviewData, self).get_context_data(**kwargs)
		if 'app_form' not in context:
			context['app_form'] = self.get_form()
		if 'doc_form' not in context:
			context['doc_form'] = self.second_form()(instance=self.get_object(), 
				prefix=self.formset_prefix)

		context['alert_status'] = self.alert_status

		# code to hide employment and mentor details
		app=self.get_object()
		sca_attributes = app.__dict__.keys()
		for x in sca_attributes:
			setattr(app, '%s_hide' %(x), False)

		rejected_attributes = FormFieldPopulationSpecific.objects.filter(
		program=app.program,
		show_on_form=False,
		).values_list('field_name', flat=True)

		for x in rejected_attributes:
			setattr(app, '%s_hide' %(x), True)

		#display remaing docunemts
		doc_submitted = ApplicationDocument.objects.filter(application=self.get_object()).values_list('document',flat=True)
		all_doc_of_programs = ProgramDocumentMap.objects.filter(program=self.get_object().program)
		show = all_doc_of_programs.exclude(document_type_id__in=doc_submitted)
		show =  show.order_by('document_type__document_name')
		context['document_not_submitted'] = show
		p_code = str(app.student_application_id)[1:5]
		program_object = Program.objects.filter(program_code=p_code)
		document_submission_flag = program_object[0].document_submission_flag
		context['document_submission_flag'] = document_submission_flag
		context['form'] = app
		context['edu1'] = StudentCandidateWorkExperience.objects.filter(application=self.get_object())
		context['qual1'] = StudentCandidateQualification.objects.filter(application=self.get_object())
		context['uploadFiles'] = ApplicationDocument.objects.filter(application=self.get_object())
		context['def_check'] = self.def_check()
		context['title'] = self.get_object().program.form_title
		context['dob_form'] = DobForm(initial={"date_of_birth":self.get_object().date_of_birth},instance=self.get_object())
		context['form_to_be_enabled'] = self.get_object().application_status in [settings.APP_STATUS[6][0], settings.APP_STATUS[8][0], settings.APP_STATUS[11][0], settings.APP_STATUS[10][0],settings.APP_STATUS[9][0],]
		context['shortlisted'] = settings.APP_STATUS[5][0]
		context['is_transfer_program_admission_active_disable'] = check_inactive_program_flag(self.get_object(),'active_for_admission_flag')
		context['rejected'] = settings.APP_STATUS[7][0]
		context['teaching_mode_check'] = self.def_teaching_mode_check()
		context['is_specific'] = self.get_object().program.program_type == 'specific'
		context['url_sel_rej'] = reverse_lazy('registrationForm:pre_sel_rej_email')
		#context['is_pg_inactive'] = not self.get_object().program.active_for_applicaton_flag or transfer_program_check(self.get_object())
		context['is_admission_inactive'] = not self.get_object().program.active_for_admission_flag
		return context

	def post(self, request, application_id=None, *args, **kwargs):
		self.application_id = application_id
		self.object = self.get_object()
		
		app_form = self.get_form()
		doc_form = self.second_form()(self.request.POST, instance=self.object, prefix="doc")
		if app_form.is_valid() and doc_form.is_valid():
			return self.forms_valid(form=app_form, formset=doc_form)
		else:
			return self.form_invalid(app_form, doc_form, **kwargs)

	def send_document_rejection_mail(self, rejection_list):
		rejection_message = "<br/>".join(['{0} - {1}'.format(x, y) for (x,y) in rejection_list])
		subject = 'Few of Documents are Rejected for Application %s'%(self.object.student_application_id)
		self.object.application_status = settings.APP_STATUS[3][0]
		self.object.save()
		msg_html = render_to_string('registrations/applicant_doc_rej_mail.html', 
			{
				'rejection_message':"\n".join(['{0} - {1}'.format(x, y) for (x,y) in rejection_list]),
			}
		)
		email = send_mail(subject,msg_html, '<'+settings.FROM_EMAIL+'>', [self.object.email_id], html_message=msg_html,fail_silently=True)
		return email

	def in_review(self, application_status, instances):
		rejected_list = [ (f.document.document_name, f.rejection_reason.reason) for f in instances if f.rejected_by_bits_flag and f.file]

		if rejected_list:
			return self.send_document_rejection_mail(rejected_list)
		else:
			self.object.application_status = application_status
			self.object.save()
			cs_model = self.cs_model.objects.update_or_create(application=self.object, 
				defaults={
					'bits_rejection_reason':cPickle.dumps(None),
					'selection_rejection_comments':None, 
				}
			)
			return (self.object,cs_model)

	def shortlisted(self, application_status, instances): 
		rejected_list = [ (f.document.document_name, f.rejection_reason.reason) 
			for f in instances if f.rejected_by_bits_flag and f.file]

		if rejected_list:
			return self.send_document_rejection_mail(rejected_list)
		else:
			self.object.application_status = application_status #"Shortlisted"
			self.object.save()
			cs_model = self.cs_model.objects.update_or_create(application=self.object, 
				defaults={
					'selected_rejected_on':timezone.localtime(timezone.now()),
					'bits_selection_rejection_by': self.request.user.pk, 
					'bits_rejection_reason':cPickle.dumps(None),
					'selection_rejection_comments':None,
				}
			)
			return (self.object,cs_model)


	def rejected(self, application_status, bits_rejection_reason, selection_rejection_comments):
		self.object.application_status = application_status
		self.object.save()
		reasons = BitsRejectionReason.objects.filter(pk__in = bits_rejection_reason).values_list('reason', flat=True)
		cs_model = self.cs_model.objects.update_or_create(application=self.object, 
				defaults={
					'selection_rejection_comments': selection_rejection_comments,
					'bits_rejection_reason': cPickle.dumps(reasons),
					'bits_selection_rejection_by': self.request.user.pk,
					'selected_rejected_on':timezone.localtime(timezone.now()),
				}
			)
		return (self.object,cs_model)

	def def_check(self):
		return ApplicationDocument.objects.filter(Q( Q(file='') | Q(file__isnull=True) )|Q(reload_flag=True),
			application=self.get_object(),program_document_map__deffered_submission_flag=True).exists()
		
	#code to hide teaching mode
	def def_teaching_mode_check(self):
		return FormFieldPopulationSpecific.objects.filter(
				program=self.get_object().program,
				show_on_form=True,
				field_name__in=['teaching_mode','programming_flag','alternate_email_id',],
			).values_list('field_name', flat=True)

	def in_review_escalated(self, application_status,instances):
		rejected_list = [ (f.document.document_name, f.rejection_reason.reason) 
			for f in instances if f.rejected_by_bits_flag and f.file]
		self.object.application_status = application_status
		self.object.save()

		if rejected_list: 
			return self.send_document_rejection_mail(rejected_list)
		else:
			cs_model = self.cs_model.objects.update_or_create(application=self.object, 
				defaults={
					'bits_rejection_reason':cPickle.dumps(None),
					'selection_rejection_comments':None,
				}
			)
			return (self.object,cs_model)
			
	def forms_valid(self, form, formset): 
		
		status = form.cleaned_data.get('application_status')
		application_status = status if status else settings.APP_STATUS[1][0]
		bits_rejection_reason = form.cleaned_data.get('bits_rejection_reason')
		selection_rejection_comments = form.cleaned_data.get('selection_rejection_comments')
		try:
			with transaction.atomic():
				instances = formset.save() # save function in form
				if application_status == settings.APP_STATUS[1][0]:
					self.in_review(application_status, instances)
				elif application_status == settings.APP_STATUS[5][0]:
					self.shortlisted(application_status, instances)
				elif application_status == settings.APP_STATUS[7][0]:
					self.rejected(application_status, bits_rejection_reason, selection_rejection_comments)
				elif application_status == settings.APP_STATUS[2][0]:
					self.in_review_escalated(application_status,instances)

		except IntegrityError:
			raise Http404

		return HttpResponseRedirect(self.get_success_url()) #this need to be fixed

	def form_invalid(self, app_form, doc_form, **kwargs):
		ctx = self.get_context_data(app_form=app_form, doc_form=doc_form, **kwargs)
		return self.render_to_response(ctx)


class BaseDeferredReviewData(BaseReviewData):
	def second_form(self):
		SubReviewerApplicationDocumentFormSet = inlineformset_factory(
			StudentCandidateApplication,
			ApplicationDocument,
			form=def_sub_rev_app_doc(email=self.request.user.email),
			extra=0,
			can_delete=False,
			can_order=False
		)
		return SubReviewerApplicationDocumentFormSet

	def send_document_rejection_mail(self, rejection_list):
		rejection_message = "<br/>".join(['{0} - {1}'.format(x, y) for (x,y) in rejection_list])
		subject = 'Few of Documents are Rejected for Application %s'%(self.object.student_application_id)
		msg_html = render_to_string('registrations/applicant_doc_rej_mail.html', 
			{
				'rejection_message':"\n".join(['{0} - {1}'.format(x, y) for (x,y) in rejection_list]),
			}
		)
		email = send_mail(subject,msg_html, '<'+settings.FROM_EMAIL+'>', 
			[self.object.email_id], html_message=msg_html, fail_silently=True)
		return email


	def forms_valid(self, form, formset): 
		
		status = self.get_object().application_status
		application_statuses = [settings.APP_STATUS[6][0], 
			settings.APP_STATUS[9][0], settings.APP_STATUS[11][0]
		]

		if status in application_statuses:
			try:
				with transaction.atomic():
					forms = formset.save()
					rejected_list = [ (f.document.document_name, f.rejection_reason.reason)
					 for f in forms if f.rejected_by_bits_flag and f.file]
					if len(rejected_list):
						self.send_document_rejection_mail(rejected_list)
					olg.regen_offer(self.get_object())

			except IntegrityError:
				raise Http404

		return HttpResponseRedirect(self.get_success_url())

class BaseSendPreConfirmSelRejEmail(View):
	sca = None
	subject = 'Application Evaluation Completed - BITS Pilani Work Integrated Learning Programmes'
	app_model = StudentCandidateApplication
	model_eloa = ExceptionListOrgApplicants
	model_pfa = PROGRAM_FEES_ADMISSION
	get_sca = lambda self, pk: self.app_model.objects.get(pk=int(pk))
	get_success_url = lambda self: JsonResponse({'bits_success':200})

	def send_evaluation_mail(self, sub, template, to, **email_context):
		context = {
			'app_name': self.sca.full_name.strip().split()[0],
			'program':self.sca.program.program_name,
			'sel_rej_date':self.sca.pre_selected_rejected_on_datetime,
		}
		context.update(**email_context)

		html_message = render_to_string(template, context)

		return send_mail(sub, html_message, '<%s>' % (settings.FROM_EMAIL,), to, html_message=html_message, fail_silently=True)

	def selection_details(self):	
		self.sca.application_status = settings.APP_STATUS[18][0]
		self.sca.pre_selected_flag = self.sca.PRE_SELECTION_FLAG_CHOICES[1][0]
		logo_path = settings.STATIC_URL_FUNC('assets/images/BITS_logo.gif')
		
		email_context = {
			'admission_fee': self.sca_admission_fee(),
			'application_fee': self.sca_application_fee(),
			'logo_path': logo_path,
			'date_limit': timezone.localtime(self.sca.pre_selected_rejected_on_datetime).date() + timezone.timedelta(days=7),
		}
		
		email_template =  'registrations/pre_select_mail.html'
		subject = 'Provisional Admission Letter - %s' % (self.sca.program.program_name,)
		to = [ self.sca.email_id, ]
		return (subject, email_template, to, email_context)

	def rejection_details(self):
		self.sca.application_status = settings.APP_STATUS[19][0]
		self.sca.pre_selected_flag = self.sca.PRE_SELECTION_FLAG_CHOICES[2][0]

		email_context = {
			'admit_batch': self.sca.admit_batch,
		}

		email_template =  'registrations/pre_rej_mail.html'
		subject = 'Application Status - %s' % (self.sca.program.program_name,)
		to = [ self.sca.email_id, ]
		return (subject, email_template, to, email_context)

	def sca_application_fee(self):
		try:
			application_fee = self.model_eloa.objects.get(
				Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
				employee_email=self.sca.login_email.email, 
				exception_type='1', 
				program=self.sca.program).fee_amount

		except self.model_eloa.DoesNotExist : 
			application_fee = PROGRAM_FEES_ADMISSION.objects.get(
				program=self.sca.program,latest_fee_amount_flag=True,
				fee_type='2').fee_amount

		return application_fee

	def sca_admission_fee(self):
		try:
			admission_fee = self.model_eloa.objects.get(
				Q(fee_amount__gte = 0.01)|Q(fee_amount__isnull=False),
				employee_email=self.request.user.email,
				exception_type='2',
				program=self.sca.program,
				).fee_amount

		except self.model_eloa.DoesNotExist:
			admission_fee = self.model_pfa.objects.get(
				program=self.sca.program,
				latest_fee_amount_flag=True,
				fee_type='1').fee_amount

		return admission_fee

	def post(self, request, *args, **kwargs):
		app_id = request.POST['app_id']
		do_status = request.POST['do_status']
		self.sca = self.get_sca(int(app_id))
		email_context = {}
		self.sca.pre_selected_rejected_on_datetime = timezone.localtime(timezone.now())
		if request.is_ajax():
			if do_status == 'SHORT': 
				subject, email_template, to, email_context = self.selection_details()
				
			elif do_status == 'REJ': 
				subject, email_template, to, email_context = self.rejection_details()
		self.sca.save()
		self.send_evaluation_mail(subject, email_template, to, **email_context)
		return self.get_success_url()

class BaseDocumentUpload(TemplateView):

	def get_formset_initial(self):
		
		sca = StudentCandidateApplication.objects.get(login_email=self.request.user)
		app_doc = ApplicationDocument.objects.filter(application=sca)

		pdm_filter = ProgramDocumentMap.objects.filter(
			program=sca.program
		).exclude(
			document_type__in=app_doc.values_list('document',flat=True)
		)

		dt_filter = DocumentType.objects.exclude(
			pk__in=app_doc.values_list('document', flat=True)
		)

		if ProgramDocumentMap.objects.filter(program=sca.program).exists():
			initial = [{'document':x.document_type, 'application':sca.pk, 'id':None} for x in pdm_filter.iterator()]
		else:
			initial = [{'document':x, 'application':sca.pk, 'id':None} for x in dt_filter.iterator()]
		return initial

	def get_context_data(self, **kwargs):
		sca = StudentCandidateApplication.objects.get(login_email=self.request.user)
		p_code = str(sca.student_application_id)[1:5]
		program_object = Program.objects.filter(program_code=p_code)
		document_submission_flag = program_object[0].document_submission_flag
		context = super(BaseDocumentUpload, self).get_context_data(**kwargs)
		initial = self.get_formset_initial()
		formset_class = inlineformset_factory(
			StudentCandidateApplication, 
			ApplicationDocument,
			can_delete=False,
			extra=len(initial),
			form=DocumentUploadForm,
			formset=DocumentUploadFormSet
		)

		context['sca'] = sca
		context['document_submission_flag'] = document_submission_flag
		context['formset'] = formset_class(instance=sca, initial=initial, prefix='upload')
		return context 

class BaseUserFileViewDownload(View):

	def get_application_document(self, request, pk):
		raise Exception('need to override by child class')

	def get(self, request, pk, *args, **kwargs):
		from registrations.utils import storage

		ad = self.get_application_document(request, pk)
		extension = os.path.splitext(os.path.basename(ad.file.name))[-1]
		temp_file = storage.document_extract_file(ad)

		content = temp_file.read()
		mime_type = magic.from_buffer(temp_file.getvalue(), mime=True)
		
		return HttpResponse(temp_file.getvalue(), content_type=mime_type)