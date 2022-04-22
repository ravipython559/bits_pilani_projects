from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from master.utils.extra_models.querysets import get_instance_or_none
from master.models import Student, CurrentExam, HallTicketException, HallTicket, Program
import functools
import datetime

class EMAUserPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):

	def test_func(self):
		is_student = self.request.user.remoteuser.user_type.user_role in ['STUDENT', 'RE-SCHL', 'CERT-SCHL']
		student = get_instance_or_none(Student, student_id=self.request.user.email.split('@')[0]) 
		return is_student and student

class CheckHallTicketConditionsMixin:
	def dispatch(self, request, *args, **kwargs):
		student_id = request.user.email.split('@')[0]
		student = get_instance_or_none(Student, student_id=student_id)
		self.student = student
		sem = request.path.split('/')[3]
		pg_code = self.request.user.email.split('@')[0][4:8]
		self.program = Program.objects.get(program_code=pg_code)

		ce_queryset = CurrentExam.objects.filter(program__program_code=pg_code, is_active=True, batch=student.batch)
		if ce_queryset:
			self.ht = not ce_queryset.filter(hall_tkt_change_flag=True).exists()
		else:
			self.ht = False

		self.ce = not ce_queryset.exists()

		if self.ht:
			if ce_queryset.filter(hall_tkt_change_flag=False, missing_tkt_exception_flag=True).exists():

				self.exception_flag = True
				q1 = HallTicketException.objects.filter(
					Q(student_id=student_id, exception_end_date__gte=datetime.datetime.now().strftime("%Y-%m-%d")) | Q(
						student_id=student_id, exception_end_date=None))
				q2 = HallTicketException.objects.filter(student_id=student_id, exception_end_date=None)
				q = q1 | q2

				if not q.exists():

					qu1 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list(
						"semester", flat=True).distinct()

					qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list(
						"exam_type", flat=True).distinct()

					data = HallTicket.objects.filter(student=self.student, semester__in=qu1, exam_type__in=qu2,
													 is_cancel=False).exclude(exam_slot_id=1).distinct()

					if not data.exists():

						self.ht = False

					else:
						pass

			else:
				self.exception_flag = False

				qu1 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list(
					"semester", flat=True).distinct()

				qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list(
					"exam_type", flat=True).distinct()

				data = HallTicket.objects.filter(student=self.student, semester__in=qu1, exam_type__in=qu2,
												 is_cancel=False).exclude(exam_slot_id=1).distinct()

				if not data.exists():
					pass

				else:
					self.no_hallticket_db = True

		else:
			pass
		# Student will be able to choose semester and proceed to generate hall ticket.
		# Student will also be able to modify their hall ticket

		self.certification_exam_type = functools.reduce(lambda x, y: "{0}, {1}".format(x, y) if y else "{0}".format(x),
														list(ce_queryset.values_list("exam_type__exam_type",
																					 flat=True) if ce_queryset.count() else [
															'-', ])) if self.program.program_type == Program.CERTIFICATION else ""

		semester = sem

		selected_rec = ce_queryset.filter(semester=semester)

		if selected_rec.filter(hall_tkt_change_flag=True).exists():  # check before selecting sem also
			url = 'student:hall-ticket'
		else:
			# check exception table with SEMESTER and STUD_ID
			query1 = HallTicketException.objects.filter(student_id=student_id,
														exception_end_date__gte=datetime.datetime.now().strftime(
															"%Y-%m-%d"), semester__id=semester)
			query2 = HallTicketException.objects.filter(student_id=student_id, semester__id=semester,
														exception_end_date=None)
			records = query1 | query2

			if selected_rec.filter(missing_tkt_exception_flag=True):
				self.ex_f = True
			else:
				self.ex_f = False

			if records.exists():
				# check HallTicket with STUD_ID, SEMESTER and EXAM_TYPE

				qu1 = CurrentExam.objects.filter(program__program_code=student_id[4:8],
												 is_active=True).values_list("semester", flat=True).distinct()

				qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8],
												 is_active=True).values_list("exam_type", flat=True).distinct()

				data = HallTicket.objects.filter(student__student_id=student_id, semester=semester,
												 exam_type__in=qu2, is_cancel=False).exclude(
					exam_slot_id=1).distinct()

				if not data.exists():
					url = 'student:hall-ticket'
				else:
					url = 'student:hall-ticket'
			else:

				if self.ex_f:
					# check hall ticket then allow to generate
					qu1 = CurrentExam.objects.filter(program__program_code=student_id[4:8],
													 is_active=True).values_list("semester",
																				 flat=True).distinct()

					qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8],
													 is_active=True).values_list("exam_type",
																				 flat=True).distinct()

					data = HallTicket.objects.filter(student__student_id=student_id, semester=semester,
													 exam_type__in=qu2, is_cancel=False).exclude(
						exam_slot_id=1).distinct()

					if not data:
						url = 'student:hall-ticket'
					else:
						url = 'student:hall-ticket-preview'
				else:
					url = 'student:hall-ticket-preview'

		if request.path == reverse_lazy(url, kwargs={'semester':sem,}):
			return super().dispatch(request, *args, **kwargs)
		else:
			return HttpResponseRedirect(reverse_lazy('student:index'))