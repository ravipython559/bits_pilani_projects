from django.http import JsonResponse
from master.models import *
from master.forms.admin_forms import *
from master.forms.forms import *
from django.views.generic import FormView, View
from table.views import FeedDataView
from master.tables import *
from master.utils.extra_models.querysets import *
from functools import reduce
import operator
from datetime import datetime
from django.db.models import F,Value
from django.db.models.functions import Concat
from administrator.tables import APPLCenterSyncLogTable
import json
from django.shortcuts import render

class AttendanceDataAjaxView(FeedDataView):
	token = get_attendance_data_view_table().token

	def get_queryset(self):
		return get_attendance_data_view(
			exam_venue=get_instance_or_none(ExamVenue, pk=self.kwargs.get('venue')),
			location=get_instance_or_none(Location, pk=self.kwargs.get('loc')),
			course=self.kwargs.get('course','n'),
			user_email=self.request.user.email if self.request.user.email else None,
			user_role = None if self.request.user.is_superuser else self.request.user.remoteuser.user_type.user_role,
		)

class HallTicketAttendanceAjaxView(FeedDataView):
	token = get_hallticket_issue_status_table().token
	def get_queryset(self):

		return get_attenlist_halltcktissue(
			program=get_instance_or_none(Program, pk=self.kwargs.get('pg')),
			exam_venue=get_instance_or_none(ExamVenue, pk=self.kwargs.get('venue')),
			location=get_instance_or_none(Location, pk=self.kwargs.get('loc')),
			photo_missing=bool(int(self.kwargs.get('miss', 0))),
		)

class ExamVenueAjax(FormView):
	template_name = "master/ajax/venue_list.html"
	form_class = ExamVenueSlotMapAjaxForm

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'].fields['exam_venue'].queryset = ExamVenue.objects.filter(location=self.location, is_active=True)
		return context

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			self.location = get_instance_or_none(Location, pk=request.GET.get('pk'))
			response = super().get(request, *args, **kwargs)
			return JsonResponse(
				{
					'context':self.render_to_response(response.context_data).render().content.decode(),
				}
			)

class BaseStudentRegistrationAjaxView(FeedDataView):

	def get_filter_queryset(self, filter_params=None):
		filter_exists = reduce(lambda x,y: x or y, map(lambda x:x[1], filter_params.items()), False)	
		sum_filter = filter_exists and reduce(operator.and_, (
				Q(**{k: v}) 
					for (k, v) in filter_params.items() if v is not None
			)
		)

		return self.queryset.filter(sum_filter) if sum_filter else self.queryset

	def get_queryset(self):
		self.queryset = get_student_details()
		filter_dict = {}
		filter_dict['pg_code'] = (self.kwargs.get('pg_code') 
				if self.kwargs.get('pg_code') != 'n' else None
		)
		filter_dict['semester'] = self.kwargs.get('sem') or None

		query = self.get_filter_queryset(filter_params=filter_dict)
		return query

class ExamVenueAddressAjax(FormView):
	template_name = "master/ajax/load_address.html"
	form_class = ExamVenueAddressAjaxForm

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		form = ExamVenueAddressAjaxForm(
			initial={
			'venue_address': self.exam_venue.venue_address if self.exam_venue else '',
			'pin_code':self.exam_venue.pin_code if self.exam_venue else '',
			'student_count_limit':self.exam_venue.student_count_limit if self.exam_venue else '',}
			)
		context['form']=form
		return context

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			self.exam_venue = get_instance_or_none(ExamVenue, pk=request.GET.get('pk_venue'))
			response = super().get(request, *args, **kwargs)
			return JsonResponse(
				{
					'context':self.render_to_response(response.context_data).render().content.decode(),
				}
			)

