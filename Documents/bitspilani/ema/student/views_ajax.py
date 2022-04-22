from django.db.models.functions import Concat
from django.views.generic import  FormView
from master.utils.extra_models.querysets import *
from .forms import *
from django.db.models import CharField
from django.db.models import Value , F
from django.http import JsonResponse
from ema import default_settings as S
import functools
import operator

class HallTicketExamSlotAjaxFormView(FormView):

	def get_form_class(self):
		student_id=self.request.user.email.split('@')[0]
		return get_hall_ticket_exam_slot_form(self.exam_type, self.exam_slot_id, self.semester, self.course_code, self.course_id, student_id)

	
	def get(self, request, *args, **kwargs):
		self.exam_type = get_instance_or_none(ExamType, **{"pk":request.GET['exam_type']})
		self.exam_slot_id = request.GET['exam_slot_id']
		self.semester = get_instance_or_none(Semester, **{"pk":request.GET['semester']})
		self.course_code = request.GET['course_code']
		self.course_id = request.GET['course_id']
		return JsonResponse({'form': str(self.get_form())})

class HallTicketLocationAjaxFormView(FormView):

	def get_form_class(self):
		student_id=self.request.user.email.split('@')[0]
		return get_hall_ticket_location_form(self.exam_type, self.exam_slot, self.location_id, self.exam_venue_id, student_id, self.semester)
	
	def get(self, request, *args, **kwargs):
		self.exam_slot = get_instance_or_none(ExamSlot, **{"pk":request.GET['exam_slot']})
		self.exam_type = get_instance_or_none(ExamType, **{"pk":request.GET['exam_type']})
		self.semester = get_instance_or_none(Semester, **{"pk":request.GET['semester']})
		self.location_id = request.GET['location_id']
		self.exam_venue_id = request.GET['exam_venue_id']
		return JsonResponse({'form': str(self.get_form())})

class HallTicketExamVenueAjaxFormView(FormView):

	def get_form_class(self):
		student_id=self.request.user.email.split('@')[0]
		return get_hall_ticket_exam_venue_form(self.exam_type, self.exam_slot, self.location, self.exam_venue_id, student_id, self.semester)
	
	def get(self, request, *args, **kwargs):
		self.exam_slot = get_instance_or_none(ExamSlot, **{"pk":request.GET['exam_slot']})
		self.location = get_instance_or_none(Location, **{"pk":request.GET['location']})
		self.exam_type = get_instance_or_none(ExamType, **{"pk":request.GET['exam_type']})
		self.semester = get_instance_or_none(Semester, **{"pk":request.GET['semester']})
		self.exam_venue_id = request.GET['exam_venue_id']
		return JsonResponse({'form': str(self.get_form())})