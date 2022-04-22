from django.shortcuts import render
from django.views.generic import FormView, TemplateView, View
from master.utils.extra_models.querysets import *
from django.urls import reverse_lazy
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .forms import *
from master.models import *
from .tables import *
from master.views import *
from .permissions import *
import requests
import re

# Create your views here.


class ApplicationCenterSyncView(FormView):
	template_name = 'administrator/app-center-sync.html'
	form_class = ApplicationCenterSyncForm	
	success_url = reverse_lazy('administrator:admin_router:sync-lms-api')
		
	def get_elearn_data(self):
		program_data_set = []
		headers = {
			'Content-type': 'application/json',
			settings.ELEARN_API_AUTHHEADER : settings.ELEARN_API_AUTHKEY,
		}
		try:
			response = requests.get(settings.ELEARN_API_URL, headers=headers)
			response.raise_for_status()
			program_data_set.extend(response.json())

		except Exception as e:
			pass

		return program_data_set

	def form_valid(self, form):
		if 'canvas' == self.request.POST.get('which_api'):
			try:
				from api import canvas
				result = canvas.API.get_data(form.cleaned_data['semester'], form.cleaned_data['course_list'])
				return JsonResponse({'status':200,'message':'Data Synced Sucessfully', 'table_render':self.table_render})

			except Exception as e:
				return JsonResponse({'status':500,'message':str(e), 'table_render':self.table_render})

		if 'taxila' == self.request.POST.get('which_api'):
			try:
				from api import taxila
				result = taxila.API.get_data(form.cleaned_data['semester'], form.cleaned_data['course_list'])
				return JsonResponse({'status':200,'message':'Data Synced Sucessfully', 'table_render':self.table_render})

			except Exception as e:
				return JsonResponse(status=500, data={'message':str(e), 'table_render':self.table_render})

		return self.render_to_response(self.get_context_data(form=form))
	
	def form_invalid(self, form):
		self.template_name = 'administrator/inclusions/ema_data_sync.html'
		return JsonResponse({'context':self.render_to_response(self.get_context_data(form=form)).render().content.decode()})

	def get_context_data(self, **kwargs):
		context = super(ApplicationCenterSyncView, self).get_context_data(**kwargs)
		query = DataSyncLogs.objects.filter(status=DataSyncLogs.SUCCESS).order_by('-synced_on')
		context['sync_log_table'] = APPLCenterSyncLogTable(query)
		return context

	def insert_DataSyncLogs(self,*args,**kwargs):
		source = kwargs.get('source')
		records_pulled = kwargs.get('records_pulled',None)
		status = kwargs.get('status',DataSyncLogs.FAILED)
		parameters = kwargs.get('parameters',None)
		DataSyncLogs.objects.create(source=source, records_pulled=records_pulled, status=status, parameters=parameters)

	@property
	def table_render(self):
		self.template_name = "administrator/inclusions/table_content_sync_data.html"
		return self.render_to_response(self.get_context_data()).render().content.decode()


	def post(self, request, *args, **kwargs):

		if request.is_ajax():
			if "elearn" == request.POST.get('which_api'):
				ctx = self.render_to_response(self.get_context_data()).render().content.decode()
				item_count=0;
				kwargs.update(source="E-LEARN")

				try:
					elearn_bulk_programs_json =  self.get_elearn_data()
					kwargs.update(records_pulled=len(elearn_bulk_programs_json))

					if not len(elearn_bulk_programs_json):
						raise ValueError("Failure in data pull")

					item_count=1
					for item_count,prog in enumerate(elearn_bulk_programs_json):
						if Program.CLUSTER.lower() in prog[2].lower():
							info,_=Program.objects.update_or_create(program_code= prog[0][0:6], defaults={"program_name":prog[1][0:60], "program_type":Program.CLUSTER,"organization": prog[2][0:50],})

						elif (Program.NON_SPECIFIC.lower() in prog[2].lower()):
							info,_=Program.objects.update_or_create(program_code= prog[0][0:6], defaults={"program_name":prog[1][0:60], "program_type":Program.NON_SPECIFIC,"organization": prog[2][0:50],})

						elif (Program.CERTIFICATION.lower() in prog[2].lower()):
							info,_=Program.objects.update_or_create(program_code= prog[0][0:6], defaults={"program_name": prog[1][0:60], "program_type": Program.CERTIFICATION,"organization": prog[2][0:50],})

						else:
							info,_=Program.objects.update_or_create(program_code= prog[0][0:6], defaults={"program_name": prog[1][0:60], "program_type": Program.SPECIFIC, "organization": prog[2][0:50],})

					kwargs.update(parameters="{0} records processed".format(len(elearn_bulk_programs_json)))
					kwargs.update(status=DataSyncLogs.SUCCESS)

					self.insert_DataSyncLogs(**kwargs)
					return JsonResponse({'status':200,'message':'E-Learn Data Synced Sucessfully', 'table_render':self.table_render})
				except Exception as e:
					kwargs.update(parameters="{0} records processed".format(item_count))
					self.insert_DataSyncLogs(**kwargs)
					return JsonResponse({'status':500,'message':str(e)+" for \n{0}:{1}".format(prog[0],prog[1]) if item_count else str(e), 'table_render':self.table_render})
			else:
				return super().post(request, *args, **kwargs)
		else:
			return super().get(request, *args, **kwargs)

