from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, TemplateView
from django.db.models.functions import Concat
from django.db.models import F, Value
from table.views import FeedDataView
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from io import BytesIO
from django.conf import settings
from django.shortcuts import render, redirect, HttpResponse
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import ast
import csv
import zipfile
import os
import shutil
import uuid
from django.urls import reverse
from celery.result import AsyncResult
from django.http import JsonResponse
from .forms import *
from master.models import *
from .tables import *
from .tasks import *
from .permissions import *
from django.db.models import Q,CharField, Value,When
from administrator.tasks import *
from master.utils.storage import admin_document_extract

# Create your views here.
@method_decorator([never_cache], name='dispatch')
class QPSubmissionStatusView(QPMUserPermissionMixin,FormView):
	template_name = 'administrator/view_qp_submission_status.html'
	form_class = QPSubmissionStatusForm

	def get_form_kwargs(self):
		kwargs = super(QPSubmissionStatusView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def get_initial(self):
		self.initial['semester_name'] = self.request.GET.get('semester_name')
		self.initial['program_type'] = self.request.GET.get('program_type')
		self.initial['batch_name'] = self.request.GET.get('batch_name')
		self.initial['faculty_id'] = self.request.GET.get('faculty_id')
		self.initial['exam_type_name'] = self.request.GET.get('exam_type_name')
		self.initial['exam_slot'] = self.request.GET.get('exam_slot')

		return self.initial

	def get_submission_list(self, data):

		qpsubmissions = QpSubmission.objects.filter(active_flag=1).annotate(semester_name=F('semester__semester_name'),
																			batch_name=F('batch__batch_name'), 
																			course_info=Concat('course_code', Value(' - '), 'course_name'), 
																			faculty_id_cancatenate = Concat('faculty_email_id', Value(' : '), 
																					'email_access_id_1',Value(' : '),
																					 'email_access_id_2', output_field=CharField()),
																			exam_type_info=F('exam_type__exam_type'))
		if data.get('semester_name'):
			qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
		if data.get('program_type'):
			qpsubmissions = qpsubmissions.filter(program_type=data.get('program_type'))
		if data.get('batch_name'):
			qpsubmissions = qpsubmissions.filter(batch__batch_name=data.get('batch_name'))
		if data.get('faculty_id'):
			qpsubmissions = qpsubmissions.filter(faculty_email_id=data.get('faculty_id'))
		if data.get('exam_type_name'):
			qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
		if data.get('exam_slot'):
			qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))
		if data.get('filter-qp2'):
			qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=True)| Q(qp_path__exact=''),Q(alternate_qp_path__isnull=True)| Q(alternate_qp_path__exact=''))| Q(rejected_flag=1))

		return qpsubmissions

	def get_table(self, data):
		return get_submission_status_table(data)(self.get_submission_list(data))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		table = self.get_table(self.request.GET)
		context['table'] = table
		context['query_params'] = 'filter-qp2' if self.request.GET.get('filter-qp2') else ''
		if 'report_async' in self.request.GET:
			if 'async_email' == self.request.GET['report_async']:
				qpsubmissions = QpSubmission.objects.filter(active_flag=1)
				data = self.request.GET
				if data.get('semester_name'):
					qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
				if data.get('program_type'):
					qpsubmissions = qpsubmissions.filter(program_type=data.get('program_type'))
				if data.get('batch_name'):
					qpsubmissions = qpsubmissions.filter(batch__batch_name=data.get('batch_name'))
				if data.get('faculty_id'):
					qpsubmissions = qpsubmissions.filter(faculty_email_id=data.get('faculty_id'))
				if data.get('exam_type_name'):
					qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
				if data.get('exam_slot'):
					qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))
				if data.get('filter-qp2'):
					qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=True)| Q(qp_path__exact=''),Q(alternate_qp_path__isnull=True)| Q(alternate_qp_path__exact=''))| Q(rejected_flag=1))

				qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=True)| Q(qp_path__exact=''),Q(alternate_qp_path__isnull=True)| Q(alternate_qp_path__exact=''))| Q(rejected_flag=1))
				faculty_email_ids = qpsubmissions.values_list('faculty_email_id','email_access_id_1','email_access_id_2')
				if faculty_email_ids:
					job = qp_email_send_async.delay(faculty_email_ids, qpsubmissions)
			
		return context

	def csv_download_view(self):
		response = HttpResponse(content_type="text/csv")
		response['Content-Disposition'] = 'attachment;filename=export.csv'
		writer = csv.writer(response)
		header = ['Semester', 'Batch', 'Course Code and Name', 'Exam Type', 'Submission DateTime', 'Submissions to be Done by','QP Submitted by','Status', 'Upload Locked']
		writer.writerow(header)
		qpsubmissions = QpSubmission.objects.filter(active_flag=1).annotate(semester_name=F('semester__semester_name'),
																			batch_name=F('batch__batch_name'),
																			course_info=Concat('course_code', Value(' - '), 'course_name'), 
																			faculty_id_cancatenate = Concat('faculty_email_id', Value(' : '), 
																			'email_access_id_1',Value(' : '),
																			'email_access_id_2', output_field=CharField()),
																			exam_type_info=F('exam_type__exam_type'))
		data = self.request.GET
		if data.get('semester_name'):
			qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
		if data.get('program_type'):
			qpsubmissions = qpsubmissions.filter(program_type=data.get('program_type'))
		if data.get('batch_name'):
			qpsubmissions = qpsubmissions.filter(batch__batch_name=data.get('batch_name'))
		if data.get('faculty_id'):
			qpsubmissions = qpsubmissions.filter(faculty_email_id=data.get('faculty_id'))
		if data.get('exam_type_name'):
			qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
		if data.get('exam_slot'):
			qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))
		if data.get('qp_queryparams') and data.get('qp_queryparams')!=['']:
			qpsubmissions = qpsubmissions.filter(Q(qp_path__isnull=True)| Q(qp_path__exact='') | Q(rejected_flag=1))
		if qpsubmissions:
			for i in qpsubmissions:
				status=" "
				if ((i.qp_path and i.last_submitted_datetime) or (i.alternate_qp_path and i.alternate_qp_submit_datetime)) and i.acceptance_flag == False and i.rejected_flag == False:
					status= "Pending Review"
				if ((i.qp_path and i.last_submitted_datetime) or (i.alternate_qp_path and i.alternate_qp_submit_datetime)) and i.acceptance_flag == True and i.last_download_datetime:
					status= "Accepted and Downloaded"
				if ((i.qp_path and i.last_submitted_datetime) or (i.alternate_qp_path and i.alternate_qp_submit_datetime)) and i.acceptance_flag == True and not i.last_download_datetime:
					status= "Accepted"
				if ((i.qp_path and i.last_submitted_datetime) or (i.alternate_qp_path and i.alternate_qp_submit_datetime)) and i.rejected_flag==True:
					status= "Sent for Resubmission"
				if (i.qp_path==None or i.qp_path=='') and (i.alternate_qp_path==None or i.alternate_qp_path==''):
					status= "Pending Submission"

				row =[i.semester_name, i.batch_name, i.course_info, i.exam_type_info, i.last_submitted_datetime, 
					' : '.join([x for x in i.faculty_id_cancatenate.split(' : ') if x]),i.submitted_by_faculty,status,
					 i.submission_locked_flag]
				writer.writerow(row)
		return response



	def get(self, request, *args, **kwargs):
		if 'report_csv' in request.GET:
			return self.csv_download_view()

		return super(QPSubmissionStatusView, self).get(request, *args, **kwargs)

