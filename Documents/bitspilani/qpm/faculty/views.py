from django.views.generic import View,FormView,TemplateView,UpdateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, FileResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import Concat, Substr
from django.db.models import (Max, Q, Case, When, F, Value, TextField, CharField, IntegerField, BooleanField)
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from django.conf import settings
from table.views import FeedDataView
import json
import ast
from .tasks import *
from .forms import *
from .tables import *
from .permissions import *


class Base_fac_Home(FormView):
	template_name = 'faculty/home.html'
	form_class = QpfacultysubmissionForm

	def get_success_url(self):
		return reverse_lazy(
			'faculty:qp_submission_status',
		)

	def get_form_kwargs(self):
		kwargs = super(Base_fac_Home, self).get_form_kwargs()
		kwargs['request'] = self.request
		return kwargs

	def form_invalid(self, form):
		return self.render_to_response(self.get_context_data(form=form))


	def form_valid(self, form):
		faculty_qp_data = QpSubmission.objects.get(semester=form.cleaned_data['semester'],
														batch = form.cleaned_data['batch'],
														course_code = form.cleaned_data['course_code'],
														exam_type = form.cleaned_data['exam_type'],)
		#To delete Previous file from storage
		faculty_qp_data.qp_path.delete()
		if faculty_qp_data.alternate_qp_path:
			faculty_qp_data.alternate_qp_path.delete()
			faculty_qp_data.alternate_qp_submit_datetime = None

			#send Email
			message = '''Greetings,\nThe instructor for the course({0}-{1}) has updated the qp file. Hence the file uploaded by you has been removed. Please check the submission again and re-upload your file if required. \n\nRegards, \nWILP Instruction Team'''.format(faculty_qp_data.course_code, faculty_qp_data.course_name)
			email_send = send_email_from_fac_to_instr.delay(message)



		faculty_qp_data.qp_path = form.cleaned_data['qp_path']
		faculty_qp_data.qp_guidelines_flag = True
		faculty_qp_data.qp_correct_flag = True
		faculty_qp_data.acceptance_flag = False
		faculty_qp_data.rejected_flag = False
		faculty_qp_data.rejection_comments = ''
		faculty_qp_data.submitted_by_faculty=self.request.user.email
		if faculty_qp_data.first_submitted_datetime:
			faculty_qp_data.last_submitted_datetime = timezone.now()
		else:
			faculty_qp_data.first_submitted_datetime = timezone.now()
			faculty_qp_data.last_submitted_datetime = timezone.now()
		faculty_qp_data.save()
		if self.request.resolver_match.app_name =="coordinator":
			url = reverse_lazy('coordinator:qp_update',
						kwargs={'pk': faculty_qp_data.pk,}
				)
		else:
			url = reverse_lazy('faculty:qp_update',
						kwargs={'pk': faculty_qp_data.pk,}
				)
		messages.success(self.request, _('Question Paper file Successfully uploaded'))
		return redirect(url)

	def get_context_data(self, *args, **kwargs):
		context = super(Base_fac_Home, self).get_context_data(*args, **kwargs)
		context['form'] = self.get_form()
		return context


