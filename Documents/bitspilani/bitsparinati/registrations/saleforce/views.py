from django.views.generic import TemplateView, View

from bits_admin.models import SaleForceLogCleanup
from .tables import salesforce_data_log, specific_program_summary_data, saleforcelogcleanuptable
from .forms import SalesForceFilterForm, SpecificSummaryDataForm
from rest_framework import status
from registrations.models import (SaleForceLeadDataLog,
								  SaleForceQualificationDataLog, SaleForceWorkExperienceDataLog,
								  SaleForceDocumentDataLog, SaleForceAsyncTask, SpecificAdmissionSummary)
from django.db.models import Q
from django.http import JsonResponse
from celery.result import AsyncResult
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from .utils import saleforce_async_api as sf_api
from celery.task.control import revoke
from datetime import date, timedelta
import sys
from itertools import chain
import json


class FailedTaskView(View):

	def restart_task(self, meta):
		serializer_meta = meta['serializer_model']
		model_meta = meta['model']
		log_model_meta = meta['log_model']
		instance = getattr(sys.modules[model_meta['module']],
						   model_meta['classname']).objects.get(pk=model_meta['pk'])
		sf_api(meta['sf_api_obj'], instance,
			   getattr(sys.modules[serializer_meta['module']], serializer_meta['classname']),
			   getattr(sys.modules[log_model_meta['module']], log_model_meta['classname']),
			   {
				   k: getattr(
					   sys.modules[v['module']],
					   v['classname']).objects.get(pk=v['pk']
												   )
				   for k, v in meta['log_param'].items()
			   },
			   serializer_fields=meta['serializer_fields'],
			   seconds=15
			   )

		if hasattr(instance, 'email'):
			return instance.email
		elif hasattr(instance, 'student_application_id'):
			return instance.student_application_id
		else:
			return instance.application.student_application_id

	def get(self, request, *args, **kwargs):
		restarted_list = []
		statuses = map(str, [status.HTTP_201_CREATED, status.HTTP_200_OK, 'STOP'])
		if request.is_ajax():
			sfat = SaleForceAsyncTask.objects.exclude(sf_status__in=statuses)
			for task in sfat.iterator():
				meta = task.context
				job = AsyncResult(task.job)
				task.status = job.state
				log = job.result
				if log and log.status:
					sf_status = str(log.status)

					if job.failed() or sf_status not in statuses:
						task.sf_status = 'STOP'
						revoke(task.job, terminate=True)
						restarted_list.append(self.restart_task(meta))

					elif job.successful():
						task.sf_status = sf_status

					task.save()

			return JsonResponse({'message': 'restarted instances:' + ', '.join(restarted_list)})


class ApplicantDataTransferLogView(TemplateView):
	template_name = 'registrations/salesforce/salesforce_data_log.html'

	def get_context_data(self, status=None, **kwargs):
		context = super(ApplicantDataTransferLogView, self).get_context_data(**kwargs)
		created_datetime = date.today() - timedelta(days=3)
		q1 = SaleForceLeadDataLog.objects.filter(created_on__gte=created_datetime)
		q2 = SaleForceQualificationDataLog.objects.filter(created_on__gte=created_datetime)
		q3 = SaleForceWorkExperienceDataLog.objects.filter(created_on__gte=created_datetime)
		q4 = SaleForceDocumentDataLog.objects.filter(created_on__gte=created_datetime)
		if status:
			status_fliter = status.split()

			if 'not' in status_fliter:
				q1 = q1.filter(~Q(status=status_fliter[1]), ~Q(status=status_fliter[2]))
				q2 = q2.filter(~Q(status=status_fliter[1]), ~Q(status=status_fliter[2]))
				q3 = q3.filter(~Q(status=status_fliter[1]), ~Q(status=status_fliter[2]))
				q4 = q4.filter(~Q(status=status_fliter[1]), ~Q(status=status_fliter[2]))
			else:
				q1 = q1.filter(Q(status=status_fliter[0]) | Q(status=status_fliter[1]))
				q2 = q2.filter(Q(status=status_fliter[0]) | Q(status=status_fliter[1]))
				q3 = q3.filter(Q(status=status_fliter[0]) | Q(status=status_fliter[1]))
				q4 = q4.filter(Q(status=status_fliter[0]) | Q(status=status_fliter[1]))
		q1 = q1.order_by('-sent_to_sf_on')
		q2 = q2.order_by('-sent_to_sf_on')
		q3 = q3.order_by('-sent_to_sf_on')
		q4 = q4.order_by('-sent_to_sf_on')
		q5 = chain(q1, q2, q3, q4)
		SDL_Table = salesforce_data_log(status=status)
		context['form'] = SalesForceFilterForm(self.request.GET)
		context['table'] = SDL_Table(q5)
		context['title'] = 'Applicant JSON Data Transfer Log'
		return context

	def get(self, request, *args, **kwargs):
		status = request.GET.get("status", None)
		return super(ApplicantDataTransferLogView, self).get(
			request, status=status, *args, **kwargs)


def file_download(request, pk, reference_id):
	query1 = SaleForceQualificationDataLog.objects.filter(id=pk, reference_id=reference_id)
	query2 = SaleForceWorkExperienceDataLog.objects.filter(id=pk, reference_id=reference_id)
	query3 = SaleForceLeadDataLog.objects.filter(id=pk, reference_id=reference_id)
	query4 = SaleForceDocumentDataLog.objects.filter(id=pk, reference_id=reference_id)
	query = chain(query1, query2, query3, query4)
	dataset = list(query)[0].dataset
	response = HttpResponse(json.dumps(dataset, indent=4), content_type="application/json")
	response['Content-Disposition'] = 'attachment;filename=file.json'
	return response


class SpecificProgramReportView(TemplateView):
	template_name = 'registrations/salesforce/specific_program_summary_data.html'

	def get_context_data(self, *args, **kwargs):
		program = self.request.GET.get('program', None)

		context = super(SpecificProgramReportView, self).get_context_data(**kwargs)
		query = SpecificAdmissionSummary.objects.all()
		if program:
			query = query.filter(specific_program_id=program)
		SS_Table = specific_program_summary_data(program=program)
		context['title'] = "Specific Program Summary Data (sent to Salesforce)"
		context['form'] = SpecificSummaryDataForm(self.request.GET)
		context['table'] = SS_Table(query)
		return context

class SaleForceLogReport(TemplateView):
	template_name ='registrations/salesforce/sf_log_data_deletion_report.html'

	def get_context_data(self, *args, **kwargs):

		context = super(SaleForceLogReport, self).get_context_data(**kwargs)
		query=SaleForceLogCleanup.objects.all()
		SSL_Table = saleforcelogcleanuptable()
		context['title'] = "SalesForce Log Data Deletion Report"
		context['table'] = SSL_Table(query)
		return context