class QPSubmissionStatusAjaxView(QPMUserPermissionMixin,FeedDataView):
	token = get_submission_status_table().token

	def get_queryset(self):

		qpsubmissions = QpSubmission.objects.filter(active_flag=1).annotate(semester_name=F('semester__semester_name'),
			batch_name=F('batch__batch_name'), 
			course_info=Concat('course_code', Value(' - '), 'course_name'),
			faculty_id_cancatenate = Concat('faculty_email_id', Value(' : '), 
							'email_access_id_1',Value(' : '), 'email_access_id_2', output_field=CharField()),
			 exam_type_info=F('exam_type__exam_type'))
		if self.kwargs.get('data') != 'n':
			data = ast.literal_eval(self.kwargs.get('data'))
			if data.get('semester_name'):
				qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
			if data.get('program_type'):
				qpsubmissions = qpsubmissions.filter(program_type=data.get('program_type'))
			if data.get('batch_name'):
				qpsubmissions = qpsubmissions.filter(batch__batch_name=data.get('batch_name'))
			if data.get('faculty_id'):
				qpsubmissions = qpsubmissions.filter(faculty_email_id=data.get('faculty_id'))
			if data.get('exam_type_name'):
				qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
			if data.get('exam_slot'):
				qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))
			if data.get('filter-qp2'):
				qpsubmissions = qpsubmissions.filter(Q(Q(qp_path__isnull=True)| Q(qp_path__exact=''),Q(alternate_qp_path__isnull=True)| Q(alternate_qp_path__exact=''))| Q(rejected_flag=1))

		return qpsubmissions