class StudentRegistrationView(EMAUserPermissionMixin,BaseStudentRegistrationView):
	ajax_url = 'administrator:admin_ajax:stud-reg-view-ajax'


class AttendenceDataView(EMAUserPermissionMixin, BaseAttendanceDataView):
	pass


class StudentAttendenceView(EMAUserPermissionMixin, BaseStudentAttendenceView):
	pass

class ExamAttendenceSummaryReportView(EMAUserPermissionMixin, BaseExamAttendenceSummaryReportView):
	pass

class StudentCountByVenueBySlotView(EMAUserPermissionMixin, BaseStudentCountByVenueBySlotView):
	pass

class StudentAttendanceCountByCourseByVenueView(EMAUserPermissionMixin, BaseStudentAttendanceCountByCourseByVenueView):
	pass

class SessionWiseAbsenseDataView(EMAUserPermissionMixin, BaseSessionWiseAbsenseDataView):
	pass

class HallTicketAttendanceView(EMAUserPermissionMixin, BaseHallTicketAttendanceView):
	ajax_url = 'administrator:admin_ajax:halltick-attend-view-ajax'

class CourseExamSceduleView(EMAUserPermissionMixin, BaseCourseExamScheduleView):
	template_name = 'master/view-course-exam-schedule.html'
	ajax_url = 'administrator:admin_ajax:course-exam-schedule-ajax'


class HallTicketPDF(EMAUserPermissionMixin,BaseHallTicketPDF):
	pass

class StudentPhotoView(EMAUserPermissionMixin,BaseStudentPhotoView):
	pass

class StudentsWithoutHallTicket(EMAUserPermissionMixin, StudentsWithoutHallticketView):
	template_name = 'master/students-without-hall-ticket.html'

class SyncSDMSEmailandPhone(EMAUserPermissionMixin,BaseSyncSDMSEmailandPhone):
	pass

class BulkActivateInactivate(EMAUserPermissionMixin, BaseBulkActivateInactivate):
	pass

class SyncQPMExamtype(APIView):
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
			ExamType.objects.create(exam_type=request.data['exam_type'], evaluation_type=request.data['evaluation_type'])
			return Response(request.data, status=status.HTTP_201_CREATED)

	def delete(self, request, *args, **kwargs):
		try:
			a = ExamType.objects.get(exam_type=request.data['exam_type'], evaluation_type=request.data['evaluation_type'])
			a.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		except:
			return Response("Given exam type is not yet created")


class SyncQPMBatch(APIView):
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


class SyncQPMSemester(APIView):
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


class SyncQPMExamSlot(APIView):
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

