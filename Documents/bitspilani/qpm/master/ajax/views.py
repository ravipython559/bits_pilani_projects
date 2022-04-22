from django.views.generic import FormView, View
from django.http import JsonResponse
from master.models import *
from datetime import datetime

class SetQPSubmissionsFlagAjax(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			context = {}
			if request.GET.get('lock_flag'):
				if request.GET.get('id_semester'):
					semester1 = list(Semester.objects.filter(id=int(request.GET.get('id_semester'))).values('id', 'semester_name'))
					semester2 = list(Semester.objects.exclude(id=int(request.GET.get('id_semester'))).values('id', 'semester_name'))
					context['semesters'] = semester1 + semester2
				if request.GET.get('id_batch'):
					batch1 = list(Batch.objects.filter(id=int(request.GET.get('id_batch'))).values('id', 'batch_name'))
					batch2 = list(Batch.objects.exclude(id=int(request.GET.get('id_batch'))).values('id', 'batch_name'))
					context['batches'] = batch1 + batch2
				if request.GET.get('id_exam_type'):
					examtype1 = list(ExamType.objects.filter(id=int(request.GET.get('id_exam_type'))).values('id', 'exam_type'))
					examtype2 = ExamType.objects.exclude(id=int(request.GET.get('id_exam_type')))
					examtype3 = list(examtype2.exclude(exam_type='-').values('id', 'exam_type'))
					context['exam_types'] = examtype1 + examtype3
				else:
					context['semesters'] = list(Semester.objects.all().values('id', 'semester_name'))
					context['batches'] = list(Batch.objects.all().values('id', 'batch_name'))
					context['exam_types'] = list(ExamType.objects.exclude(exam_type='-').values('id', 'exam_type'))
			if request.GET.get('lock_all_submissions_flag'):
				context['semesters'] = list(Semester.objects.filter(semester_name='-').values('id', 'semester_name'))
				context['batches'] = list(Batch.objects.filter(batch_name='-').values('id', 'batch_name'))
				context['exam_types'] = list(ExamType.objects.filter(exam_type='-').values('id', 'exam_type'))
			return JsonResponse(context)


def get_date_day_or_empty(date_str, format = '%Y-%m-%d', display_format = "%A"):
	try:
		date_day = datetime.strptime(date_str, format).date().strftime(display_format)
	except Exception as e:
		date_day = ''
	return date_day


class ExamSlotAjax(View):
	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			slot_date_str = request.GET.get('slot_date')
			return JsonResponse({
					"slot_day_value": get_date_day_or_empty(slot_date_str),
				})