class QPPathViewDetailsView(QPMUserPermissionMixin,FormView):
	template_name = 'administrator/view_qp_path_view_details.html'
	form_class = AcceptRejectForm

	def form_invalid(self, form):
		return self.render_to_response(self.get_context_data(form=form))

	def get_form_kwargs(self):
		kwargs = super(QPPathViewDetailsView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def get_initial(self):
		initial = super().get_initial()
		uploaded_data = QpSubmission.objects.get(id=self.kwargs['pk'])
		initial['submission_locked_flag'] = uploaded_data.submission_locked_flag
		initial['acceptance_flag'] = uploaded_data.acceptance_flag	
		initial['rejected_flag'] = uploaded_data.rejected_flag	
		initial['rejection_comments'] = uploaded_data.rejection_comments
		return initial

	def form_valid(self, form):
		faculty_qp_data =  QpSubmission.objects.get(id = self.kwargs['pk'])
		if form.cleaned_data['alternate_qp_path']:
			#To delete Previous file from storage
			faculty_qp_data.alternate_qp_path.delete()
			if faculty_qp_data.first_submitted_datetime is None and faculty_qp_data.last_submitted_datetime is None:
				faculty_qp_data.first_submitted_datetime = timezone.now()
				faculty_qp_data.last_submitted_datetime = timezone.now()

			faculty_qp_data.alternate_qp_path = form.cleaned_data['alternate_qp_path']
			faculty_qp_data.alternate_qp_submit_datetime = timezone.now()
			faculty_qp_data.submitted_by_faculty = self.request.user.email

		if form.cleaned_data['acceptance_flag']:
			faculty_qp_data.acceptance_flag = form.cleaned_data['acceptance_flag']
			faculty_qp_data.rejected_flag = False
			faculty_qp_data.submission_locked_flag = True
			faculty_qp_data.rejection_comments = ''
			faculty_qp_data.accepted_datetime = timezone.now()
		if form.cleaned_data['rejected_flag']:
			faculty_qp_data.rejected_flag = form.cleaned_data['rejected_flag']
			faculty_qp_data.acceptance_flag = False
			faculty_qp_data.rejected_datetime = timezone.now()
			faculty_qp_data.rejection_comments = form.cleaned_data['rejection_comments']

		faculty_qp_data.save()

		if form.cleaned_data['acceptance_flag']:
			message = '''Greetings Faculty,\nThe Question Paper submitted for the course({0}-{1}) has been accepted by the Instruction Cell. They will be using the same for conduct of the upcoming exam. Further changes to the Question Paper won't be allowed now. If you need to change the question paper submitted, please contact the Instruction Cell ASAP. \n\nRegards, \nWILP Instruction Team'''.format(faculty_qp_data.course_code, faculty_qp_data.course_name)
			email_send = send_email_fac.delay(message, faculty_qp_data)
		if form.cleaned_data['rejected_flag']:
			message = '''Greetings Faculty,\nThe Question Paper submitted for the course({0}-{1}) has been sent back for review for the reasons – {2}. Please re-upload the updated question paper ASAP.\n\nRegards, \nWILP Instruction Cell'''.format(faculty_qp_data.course_code, faculty_qp_data.course_name, faculty_qp_data.rejection_comments)
			email_send = send_email_fac.delay(message, faculty_qp_data)

		url = reverse_lazy('administrator:qp_path_view_details',
						kwargs={'pk': faculty_qp_data.pk,}
				)
		messages.success(self.request, _('We have successfully made changes for QP,Thanks'))
		return redirect(url)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		query = QpSubmission.objects.get(id = self.kwargs['pk'])
		context["query"] = query
		if query.qp_path:
			if self.request.is_secure():
				context['qp_path']= "https://"+self.request.META['HTTP_HOST'] + reverse_lazy('administrator:document-view',kwargs={'pk':query.id,'storage_path':'qp_path'})
			else:
				context['qp_path']= "http://"+self.request.META['HTTP_HOST'] + reverse_lazy('administrator:document-view',kwargs={'pk':query.id,'storage_path':'qp_path'})


		if query.alternate_qp_path:
			if self.request.is_secure():
				context['qp_alternate_path']= "https://"+self.request.META['HTTP_HOST'] + reverse_lazy('administrator:document-view',kwargs={'pk':query.id,'storage_path':'alternate_qp_path'})
			else:
				context['qp_alternate_path']= "http://"+self.request.META['HTTP_HOST'] + reverse_lazy('administrator:document-view',kwargs={'pk':query.id,'storage_path':'alternate_qp_path'})

			context['qp_alternate_path_name'] = query.semester.semester_name+'_'+query.batch.batch_name+'_'+query.course_code+'_'\
										+query.course_name+'_'+query.exam_type.exam_type+'_'+query.exam_slot.slot_name\
										+'_INSTR'+os.path.splitext(query.alternate_qp_path.name)[1]

		try:
			context['faculty_name'] = User.objects.get(email = query.faculty_email_id ).username
		except:
			context['faculty_name'] = ''
		# document_name = query.qp_path.name.split("/")
		# del document_name[0]
		# context['qp_path_name'] = "".join(document_name)
		context['qp_path_name'] = query.semester.semester_name+'_'+query.batch.batch_name+'_'+query.course_code+'_'\
										+query.course_name+'_'+query.exam_type.exam_type+'_'+query.exam_slot.slot_name\
										+os.path.splitext(query.qp_path.name)[1]
		return context

	def get(self, request, *args, **kwargs):
		return super(QPPathViewDetailsView, self).get(request, *args, **kwargs)


def multi_download_ajax_view(request):
	if request.is_ajax():
		if request.GET.get('job')=='':
			doc_uuid = uuid.uuid4().hex
			if not os.path.exists('/tmp/{}/documents/'.format(doc_uuid)):
				os.makedirs('/tmp/{}/documents/'.format(doc_uuid))

			qpsubmissions = QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).annotate(semester_name=F('semester__semester_name'),batch_name=F('batch__batch_name'), course_info=Concat('course_code', Value(' - '), 'course_name'), exam_type_name=F('exam_type__exam_type'))
			if request.GET.get('semester_name'):
				qpsubmissions = qpsubmissions.filter(semester__semester_name=request.GET.get('semester_name'))
			if request.GET.get('program_type'):
				qpsubmissions = qpsubmissions.filter(program_type=request.GET.get('program_type'))
			if request.GET.get('batch_name'):
				qpsubmissions = qpsubmissions.filter(batch__batch_name=request.GET.get('batch_name'))
			if request.GET.get('faculty_id'):
				qpsubmissions = qpsubmissions.filter(faculty_email_id=request.GET.get('faculty_id'))
			if request.GET.get('exam_type_name'):
				qpsubmissions = qpsubmissions.filter(exam_type__exam_type=request.GET.get('exam_type_name'))
			if request.GET.get('exam_slot'):
				qpsubmissions = qpsubmissions.filter(exam_slot=request.GET.get('exam_slot'))
			if request.GET.get('date'):
				qpsubmissions = qpsubmissions.filter(last_submitted_datetime__gte =parse_datetime(request.GET.get('date')))
			if request.GET.get('search'):
				qpsubmissions = qpsubmissions.filter(Q(course_info__icontains=request.GET.get('search'))|Q(faculty_email_id__icontains=request.GET.get('search')))

			check_box=None
			if request.GET.get('checkbox1') =='true':
				check_box='only_instr'

			if request.GET.get('checkbox2') =='true':
				check_box='both_qp_and_alternate_qp'

			if qpsubmissions.count()>=1:
				job = admin_multiple_file_download.delay(filelist=qpsubmissions,doc_uuid=doc_uuid,
														email=request.user.email,check_box=check_box)
				return JsonResponse({'Job_created':True,'job_id':job.id,'doc_uuid':doc_uuid,'no_files':qpsubmissions.count()})
			else:
				return JsonResponse({'no_files':qpsubmissions.count()})
		else:
			if 'job' in request.GET:
				job_id = request.GET['job']
			else:
				return JsonResponse({'message':None,'status':'FAILURE'})
			job = AsyncResult(job_id)

			try :
				message = job.result
			except :
				message ='processing...'

			print('Message............',message)
			if job.status == 'SUCCESS':
				job.revoke()
				return JsonResponse({'message':None,'status':'SUCCESS'})
			else:

				return JsonResponse({'message':'Pending','status':'FAILURE','exception_error_msg':str(message)})