class Base_fac_qp_update(FormView):
	template_name = 'faculty/Update_QP.html'
	form_class = QpfacultysubmissionForm

	def get_form_kwargs(self):
		kwargs = super(Base_fac_qp_update, self).get_form_kwargs()
		kwargs['request'] = self.request
		return kwargs
	
	def form_invalid(self, form):
		return self.render_to_response(self.get_context_data(form=form))

	def form_valid(self, form):
		faculty_qp_data = QpSubmission.objects.get(semester=form.cleaned_data['semester'],
														batch = form.cleaned_data['batch'],
														course_code = form.cleaned_data['course_code'],
														exam_type = form.cleaned_data['exam_type'],)
		#To delete Previous file from storage
		faculty_qp_data.qp_path.delete()
		if faculty_qp_data.alternate_qp_path:
			faculty_qp_data.alternate_qp_path.delete()
			faculty_qp_data.alternate_qp_submit_datetime = None

			#send Email
			message = '''Greetings,\nThe instructor for the course({0}-{1}) has updated the qp file. Hence the file uploaded by you has been removed. Please check the submission again and re-upload your file if required. \n\nRegards, \nWILP Instruction Team'''.format(faculty_qp_data.course_code, faculty_qp_data.course_name)
			email_send = send_email_from_fac_to_instr.delay(message)

		faculty_qp_data.qp_path.delete()
		faculty_qp_data.qp_path = form.cleaned_data['qp_path']
		faculty_qp_data.qp_guidelines_flag = True
		faculty_qp_data.qp_correct_flag = True
		faculty_qp_data.acceptance_flag = False
		faculty_qp_data.rejected_flag = False
		faculty_qp_data.rejection_comments = ''
		faculty_qp_data.submitted_by_faculty=self.request.user.email
		if faculty_qp_data.first_submitted_datetime:
			faculty_qp_data.last_submitted_datetime = timezone.now()
		else:
			faculty_qp_data.first_submitted_datetime = timezone.now()
			faculty_qp_data.last_submitted_datetime = timezone.now()
		faculty_qp_data.save()

		if self.request.resolver_match.app_name =="coordinator":
			url = reverse_lazy('coordinator:qp_update',
						kwargs={'pk': faculty_qp_data.pk,}
				)
		else:
			url = reverse_lazy('faculty:qp_update',
						kwargs={'pk': faculty_qp_data.pk,}
				)
		messages.success(self.request, _('Question Paper file Successfully uploaded'))
		return redirect(url)

	def get_initial(self):
		initial = super().get_initial()
		uploaded_data = QpSubmission.objects.get(id=self.kwargs['pk'])
		initial['semester'] = uploaded_data.semester
		initial['batch'] = uploaded_data.batch
		initial['course_code'] = uploaded_data.course_code
		initial['exam_type'] = uploaded_data.exam_type	
		initial['exam_slot'] = uploaded_data.exam_slot
		initial['qp_guidelines_flag'] = uploaded_data.qp_guidelines_flag	
		initial['qp_correct_flag'] = uploaded_data.qp_correct_flag	
		initial['qp_path'] = uploaded_data.qp_path
		initial['acceptance_flag'] = uploaded_data.acceptance_flag if uploaded_data.acceptance_flag  else None
		return initial


class Base_fac_qp_submision_status(TemplateView):
	template_name = 'faculty/view_qp_submission_status.html'

	def get_submission_list(self, data):
		query = QpSubmission.objects.filter((Q(faculty_email_id=self.request.user.email)|
												Q(email_access_id_1=self.request.user.email)|
												Q(email_access_id_2=self.request.user.email))
												,active_flag=True,).annotate(exam_type_info=F('exam_type__exam_type')).order_by('-last_submitted_datetime')
		return query

	def get_table(self, data):
		return faculty_Qp_submissions(data)(self.get_submission_list(data))

	def get_context_data(self, *args, **kwargs):
		context = super(Base_fac_qp_submision_status,self).get_context_data(*args, **kwargs)
		data={}
		data['faculty_email_id'] = self.request.user.email
		context['table'] = self.get_table(data)
		return context

class Home(QPMUserPermissionMixin,Base_fac_Home):
	pass

class qp_update(QPMUserPermissionMixin,Base_fac_qp_update):
	pass

class qp_submision_status(QPMUserPermissionMixin,Base_fac_qp_submision_status):
	pass

class FacQPSubmissionStatusAjaxView(FeedDataView):
	token = faculty_Qp_submissions().token

	def get_queryset(self):
		if self.kwargs.get('data') != 'n':
			data = ast.literal_eval(self.kwargs.get('data'))
			
			query = QpSubmission.objects.filter((Q(faculty_email_id=data['faculty_email_id'])|
												Q(email_access_id_1=data['faculty_email_id'])|
												Q(email_access_id_2=data['faculty_email_id'])
												),active_flag=True,).annotate(exam_type_info=F('exam_type__exam_type'))
		
		else:
			query = QpSubmission.objects.none()

		return query