class CurrentExamAjax(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			program = get_instance_or_none(Program, pk=request.GET.get('pk'))
			return JsonResponse(
				{

					'program': program and program.pk,
					'certification': program and program.program_type == Program.CERTIFICATION,
					'non-specific': program and program.program_type == Program.NON_SPECIFIC,
					'specific': program and program.program_type == Program.SPECIFIC,
					'cluster': program and program.program_type == Program.CLUSTER,
					'others': program and program.program_type == Program.OTHERS,
					'default_semester_pk': Semester.objects.get(semester_name=S.SEMESTER_NAME).pk,
					'default_batch_pk': Batch.objects.get(batch_name=S.BATCH_NAME).pk,
				}
			)


class BaseHallTicketAttendanceAjaxView(FeedDataView):
	pass

class ExamSlotAjax(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			slot_date_str = request.GET.get('slot_date')
			return JsonResponse({
					"slot_day_value": get_date_day_or_empty(slot_date_str),
				})
			
class BaseCourseExamScheduleAjax(FeedDataView):
	token = couse_exam_schedule_paging().token

	def filter_queryset(self, queryset):
		search = self.query_data.get("sSearch",'')
		queryset = queryset.filter(
			reduce(operator.and_, (
				Q(course_code__icontains = x )|
				Q(course_name__icontains = x )|
				Q(comp_code__icontains = x )
				for x in search.split()
				)
			)) if search else queryset
		return queryset
	
	def get_queryset(self):
		query = super(BaseCourseExamScheduleAjax, self).get_queryset()
		semester = self.kwargs.get('semester')
		exam_type = self.kwargs.get('exam_type')
		exam_slot = self.kwargs.get('exam_slot')

		query = query.filter(semester=semester) if semester else query
		query = query.filter(exam_type=exam_type) if exam_type else query
		query = query.filter(exam_slot=exam_slot) if exam_slot else query

		query = query.annotate(
			sem_name = F('semester__semester_name'),
			exam_details = Concat(F('exam_type__exam_type'),Value('-'), F('exam_type__evaluation_type'),
				output_field=CharField()
			),
			slot_details = Concat(F('exam_slot__slot_date'),Value(' '), F('exam_slot__slot_day'), 
				Value(' '),F('exam_slot__slot_name'),
				output_field=CharField()
			),
		)
		return query

class ExamAttendanceAjax(FormView):
	template_name = 'master/inclusion/loc_exam_course.html'

	def get_form_class(self):
		return attendance_form(self.request.user)

	def get_location(self):
		return self.request.GET.get('location') or None

	def get_exam_venue(self):
		return self.request.GET.get('exam_venue') or None

	def get_form(self, *args, **kwargs):
		form = super().get_form(*args, **kwargs)

		try:
			loc = Location.objects.get(pk=self.get_location())
			form.fields['exam_venue'].queryset=ExamVenue.objects.filter(location=loc)
			form.fields['exam_venue'].initial = self.get_exam_venue()
			exam_slot_list = ExamVenueSlotMap.objects.filter(exam_venue__pk=self.get_exam_venue()).values_list('exam_slot')
			form.fields['course'].queryset = CourseExamShedule.objects.filter(exam_slot__in=exam_slot_list).annotate(
					course_code_name=Concat('course_code',Value(':'),'course_name')).values_list("course_code_name",flat=True).distinct()
		except Exception as e:
			pass

		return form


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = self.get_form()
		return context

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			response = super().get(request, *args, **kwargs)
			return JsonResponse(
				{

					'context':self.render_to_response(response.context_data).render().content.decode(),
				}
			)


class ExamAttendanceSummaryReportAjax(FormView):
	template_name = 'master/inclusion/loc_exam_attendance_summary_report.html'

	def get_form_class(self):
		return exam_attendance_summary_report_form(self.request.user)

	def get_exam_type(self):
		return self.request.GET.get('exam_type') or None

	def get_form(self, *args, **kwargs):
		form = super().get_form(*args, **kwargs)
		try:
			exam_type = ExamType.objects.get(pk=self.get_exam_type())
			exam_slot_list = ExamVenueSlotMap.objects.filter(exam_type=exam_type).values_list('exam_slot')
			form.fields['exam_slot'].queryset = ExamSlot.objects.filter(pk__in=exam_slot_list).distinct().order_by('slot_date','slot_start_time',)
		except Exception as e:
			form.fields['exam_slot'].queryset = ExamSlot.objects.none()

		return form


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = self.get_form()
		return context

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			response = super().get(request, *args, **kwargs)
			return JsonResponse(
				{

					'context':self.render_to_response(response.context_data).render().content.decode(),
				}
			)

class ProgramFetchAjax(FormView):
	template_name = 'master/inclusion/bulk_act_deact_program.html'
	form_class = BulkActivateInactivateForm

	def get_program_type(self):
		return self.request.GET.get('program_type') or None

	def get_form(self, *args, **kwargs):
		form = super().get_form(*args, **kwargs)
		if self.get_program_type():
			try:
				programs = Program.objects.filter(program_type=self.get_program_type()).order_by('program_code')
				form.fields['program'].queryset = programs
			except Exception as e:
				form.fields['program'].queryset = Program.objects.all().order_by('program_code')
		return form


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = self.get_form()
		return context

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			response = super().get(request, *args, **kwargs)
			return JsonResponse(
				{

					'context':self.render_to_response(response.context_data).render().content.decode(),
				}
			)

class ExamtypeFetchAjax(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			ev_type=request.GET.get('ev_type')
			exam_type=ExamType.objects.filter(evaluation_type=ev_type)

			return render(request, 'master/inclusion/exam_type_dropdown.html', {'exam_type': exam_type})



class StudentAttendanceAjax(FormView):
	template_name = 'master/inclusion/loc_student_attendance.html'

	def get_form_class(self):
		return student_attendance_form(self.request.user)

	def get_exam_type(self):
		return self.request.GET.get('exam_type') or None

	def get_exam_venue(self):
		return self.request.GET.get('exam_venue') or None

	def get_course(self):
		return self.request.GET.get('course') or None

	def get_form(self, *args, **kwargs):
		form = super().get_form(*args, **kwargs)
		exam_type = get_instance_or_none(ExamType, pk=self.get_exam_type())
		evsm = ExamVenueSlotMap.objects.filter(exam_type=exam_type)
		form.fields['exam_venue'].queryset = ExamVenue.objects.filter(examvenueslotmap_ev__exam_venue__in=evsm.values('exam_venue')).distinct()
		form.fields['exam_venue'].initial = self.get_exam_venue()

		exam_slot_list = evsm.filter(exam_venue__pk=self.get_exam_venue()).values_list('exam_slot')

		form.fields['course'].queryset = CourseExamShedule.objects.filter(exam_slot__in=exam_slot_list,exam_type=exam_type).distinct()

		form.fields['course'].initial = self.get_course()
		form.fields['exam_slot'].queryset = ExamSlot.objects.filter(pk__in=exam_slot_list).distinct()

		return form


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = self.get_form()
		return context

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			response = super().get(request, *args, **kwargs)
			return JsonResponse(
				{

					'context':self.render_to_response(response.context_data).render().content.decode(),
				}
			)

class HallTicketAttendanceIssueAjax(FormView):
	template_name = 'master/inclusion/location_venue.html'
	form_class = ProgramLocationVenueForm

	def get_location(self):
		return self.request.GET.get('location') or None

	def get_initial(self):
		return self.request.GET

	def get_form(self,*args,**kwargs):
		form = super().get_form(*args,**kwargs)
		try:
			loca = Location.objects.get(pk=self.get_location())
			form.fields['exam_venue'].queryset = ExamVenue.objects.filter(location=loca)
		except Exception as e:
			form.fields['exam_venue'].queryset = ExamVenue.objects.none()
		return form

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = self.get_form()
		return context

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			response = super().get(request, *args, **kwargs)
			return JsonResponse(
				{

					'context':self.render_to_response(response.context_data).render().content.decode(),
				}
			)


class BaseSyncLogDataAjaxView(FeedDataView):
	def get_queryset(self):
		query = super(BaseSyncLogDataAjaxView, self).get_queryset()
		query = query.filter(status=DataSyncLogs.SUCCESS).order_by('-synced_on')
		return query

class UpdateStudentPhotoAjax(View):
	def post(self, request):
		photo = request.FILES['file']
		try:
			uploadstudentphoto_object = UploadStudentPhoto.objects.get(student_id=request.POST.get('student_id').strip())
			uploadstudentphoto_object.student_photo.delete()
			uploadstudentphoto_object.save()
			uploadstudentphoto_object.student_photo = photo
			uploadstudentphoto_object.save()
		except Exception as e:
			UploadStudentPhoto.objects.create(student_id=request.POST.get('student_id').strip(), student_photo=photo)

		student_object = Student.objects.get(student_id=request.POST.get('student_id').strip())
		student_object.photo.delete()
		student_object.save()
		student_object.photo = photo
		student_object.save()

		return JsonResponse({
				'context': 'done'
			})

class PhotoAlreadyExistsAjax(View):
	  def post(self, request):
		  student_object = Student.objects.get(student_id=request.POST.get("student_id"))
		  if student_object.photo:
			  context = "Yes"
		  else:
			  context = "No"
		  return JsonResponse({
				  'context': context
			  })

#This class is to remove the special characters present in the uploaded file
class HandleUploadFunctionAjax(View):
	def post(self, request):
		data = json.loads(request.POST.get('data'))

		data_list = []
		for each in data:
			if each=="":
				pass
			else:
				data_list.append(each)

		final_data_list = []
		for row in data_list:
			new_row = ""
			new_row_list = []
			for each_char in row:
				if ord(each_char) > 127 or each_char == '?':
					pass
				else:
					new_row += each_char
			new_row_list.append(new_row+'\n')
			final_data_list.append(new_row_list)

		return JsonResponse({
			'context': final_data_list
		})

class HallticketExceptionAjaxView(View):
	def post(self, request):
		student_id = request.POST.get('student_id')
		program_object = Program.objects.filter(program_code=student_id.strip()[4:8]).first()
		if program_object.program_type == 'certification':
			return JsonResponse({
				'context': 'certification',
			})
		else:
			return JsonResponse({
				'context': 'non-certification',
			})