def multidocdownloadview(request):
	doc_uuid = request.GET.get('doc_uuid')
	response = HttpResponse(open('/tmp/{}/documents.zip'.format(doc_uuid), 'rb').read())
	response ['content_type']='application/zip'
	response['Content-Disposition'] = 'attachment; filename=files.zip'
	shutil.rmtree('/tmp/{}/'.format(doc_uuid))
	return response


@method_decorator([never_cache], name='dispatch')
class QPSubmissionsDownloadView(QPMUserPermissionMixin,FormView):
	template_name = 'administrator/view_qp_submissions_download.html'
	form_class = QPSubmissionsDownloadForm

	def get_form_kwargs(self):
		kwargs = super(QPSubmissionsDownloadView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def get_initial(self):
		self.initial['semester_name'] = self.request.GET.get('semester_name')
		self.initial['program_type'] = self.request.GET.get('program_type')
		self.initial['batch_name'] = self.request.GET.get('batch_name')
		self.initial['faculty_id'] = self.request.GET.get('faculty_id')
		self.initial['exam_type_name'] = self.request.GET.get('exam_type_name')
		self.initial['exam_slot'] = self.request.GET.get('exam_slot')
		self.initial['date'] = self.request.GET.get('date')

		return self.initial

	def get_qp_download_list(self, data):

		qpsubmissions = QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).annotate(semester_name=F('semester__semester_name'),batch_name=F('batch__batch_name'), course_info=Concat('course_code', Value(' - '), 'course_name'), exam_type_name=F('exam_type__exam_type'))
		if data.get('semester_name'):
			qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
		if data.get('program_type'):
			qpsubmissions = qpsubmissions.filter(program_type=data.get('program_type'))
		if data.get('batch_name'):
			qpsubmissions = qpsubmissions.filter(batch__batch_name=data.get('batch_name'))
		if data.get('faculty_id'):
			qpsubmissions = qpsubmissions.filter(faculty_email_id=data.get('faculty_id'))
		if data.get('exam_type_name'):
			qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
		if data.get('exam_slot'):
			qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))
		if data.get('date'):
			qpsubmissions = qpsubmissions.filter(last_submitted_datetime__gte =parse_datetime(data.get('date')))
		if data.get('search'):
			qpsubmissions = qpsubmissions.filter(Q(course_info__icontains=data.get('search'))|Q(faculty_email_id__icontains=data.get('search')))
		return qpsubmissions

	def get_qp_download_table(self, data):
		return get_qp_submissions_download_table(data)(self.get_qp_download_list(data))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		table = self.get_qp_download_table(self.request.GET)
		context['table'] = table
		return context

	def get(self, request, *args, **kwargs):
		if request.GET.get('file_download'):
			filelist = self.get_qp_download_list(self.request.GET)
			byte_data = BytesIO()
			zip_file = zipfile.ZipFile(byte_data, "w")

			check_box=None
			if self.request.GET.get('chckbox1')=='chckbox1':
				check_box='only_instr'

			if self.request.GET.get('chckbox2')=='chckbox2':
				check_box='both_qp_and_alternate_qp'

			if check_box=='only_instr':
				for file in filelist:
					if file.alternate_qp_path.name:
						filename = settings.MEDIA_ROOT + '/' + file.alternate_qp_path.name
						file.last_download_datetime = timezone.now()
						file.downloaded_by = self.request.user.email
						zip_file.write(filename,file.alternate_qp_path.name)
						file.save()
			elif check_box == 'both_qp_and_alternate_qp':
				for file in filelist:
					if file.qp_path.name:
						filename = settings.MEDIA_ROOT + '/' + file.qp_path.name
						file.last_download_datetime = timezone.now()
						file.downloaded_by = self.request.user.email
						zip_file.write(filename,file.qp_path.name)
						file.save()

				for file in filelist:
					if file.alternate_qp_path.name:
						filename = settings.MEDIA_ROOT + '/' + file.alternate_qp_path.name
						file.last_download_datetime = timezone.now()
						file.downloaded_by = self.request.user.email
						zip_file.write(filename,file.alternate_qp_path.name)
						file.save()
			else:
				for file in filelist:
					if file.qp_path.name:
						filename = settings.MEDIA_ROOT + '/' + file.qp_path.name
						file.last_download_datetime = timezone.now()
						file.downloaded_by = self.request.user.email
						zip_file.write(filename,file.qp_path.name)
						file.save()
			zip_file.close()

			response = HttpResponse(byte_data.getvalue(), content_type='application/zip')
			response['Content-Disposition'] = 'attachment; filename=files.zip'
			return response
		return super(QPSubmissionsDownloadView, self).get(request, *args, **kwargs)