class semester_drop_down(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			query = QpSubmission.objects.filter((Q(faculty_email_id=self.request.user.email)|
												Q(email_access_id_1=self.request.user.email)|
												Q(email_access_id_2=self.request.user.email)),
												active_flag=True,).exclude(acceptance_flag=True)\
												.annotate(course_code_name=Concat('course_code', Value(' - '), 'course_name'))

			if request.GET.get('semester',None):
				query = query.filter(semester = request.GET.get('semester',None))

			if request.GET.get('batch',None):
				query = query.filter(batch = request.GET.get('batch',None))

			context = {}
			context['program_type'] = query[0].program_type if len(query)==1 else None
			context['batch'] = json.dumps(list(Batch.objects.filter(id__in=query.values_list('batch', flat=True).distinct()).values('id','batch_name')), cls=DjangoJSONEncoder)
			context['course_form'] = json.dumps(list(query.values('course_code','course_code_name')), cls=DjangoJSONEncoder)
			context['exam_type_form'] = json.dumps(list(ExamType.objects.filter(id__in=query.values_list('exam_type', flat=True).distinct()).values('id','exam_type')), cls=DjangoJSONEncoder)
			return JsonResponse(context)


class batch_drop_down(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			query = QpSubmission.objects.filter((Q(faculty_email_id=self.request.user.email)|
												Q(email_access_id_1=self.request.user.email)|
												Q(email_access_id_2=self.request.user.email)),
												semester = request.GET.get('semester'),
												batch = request.GET.get('batch'),
												active_flag=True,).exclude(acceptance_flag=True)\
												.annotate(course_code_name=Concat('course_code', Value(' - '), 'course_name'))

			if request.GET.get('semester',None):
				query = query.filter(semester = request.GET.get('semester',None))

			if request.GET.get('batch',None):
				query = query.filter(batch = request.GET.get('batch',None))

			context = {}
			data = [{'course_code': distinct_course.course_code, 'course_name': distinct_course.course_name.upper(),'course_code_name': distinct_course.course_code_name.upper()} for distinct_course in query]
			course_data = [dict(t) for t in {tuple(d.items()) for d in data}]
			context['program_type'] = query[0].program_type if len(query)==1 else None
			context['semester'] = json.dumps(list(Semester.objects.filter(id__in=query.values_list('semester', flat=True).distinct()).values('id','semester_name')), cls=DjangoJSONEncoder)
			context['course_form'] = json.dumps(course_data, cls=DjangoJSONEncoder)
			context['exam_type_form'] = json.dumps(list(ExamType.objects.filter(id__in=query.values_list('exam_type', flat=True).distinct()).values('id','exam_type')), cls=DjangoJSONEncoder)
			return JsonResponse(context)



class course_drop_down(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			query = QpSubmission.objects.filter((Q(faculty_email_id=self.request.user.email)|
												Q(email_access_id_1=self.request.user.email)|
												Q(email_access_id_2=self.request.user.email)),
												course_code = request.GET.get('course'),
												semester = request.GET.get('semester'),
												batch = request.GET.get('batch'),
												active_flag=True,).exclude(acceptance_flag=True)\
												.annotate(course_code_name=Concat('course_code', Value(' - '), 'course_name')).order_by('course_code')

			if request.GET.get('semester',None):
				query = query.filter(semester = request.GET.get('semester',None))

			if request.GET.get('batch',None):
				query = query.filter(batch = request.GET.get('batch',None))

			context = {}
			context['exam_type_form'] = json.dumps(list(ExamType.objects.filter(id__in=query.values_list('exam_type', flat=True).distinct()).values('id','exam_type')), cls=DjangoJSONEncoder)
			return JsonResponse(context)


class get_program_examslot(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():

			query = QpSubmission.objects.get((Q(faculty_email_id=self.request.user.email)|
												Q(email_access_id_1=self.request.user.email)|
												Q(email_access_id_2=self.request.user.email)),
												semester=request.GET.get('semester'),
												batch=request.GET.get('batch'),
												course_code=request.GET.get('course_code'),
												exam_type = request.GET.get('examtype'))
			context = {}
			uploaded_data = {}

			if query.qp_path:
				if self.request.is_secure():
					uploaded_data['qp_path']= "https://"+request.META['HTTP_HOST'] + reverse_lazy('faculty:document-view',kwargs={'pk':query.id,'storage_path':'qp_path'})
				else:
					uploaded_data['qp_path']= "http://"+request.META['HTTP_HOST'] + reverse_lazy('faculty:document-view',kwargs={'pk':query.id,'storage_path':'qp_path'})

			if query.alternate_qp_path:
				if self.request.is_secure():
					uploaded_data['qp_alternate_path']= "https://"+request.META['HTTP_HOST'] + reverse_lazy('faculty:document-view',kwargs={'pk':query.id,'storage_path':'alternate_qp_path'})
				else:
					uploaded_data['qp_alternate_path']= "http://"+request.META['HTTP_HOST'] + reverse_lazy('faculty:document-view',kwargs={'pk':query.id,'storage_path':'alternate_qp_path'})

				uploaded_data['qp_alternate_path_name'] = query.semester.semester_name+'_'+query.batch.batch_name+'_'+query.course_code+'_'\
											+query.course_name+'_'+query.exam_type.exam_type+'_'+query.exam_slot.slot_name\
											+'_INSTR'+os.path.splitext(query.alternate_qp_path.name)[1]



			# document_name = query.qp_path.name.split("/")
			# del document_name[0]
			# uploaded_data['qp_path_name'] = "".join(document_name)

			uploaded_data['qp_path_name'] = query.semester.semester_name+'_'+query.batch.batch_name+'_'+query.course_code+'_'\
											+query.course_name+'_'+query.exam_type.exam_type+'_'+query.exam_slot.slot_name\
											+os.path.splitext(query.qp_path.name)[1]

			uploaded_data['last_downloaded']= timezone.localtime(query.last_download_datetime).strftime("%d %B, %Y %I:%M %p") if query.last_download_datetime else None
			uploaded_data['last_submitted_datetime']= timezone.localtime(query.last_submitted_datetime).strftime("%d %B, %Y %I:%M %p") if query.last_submitted_datetime else None
			context['submitted_by_faculty'] = query.submitted_by_faculty
			context['alredy_entry_present'] = json.dumps(uploaded_data,cls=DjangoJSONEncoder)
			context['course_code_name'] = query.course_code +' - '+query.course_name
			context['course_code'] = query.course_code

			exam_slot = QpSubmission.objects.filter(faculty_email_id=request.user.email,active_flag=True,).exclude(acceptance_flag=True,
													semester=request.GET.get('semester'),
													batch=request.GET.get('batch'),
													course_code=request.GET.get('course_code'),
													exam_type = request.GET.get('examtype')).values_list('exam_slot',flat=True)
			

			context['slot_drop_down'] = json.dumps(list(ExamSlot.objects.filter(id__in=exam_slot).values('id','slot_name')), cls=DjangoJSONEncoder)
			context['lock_all_submissions_flag']=SetQpSubmissionsLock.objects.filter(lock_all_submissions_flag=True)[0].lock_all_submissions_flag if SetQpSubmissionsLock.objects.filter(lock_all_submissions_flag=True) else None
			context['program'] = query.program_type
			context['slot_name'] = query.exam_slot.slot_date.strftime("%d %B, %Y")+' - '+query.exam_slot.slot_start_time.strftime("%I:%M %p")
			context['exam_slot_id'] = query.exam_slot.id
			context['submission_locked_flag'] = query.submission_locked_flag

			try:
				SetQpSubmissionsLock_query= SetQpSubmissionsLock.objects.get(semester=request.GET.get('semester')
																			,batch=request.GET.get('batch')
																			,exam_type=request.GET.get('examtype'))
				context['check_for_program_qp_submissions_locks'] = True
			except:
				context['check_for_program_qp_submissions_locks'] = None
			return JsonResponse(context)

from master.views import UserFileViewDownload

class FacultyUserFileViewDownload(UserFileViewDownload):
	def get_application_document(self, request, pk):
		file = QpSubmission.objects.filter((Q(faculty_email_id=self.request.user.email)|
												Q(email_access_id_1=self.request.user.email)|
												Q(email_access_id_2=self.request.user.email)),pk=pk).first()
		if file:
			return file
		else:
			return None