class QPSubmissionsDownloadAjaxView(QPMUserPermissionMixin,FeedDataView):
	token = get_qp_submissions_download_table().token

	def get_queryset(self):
		qpsubmissions = QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).annotate(semester_name=F('semester__semester_name'),batch_name=F('batch__batch_name'), course_info=Concat('course_code', Value(' - '), 'course_name'), exam_type_name=F('exam_type__exam_type'))
		if self.kwargs.get('data') != 'n':
			data = ast.literal_eval(self.kwargs.get('data'))
			
			if data.get('semester_name'):
				qpsubmissions = qpsubmissions.filter(semester__semester_name=data.get('semester_name'))
			if data.get('program_type'):
				qpsubmissions = qpsubmissions.filter(program_type=data.get('program_type'))
			if data.get('batch_name'):
				qpsubmissions = qpsubmissions.filter(batch__batch_name=data.get('batch_name'))
			if data.get('faculty_id'):
				qpsubmissions = qpsubmissions.filter(faculty_email_id=data.get('faculty_id'))
			if data.get('exam_type_name'):
				qpsubmissions = qpsubmissions.filter(exam_type__exam_type=data.get('exam_type_name'))
			if data.get('exam_slot'):
				qpsubmissions = qpsubmissions.filter(exam_slot=data.get('exam_slot'))
			if data.get('date'):
				qpsubmissions = qpsubmissions.filter(last_submitted_datetime__gte =parse_datetime(data.get('date')))
		return qpsubmissions


from master.views import UserFileViewDownload

class adminUserFileViewDownload(UserFileViewDownload):
	def get_application_document(self, request, pk):
		if request.user.is_superuser or request.user.is_staff:
			return QpSubmission.objects.get(pk=pk)
		else:
			return None


class SyncEMAExamtype(APIView):
	def post(self, request, *args, **kwargs):
		try:
			if 'pre_exam_type' in request.data:
				a = ExamType.objects.get(exam_type=request.data['pre_exam_type'], evaluation_type=request.data['pre_evaluation_type'])
				if str(a.exam_type) != request.data['exam_type'] or str(a.evaluation_type) != request.data['evaluation_type']:
					if str(a.exam_type) != request.data['exam_type']:
						a.exam_type = request.data['exam_type']
					if str(a.evaluation_type)!= request.data['evaluation_type']:
						a.evaluation_type = request.data['evaluation_type']
					a.save()
					return Response(request.data, status=status.HTTP_200_OK)

			ExamType.objects.get(exam_type=request.data['exam_type'], evaluation_type=request.data['evaluation_type'])
			return Response(request.data, status=status.HTTP_200_OK)
		except:
			if 'pre_exam_type' in request.data:
				a = ExamType.objects.filter(exam_type=request.data['pre_exam_type'], evaluation_type__isnull=True)
				if a:
					if str(a[0].exam_type) != request.data['exam_type'] or str(a[0].evaluation_type) != request.data['evaluation_type']:
						if str(a[0].exam_type) != request.data['exam_type']:
							a[0].exam_type = request.data['exam_type']
						if str(a[0].evaluation_type)!= request.data['evaluation_type']:
							a[0].evaluation_type = request.data['evaluation_type']
						a[0].save()
						return Response(request.data, status=status.HTTP_200_OK)
			a = ExamType.objects.filter(exam_type=request.data['exam_type'], evaluation_type__isnull=True)
			if a:
				if str(a[0].evaluation_type)!= request.data['evaluation_type']:
					a[0].evaluation_type = request.data['evaluation_type']
					a[0].save()
					return Response(request.data, status=status.HTTP_200_OK)

			ExamType.objects.create(exam_type=request.data['exam_type'], evaluation_type=request.data['evaluation_type'])
			return Response(request.data, status=status.HTTP_201_CREATED)

	def delete(self, request, *args, **kwargs):
		try:
			a = ExamType.objects.get(exam_type=request.data['exam_type'], evaluation_type=request.data['evaluation_type'])
			a.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		except:
			a = ExamType.objects.filter(exam_type=request.data['exam_type'], evaluation_type__isnull=True)
			if a:
				a[0].delete()
				return Response(status=status.HTTP_204_NO_CONTENT)
			return Response("Given exam type is not yet created")


class SyncEMABatch(APIView):
	def post(self, request, *args, **kwargs):
		try:
			if 'pre_batch_name' in request.data:
				a = Batch.objects.get(batch_name=request.data['pre_batch_name'])
				if str(a.batch_name) != request.data['batch_name'] or str(a.year) != request.data['year'] or str(a.sem_number) != request.data['sem_number']:
					if str(a.batch_name) != request.data['batch_name']:
						a.batch_name = request.data['batch_name']
					if str(a.year)!= request.data['year']:
						a.year = request.data['year']
					if str(a.sem_number) != request.data['sem_number']:
						a.sem_number = request.data['sem_number']
					a.save()
					return Response(request.data, status=status.HTTP_200_OK)

			b = Batch.objects.get(batch_name=request.data['batch_name'])
			if b:
				if str(b.year) != request.data['year'] or str(b.sem_number) != request.data['sem_number']:
					if str(b.year)!= request.data['year']:
						b.year = request.data['year']
					if str(b.sem_number) != request.data['sem_number']:
						b.sem_number = request.data['sem_number']
					b.save()
					return Response(request.data, status=status.HTTP_200_OK)

			return Response(request.data, status=status.HTTP_200_OK)
		except:
			Batch.objects.create(batch_name=request.data['batch_name'], year=request.data['year'], sem_number=request.data['sem_number'])
			return Response(request.data, status=status.HTTP_201_CREATED)

	def delete(self, request, *args, **kwargs):
		try:
			a = Batch.objects.get(batch_name=request.data['batch_name'])
			a.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		except:
			return Response("Given batch is not yet created")


class SyncEMASemester(APIView):
	def post(self, request, *args, **kwargs):
		try:
			if 'pre_semester_name' in request.data:
				a = Semester.objects.get(semester_name=request.data['pre_semester_name'])
				if str(a.semester_name) != request.data['semester_name']:
					a.semester_name= request.data['semester_name']
					a.save()
					return Response(request.data, status=status.HTTP_200_OK)

			Semester.objects.get(semester_name=request.data['semester_name'])
			return Response(request.data, status=status.HTTP_200_OK)
		except:
			Semester.objects.create(semester_name=request.data['semester_name'])
			return Response(request.data, status=status.HTTP_201_CREATED)

	def delete(self, request, *args, **kwargs):
		try:
			a = Semester.objects.get(semester_name=request.data['semester_name'])
			a.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		except:
			return Response("Given Semester is not yet created")


class SyncEMAExamSlot(APIView):
	def post(self, request, *args, **kwargs):
		try:
			if 'pre_slot_name' in request.data:
				a = ExamSlot.objects.get(slot_name=request.data['pre_slot_name'])
				if str(a.slot_name) != request.data['slot_name'] or str(a.slot_date) != request.data['slot_date'] or str(a.slot_day) != request.data['slot_day'] or str(a.slot_start_time) != request.data['slot_start_time']:
					if str(a.slot_name) != request.data['slot_name']:
						a.slot_name = request.data['slot_name']
					if str(a.slot_date)!= request.data['slot_date']:
						a.slot_date = request.data['slot_date']
					if str(a.slot_day) != request.data['slot_day']:
						a.slot_day = request.data['slot_day']
					if str(a.slot_start_time) != request.data['slot_start_time']:
						a.slot_start_time = request.data['slot_start_time']
					a.save()
					return Response(request.data, status=status.HTTP_200_OK)
			b = ExamSlot.objects.get(slot_name=request.data['slot_name'])
			if b:
				if str(b.slot_date) != request.data['slot_date'] or str(b.slot_day) != request.data['slot_day'] or str(b.slot_start_time) != request.data['slot_start_time']:
					if str(b.slot_date)!= request.data['slot_date']:
						b.slot_date = request.data['slot_date']
					if str(b.slot_day) != request.data['slot_day']:
						b.slot_day = request.data['slot_day']
					if str(b.slot_start_time) != request.data['slot_start_time']:
						b.slot_start_time = request.data['slot_start_time']
					b.save()
					return Response(request.data, status=status.HTTP_200_OK)

			return Response(request.data, status=status.HTTP_200_OK)
		except:
			ExamSlot.objects.create(slot_name=request.data['slot_name'], slot_date=request.data['slot_date'], slot_day=request.data['slot_day'], slot_start_time=request.data['slot_start_time'])
			return Response(request.data, status=status.HTTP_201_CREATED)

	def delete(self, request, *args, **kwargs):
		try:
			a = ExamSlot.objects.get(slot_name=request.data['slot_name'])
			a.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		except:
			return Response("Given ExamSlot is not yet created")


class ManageQPLockUnlockView(FormView):
	template_name = 'administrator/manage_qp_lock_unlock.html'
	form_class = ManageQpLockUnlockForm

	def get_success_url(self):
		return self.request.path_info

	def get_filtered_data(self, form, query):
		if form.cleaned_data['program_type']:
			query = query.filter(program_type=form.cleaned_data['program_type'])
		if form.cleaned_data['semester_name'] and not form.cleaned_data['program_type'] == 'CERTIFICATION':
			query = query.filter(semester=form.cleaned_data['semester_name'])
		if form.cleaned_data['batch_name']:
			query = query.filter(batch=form.cleaned_data['batch_name'])
		if form.cleaned_data['exam_type']:
			query = query.filter(exam_type=form.cleaned_data['exam_type'])
		if form.cleaned_data['exam_slot']:
			query = query.filter(exam_slot=form.cleaned_data['exam_slot'])
		if form.cleaned_data['course_code']:
			query = query.filter(course_code=form.cleaned_data['course_code'].split(' ')[0])

		return query

	def form_valid(self, form):
		if 'inactive_qp_flag_button' in self.request.POST:
			query = QpSubmission.objects.all()
			filtered_query = self.get_filtered_data(form, query)
			entries = filtered_query.filter(active_flag=True).update(active_flag=False)
			button = 'inactive_qp_flag_button'

		if 'active_qp_flag_button' in self.request.POST:
			query = QpSubmission.objects.all()
			filtered_query = self.get_filtered_data(form, query)
			entries = filtered_query.filter(active_flag=False).update(active_flag=True)
			button = 'active_qp_flag_button'

		return self.render_to_response(self.get_context_data(modified_entries=entries, button=button))

	def form_invalid(self, form):
		return super().form_invalid(form)

	def get_context_data(self, **kwargs):
		context  = super().get_context_data(**kwargs)
		context['modified_entries'] = kwargs.get('modified_entries') if kwargs else None
		context['button'] = kwargs.get('button') if kwargs else None
		return context

def get_course_detail(request):
	if request.is_ajax():
		x = request.GET.get('sid')
		qp = QpSubmission.objects.get(id=x)
		return JsonResponse({'course': qp.course_code+" "+qp.course_name, })
