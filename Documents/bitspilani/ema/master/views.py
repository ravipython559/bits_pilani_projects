from django.shortcuts import render, HttpResponseRedirect
from django.views.generic import TemplateView,FormView
from master.models import *
from master.tables import *
from master.tasks import *
from master.forms.forms import *
from master.utils.extra_models.querysets import *
from master.utils.csv.response import hall_ticket_csv_streaming_csv_response
from django.urls import reverse_lazy
from functools import reduce 
from django.forms import modelformset_factory
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.db.models import F, Value, OuterRef, Subquery
from django.db.models.functions import Concat
from easy_pdf.views import PDFTemplateView, PDFTemplateResponseMixin
from djqscsv import render_to_csv_response
from easy_pdf.rendering import render_to_pdf_response
import collections, operator, re
from ema import default_settings as S
from django.db.models import Count, Sum
from collections import namedtuple
from django.http import HttpResponse
import csv
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
import functools

# Create your views here.
@method_decorator([never_cache], name="dispatch")
class BaseStudentRegistrationView(TemplateView):

	template_name = 'master/stud-reg-view.html'
	model = StudentRegistration
	form_class = ProgramSemesterForm

	def get_filter_queryset(self, filter_params=None):
		filter_exists = reduce(lambda x,y: x or y, map(lambda x:x[1], filter_params.items()), False)	
		sum_filter = filter_exists and reduce(operator.and_, (
				Q(**{k: v}) 
					for (k, v) in filter_params.items() if v is not None
			)
		)

		return self.queryset.filter(sum_filter) if sum_filter else self.queryset


	def get_context_data(self, **kwargs):
		context = super(BaseStudentRegistrationView, self).get_context_data(**kwargs)
		self.queryset = get_student_details()
		filter_dict = {}
		filter_dict['pg_code'] = self.request.GET.get('program') or None
		filter_dict['semester'] = self.request.GET.get('semester') or None

		query = self.get_filter_queryset(filter_params=filter_dict)
		context['table'] = stud_reg_view(self.ajax_url,**filter_dict)(query)
		context['header_title'] = 'Student Registration Details'
		search = self.request.GET.get('search') or None
		context['form']  = self.form_class(initial={
			'program': filter_dict['pg_code'],
			'semester': filter_dict['semester'],
			'search':search,
			})
		return context

@method_decorator([never_cache], name='dispatch')
class BaseAttendanceDataView(FormView): 
	template_name = 'master/attendance_view.html'
	form_class = AdminLocVenueCourseCodeForm
	global_js_variable = 'global_js_variable'
	bulk_prefix = 'attendence-'

	def get_table(self,**kwargs):
		kwargs.update(course=kwargs.get('course','n'))
		return get_attendance_data_view_table(self.global_js_variable, self.bulk_prefix, **kwargs)(self.get_queryset(**kwargs))

	def form_invalid(self, form):
		return self.render_to_response(self.get_context_data(form=form))

	def form_valid(self, form):
		table = self.get_table(**form.cleaned_data)
		return self.render_to_response(self.get_context_data(form=form, table=table))

	def get_queryset(self, **kwargs):
		kwargs.update(user_email = self.request.user.email if self.request.user.email else None)
		kwargs.update(user_role = None if self.request.user.is_superuser else self.request.user.remoteuser.user_type.user_role)
		return get_attendance_data_view(**kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['global_js_variable'] = self.global_js_variable
		context['bulk_prefix'] = self.bulk_prefix

		if 'table' not in context:
			context['table'] = self.get_table()

		return context

	def get(self, request, *args, **kwargs):
		if 'filter-et' in request.GET:
			form = self.get_form_class()(request.GET)
			if form.is_valid():
				return self.form_valid(form)
			else:
				return self.form_invalid(form)
		return super().get(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		
		if 'attendance' in request.POST:
			form = self.get_form_class()(request.POST)
			if form.is_valid():
				queryset = self.get_queryset(**form.cleaned_data)
				for key, value in request.POST.items():

					result = re.match(r'%s(?P<pk>\d+)' % self.bulk_prefix, key)
					if result:
						instance = get_instance_or_none(queryset.model, pk=result.group('pk'))
						if instance:
							ExamAttendance.objects.update_or_create(
								exam_venue=instance.examvenueslotmap.exam_venue, 
								course=instance.courseexamshedule, 
								semester=instance.courseexamshedule.semester, 
								exam_type=instance.courseexamshedule.exam_type, 
								exam_slot=instance.courseexamshedule.exam_slot,
								defaults={
									'attendance_count':int(value), 
									'last_update_by':request.user
									}
								)

		return HttpResponseRedirect(self.request.path_info)



@method_decorator([never_cache], name='dispatch')
class BaseStudentAttendenceView(FormView):

	template_name = 'master/student-attend-view.html'

	def get_form_class(self):
		return student_attendance_form(self.request.user)

	def get_set(self, form):
		hallticket = HallTicket.objects.filter(exam_type=form.cleaned_data['exam_type'], exam_venue=form.cleaned_data['exam_venue'], is_cancel=False)
		if form.cleaned_data['course']:
			hallticket = hallticket.filter(course=form.cleaned_data['course'])
		if form.cleaned_data['exam_slot']:
			hallticket = hallticket.filter(exam_slot=form.cleaned_data['exam_slot'])
		return hallticket


	def form_valid(self, form):
		hallticket = self.get_set(form)
		group_ht = collections.defaultdict(list)

		for ht in hallticket.iterator():
			group_ht[(str(ht.course), str(ht.exam_slot))].append(ht)
		return render_to_pdf_response(
			request=self.request,
			template='master/pdf/attended_students.html',
			context=self.get_context_data(form=form, ht=dict(group_ht)),
			using=self.template_engine,
			filename='course.pdf',
		)

	def get(self, request, *args, **kwargs):
		self.email = request.user.email
		if 'filter-ht' in request.GET:
			form = self.get_form_class()(request.GET)
			if form.is_valid():
				return self.form_valid(form)
			else:
				return self.form_invalid(form)
		return super().get(request, *args, **kwargs)


@method_decorator([never_cache], name='dispatch')
class BaseExamAttendenceSummaryReportView(FormView):

	template_name = 'master/exam-attendance-summary-report-view.html'
	model = HallTicket

	def get_form_class(self):
		return exam_attendance_summary_report_form(self.request.user)

	def get_students_query(self, halltickets):
		ht = halltickets.values('course_id', 'exam_venue_id').annotate(
			comp_code=F('course__comp_code'),
			course_code=F('course__course_code'),
			course_name=F('course__course_name'),
			venue_short_name=F('exam_venue__venue_short_name'),
			location_name=F('exam_venue__location__location_name'),
			student_count= Count('student_id', distinct=True))
		result = {}
		courses = set()
		for h in ht:
			course_id = h['course_id']
			comp_code = h['comp_code'] if h['comp_code'] else ''
			if course_id in result:
				result[course_id].update({h['exam_venue_id']:h['student_count']})
				result[course_id]['TOTAL'] += h['student_count']
			else:
				result[course_id] = {h['exam_venue_id']:h['student_count']}
				result[course_id]['TOTAL'] = h['student_count']
			courses.add(tuple([course_id, comp_code, h['course_code'], h['course_name']]))

		return ht, result, courses


	def form_valid(self, form):
		halltickets = HallTicket.objects.filter(exam_type=form.cleaned_data['exam_type'], exam_slot=form.cleaned_data['exam_slot'], is_cancel=False)
		ht, result, courses = self.get_students_query(halltickets)
		return self.render_to_response(self.get_context_data(form=form, ht=ht,result=result, courses=courses))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		venues = ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME)
		venues = venues.values('id', 'venue_short_name').annotate(location_name=F('location__location_name'))
		context['venues'] = venues
		return context

	def csv_form_valid(self, form):
		exam_slot = self.request.GET.get('exam_slot')
		halltickets = HallTicket.objects.filter(exam_type=self.request.GET.get('exam_type'), exam_slot=exam_slot, is_cancel=False)
		exam_slot = ExamSlot.objects.get(pk=exam_slot)
		ht, result, courses = self.get_students_query(halltickets)
		response = HttpResponse(content_type="text/csv")
		response['Content-Disposition'] = 'attachment;filename=export.csv'
		writer = csv.writer(response)
		a = ['Slot Name','Compcode', 'Course No', 'Course Title']
		venues = ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME)
		venues = venues.values('id', 'venue_short_name').annotate(location_name=F('location__location_name'))
		location_venues = []
		for i in venues:
			a.insert(len(a), '{0}({1})'.format(i['location_name'], i['venue_short_name']))
		a.insert(len(a), 'Total')
		writer.writerow(a)
		for i in courses:
			xyz = [exam_slot, i[1], i[2], i[3]]
			for j in venues:
				if i[0] in result:
					xyz.insert(len(xyz), result[i[0]].get(j['id'], ''))
			xyz.insert(len(xyz), result[i[0]].get('TOTAL', ''))
			writer.writerow(xyz)
		return response


	def get(self, request, *args, **kwargs):
		response = super(BaseExamAttendenceSummaryReportView, self).get(request, *args, **kwargs)
		if 'filter-ht' in request.GET:
			form = self.get_form_class()(request.GET)
			if form.is_valid():
				return self.form_valid(form)
			else:
				return self.form_invalid(form)
		if 'report_csv' in request.GET:
			form = self.get_form_class()(request.GET)
			if form.is_valid():
				return self.csv_form_valid(form)
			else:
				return self.form_invalid(form)

		return response


@method_decorator([never_cache], name='dispatch')
class BaseStudentCountByVenueBySlotView(TemplateView):

	template_name = 'master/student-count-by-venue-by-slot-view.html'

	def get_students_count_query(self):

		ht = HallTicket.filter_hallticket.filter(is_cancel=False).annotate(program_code=Substr('student__student_id', 5, 4),)
		ce = CurrentExam.objects.filter(is_active=True,)
		if ce.exists():
			is_active_student = functools.reduce(operator.or_,
				(
					Q(
						program_code=x.program.program_code,
						semester=x.semester,
						student__batch=x.batch,
						exam_type=x.exam_type,
					) for x in ce.iterator()
				)
			)

		if is_active_student:
			ht = ht.filter(is_active_student).values('exam_slot_id', 'exam_venue_id').annotate(student_count= Count('student_id', distinct=True),)
		else:
			ht = ht.none()
		if ht:
			if not self.request.user.is_superuser and self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR':
				cordinator_location = LocationCoordinator.objects.filter(coordinator_email_id=self.request.user.email)
				ht = ht.filter(exam_venue__location__in=Subquery(cordinator_location.values('location')))
		result = {}
		for h in ht:
			venue_id = h['exam_venue_id']
			if venue_id in result:
				result[venue_id].update({h['exam_slot_id']:h['student_count']})
				result[venue_id]['TOTAL'] += h['student_count']
			else:
				result[venue_id] = {h['exam_slot_id']:h['student_count']}
				result[venue_id]['TOTAL'] = h['student_count']
		return result

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['result'] = self.get_students_count_query()
		context['exam_slots'] = ExamSlot.objects.exclude(slot_name=S.EXAM_SLOT_NAME)
		context['venues'] = ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME)
		return context

	def csv_form_valid(self):
		result = self.get_students_count_query()
		venues = ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME)
		exam_slots = ExamSlot.objects.exclude(slot_name=S.EXAM_SLOT_NAME)
		response = HttpResponse(content_type="text/csv")
		response['Content-Disposition'] = 'attachment;filename=export.csv'
		writer = csv.writer(response)
		headers = ['Centre/Ec3 Makeup']
		for i in exam_slots:
			headers.insert(len(headers), i.slot_name)

		headers.insert(len(headers), 'Grand Total')
		writer.writerow(headers)
		for i in venues:
			xyz=[i.venue_short_name]
			for j in exam_slots:
				if i.id in result:
					xyz.insert(len(xyz), result[i.id].get(j.id, 0))
				else:
					xyz.insert(len(xyz), 0)
			if i.id in result:
				xyz.insert(len(xyz), result[i.id].get('TOTAL', 0))
			else:
				xyz.insert(len(xyz), 0)
			writer.writerow(xyz)
		return response


	def get(self, request, *args, **kwargs):
		response = super(BaseStudentCountByVenueBySlotView, self).get(request, *args, **kwargs)
		if 'report_csv' in request.GET:
			return self.csv_form_valid()

		return response

@method_decorator([never_cache], name='dispatch')
class BaseStudentAttendanceCountByCourseByVenueView(FormView):

	template_name = 'master/student-attendance-count-by-course-by-venue-view.html'

	def get_form_class(self):
		return student_attendance_count_form(self.request.user)

	def get_students_count_query(self, form_exam_type=None, form_exam_slot=None):

		ce = CurrentExam.objects.filter(is_active=True)
		if form_exam_type:
			ce = ce.filter(exam_type=form_exam_type)

		if ce.exists():
			is_active_exam_attendance = functools.reduce(operator.or_,
				(
					Q(
						semester=x.semester,
						course__batch=x.batch,
						exam_type=x.exam_type,
					) for x in ce.iterator()
				)
			)

		if is_active_exam_attendance:
			ea = ExamAttendance.objects.filter(is_active_exam_attendance).values('exam_venue_id', 'course_id').annotate(exam_attendace_count=Sum('attendance_count'))
		else:
			ea = ea.none()
		if form_exam_slot and ea:
			ea = ea.filter(exam_slot=form_exam_slot)

		if ea:
			if not self.request.user.is_superuser and self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR':
				cordinator_location = LocationCoordinator.objects.filter(coordinator_email_id=self.request.user.email)
				ea = ea.filter(exam_venue__location__in=Subquery(cordinator_location.values('location')))
		result = {}
		for e in ea:
			course_id = e['course_id']
			if course_id in result:
				result[course_id].update({e['exam_venue_id']:e['exam_attendace_count']})
				result[course_id]['TOTAL'] += e['exam_attendace_count']
			else:
				result[course_id] = {e['exam_venue_id']:e['exam_attendace_count']}
				result[course_id]['TOTAL'] = e['exam_attendace_count']
		return result

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		if 'result' not in context:
			context['result'] = self.get_students_count_query()
		context['courses'] = CourseExamShedule.objects.all().distinct()
		context['venues'] = ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME)
		return context

	def form_valid(self, form):
		result = self.get_students_count_query(form.cleaned_data['exam_type'], form.cleaned_data['exam_slot'])
		return self.render_to_response(self.get_context_data(form=form, result=result))

	def csv_form_valid(self, form):
		result = self.get_students_count_query(form.cleaned_data['exam_type'], form.cleaned_data['exam_slot'])
		venues = ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME)
		courses = CourseExamShedule.objects.all().distinct()
		response = HttpResponse(content_type="text/csv")
		response['Content-Disposition'] = 'attachment;filename=export.csv'
		writer = csv.writer(response)
		headers = ['SNo', 'Compcode', 'Course No.', 'Course Name']
		for i in venues:
			headers.insert(len(headers), i.venue_short_name)

		headers.insert(len(headers), 'Total')
		writer.writerow(headers)
		count = 0
		for i in courses:
			count +=1
			comp_code = i.comp_code if i.comp_code else ''
			xyz=[count, comp_code, i.course_code, i.course_name]
			for j in venues:
				if i.id in result:
					xyz.insert(len(xyz), result[i.id].get(j.id, 0))
				else:
					xyz.insert(len(xyz), 0)
			if i.id in result:
				xyz.insert(len(xyz), result[i.id].get('TOTAL', 0))
			else:
				xyz.insert(len(xyz), 0)
			writer.writerow(xyz)
		return response

	def form_validation(self, request, valid_reference):
		form = self.get_form_class()(request.GET)
		if form.is_valid():
			return valid_reference(form)
		else:
			return self.form_invalid(form)


	def get(self, request, *args, **kwargs):
		response = super(BaseStudentAttendanceCountByCourseByVenueView, self).get(request, *args, **kwargs)
		if 'filter-ht' in request.GET:
			return self.form_validation(request, self.form_valid)
		elif 'report_csv' in request.GET:
			return self.form_validation(request, self.csv_form_valid)

		return response


@method_decorator([never_cache], name='dispatch')
class BaseSessionWiseAbsenseDataView(FormView):

	template_name = 'master/student-attendance-count-by-course-by-venue-view.html'

	def get_form_class(self):
		return student_attendance_count_form(self.request.user)

	def get_students_count_query(self, form_exam_type=None, form_exam_slot=None):

		ce = CurrentExam.objects.filter(is_active=True)
		if form_exam_type:
			ce = ce.filter(exam_type=form_exam_type)

		if ce.exists():
			is_active_exam_attendance = functools.reduce(operator.or_,
				(
					Q(
						semester=x.semester,
						exam_type=x.exam_type,
					) for x in ce.iterator()
				)
			)

		if is_active_exam_attendance:
			ea = ExamAttendance.objects.filter(is_active_exam_attendance).values('exam_venue', 'course').annotate(exam_attendace_count=Sum('attendance_count'))
		else:
			ea = ea.none()
		if form_exam_slot and ea:
			ea = ea.filter(exam_slot=form_exam_slot)

		if ea:
			if not self.request.user.is_superuser and self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR':
				cordinator_location = LocationCoordinator.objects.filter(coordinator_email_id=self.request.user.email)
				ea = ea.filter(exam_venue__location__in=Subquery(cordinator_location.values('location')))
		ht = HallTicket.filter_hallticket.filter(is_cancel=False).annotate(program_code=Substr('student__student_id', 5, 4))

		ht_ce = CurrentExam.objects.filter(is_active=True,)
		if form_exam_type:
			ht_ce = ht_ce.filter(exam_type=form_exam_type)
		if ht_ce.exists():
			is_active_student = functools.reduce(operator.or_,
				(
					Q(
						program_code=x.program.program_code,
						semester=x.semester,
						exam_type=x.exam_type,
					) for x in ht_ce.iterator()
				)
			)
		if is_active_student:
			ht = ht.filter(is_active_student).values('exam_venue', 'course').annotate(student_count= Count('student_id', distinct=True))
		else:
			ht = ht.none()

		if form_exam_slot and ht:
			ht = ht.filter(exam_slot=form_exam_slot)

		if ht:
			if not self.request.user.is_superuser and self.request.user.remoteuser.user_type.user_role == 'CO-ORDINATOR':
				cordinator_location = LocationCoordinator.objects.filter(coordinator_email_id=self.request.user.email)
				ht = ht.filter(exam_venue__location__in=Subquery(cordinator_location.values('location')))

		result = {}
		for h in ht:
			course_id = h['course']
			if course_id in result:
				result[course_id].update({h['exam_venue']:h['student_count']})
				result[course_id]['TOTAL'] += h['student_count']
			else:
				result[course_id] = {h['exam_venue']:h['student_count']}
				result[course_id]['TOTAL'] = h['student_count']

		for e in ea:
			if e['course'] in result:
				if e['exam_venue'] in result[e['course']]:
					if result[e['course']][e['exam_venue']] > e['exam_attendace_count']:
						absence_count =  result[e['course']][e['exam_venue']]-e['exam_attendace_count']
					else:
						absence_count = 0

					result[e['course']].update({e['exam_venue']: absence_count})
				del result[e['course']]['TOTAL']
				result[e['course']]['TOTAL'] =  sum(d for d in result[e['course']].values())
		return result

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		if 'result' not in context:
			context['result'] = self.get_students_count_query()
		context['courses'] = CourseExamShedule.objects.all().distinct()
		context['venues'] = ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME)
		return context

	def form_valid(self, form):
		result = self.get_students_count_query(form.cleaned_data['exam_type'], form.cleaned_data['exam_slot'])
		return self.render_to_response(self.get_context_data(form=form, result=result))

	def csv_form_valid(self, form):
		result = self.get_students_count_query(form.cleaned_data['exam_type'], form.cleaned_data['exam_slot'])
		venues = ExamVenue.objects.exclude(venue_short_name=S.VENUE_SHORT_NAME)
		courses = CourseExamShedule.objects.all().distinct()
		response = HttpResponse(content_type="text/csv")
		response['Content-Disposition'] = 'attachment;filename=export.csv'
		writer = csv.writer(response)
		headers = ['SNo', 'Compcode', 'Course No.', 'Course Name']
		for i in venues:
			headers.insert(len(headers), i.venue_short_name)

		headers.insert(len(headers), 'Total')
		writer.writerow(headers)
		count = 0
		for i in courses:
			count +=1
			comp_code = i.comp_code if i.comp_code else ''
			xyz=[count, comp_code, i.course_code, i.course_name]
			for j in venues:
				if i.id in result:
					xyz.insert(len(xyz), result[i.id].get(j.id, 0))
				else:
					xyz.insert(len(xyz), 0)
			if i.id in result:
				xyz.insert(len(xyz), result[i.id].get('TOTAL', 0))
			else:
				xyz.insert(len(xyz), 0)
			writer.writerow(xyz)
		return response

	def form_validation(self, request, valid_reference):
		form = self.get_form_class()(request.GET)
		if form.is_valid():
			return valid_reference(form)
		else:
			return self.form_invalid(form)


	def get(self, request, *args, **kwargs):
		response = super(BaseSessionWiseAbsenseDataView, self).get(request, *args, **kwargs)
		if 'filter-ht' in request.GET:
			return self.form_validation(request, self.form_valid)
		elif 'report_csv' in request.GET:
			return self.form_validation(request, self.csv_form_valid)

		return response

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class BaseHallTicketAttendanceView(FormView):
	template_name = 'master/halltick-attend-view.html'
	model = HallTicket
	form_class = ProgramLocationVenueForm

	def get_initial(self):
		initial = super().get_initial()
		# When the user select the multiple programs
		if self.request.GET.get('program'):
			# initial['program'] = self.request.GET.get('program')
			initial['program'] = dict(self.request.GET)['program']
		else:
			pass
		initial['location'] = self.request.GET.get('location')
		initial['exam_venue'] = self.request.GET.get('exam_venue')
		initial['exam_slot'] = self.request.GET.get('exam_slot')
		initial['exam_type'] = self.request.GET.get('exam_type')
		initial['date'] = self.request.GET.get('date')
		# initial['time'] = self.request.GET.get('time')

		if self.request.GET.get('photo_missing')=='true':
			initial['photo_missing'] = self.request.GET.get('photo_missing')

		return initial


	def form_valid(self, form):
		return self.render_to_response(self.get_context_data(form=form,))


	def form_validation(self, request, valid_reference):
		form = self.get_form_class()(request.GET)
		if form.is_valid():
			return valid_reference(form)
		else:
			return self.form_invalid(form)



	def csv_form_valid(self, form):
		queryset_for_csv=get_attenlist_halltcktissue(self,program=form.cleaned_data.get('program'),
													location=form.cleaned_data.get('location'),
													exam_venue=form.cleaned_data.get('exam_venue'),
													exam_type=form.cleaned_data.get('exam_type'),
													exam_slot=form.cleaned_data.get('exam_slot'),
													date=form.cleaned_data.get('date'),
													)

		response = HttpResponse(content_type="text/csv")
		response['Content-Disposition'] = 'attachment;filename=hall_ticket_issue_status.csv'
		writer = csv.writer(response)
		headers = ['Student ID/Studnt Name','Course Code/ Course Name', 'Exam Type', 'Exam Slot','Exam Venue','Created / Last Updated Date','Hall Ticket']
		writer.writerow(headers)
		for i in queryset_for_csv:
			if CourseExamShedule.objects.filter(course_code=i['course_code']).exists():
				course_name=CourseExamShedule.objects.filter(course_code=i['course_code'])[0]
				course_name=course_name.course_name
			else:
				course_name='-'
			if 'student_name' in i.keys():
				if i['student_name'] =='-':
					stud_name = i['student_reg']
					row = [stud_name,i['course_code']+':'+course_name,'-', '-','-','-','-']
				else:
					if 'venue_short_name' in i.keys():
						if i['venue_short_name']=='-':
							if 	i['exam_venue_name']=='-':
								created_on_date='-'
							else:	
								if 'created_on' in i.keys():
									created_on_date=i['created_on']
								else:	
									created_on_date=i['created_on_y']
							row = [i['student_name'], i['course_code']+':'+course_name,'-','-','-',created_on_date,'-']
						else:
							stud_name = i['student_name']
							cour = i['course_code']
							hall_tic = 'Yes'
							if 'created_on' in i.keys():
								created_on_date=i['created_on']
							else:	
								created_on_date=i['created_on_y']
							row = [stud_name, cour,i['exam_type_name'], i['exam_slot_name'], i['venue_short_name'],created_on_date,hall_tic]					
			else:
				stud_name = i['student_reg']
				row = [stud_name, i['course_code']+':'+course_name, '-', '-','-','-','-']
		
			writer.writerow(row)
		return response


	def csv_wheebox_data(self, form):
		wheebox_queryset = get_attenlist_halltcktissue(self,program=form.cleaned_data.get('program'),
													location=form.cleaned_data.get('location'),
													exam_venue=form.cleaned_data.get('exam_venue'),
													exam_type=form.cleaned_data.get('exam_type'),
													exam_slot=form.cleaned_data.get('exam_slot'),
													date=form.cleaned_data.get('date'),)

		response = HttpResponse(content_type="text/csv")
		response['Content-Disposition'] = 'attachment;filename=wheebox_data.csv'
		writer = csv.writer(response)
		headers = ['Student ID','Student Name', 'Student Email-ID', 'Personal Email-ID', 'Domain', 'Course Code/ Course Name', 'Personal Phone','Exam Slot']
		writer.writerow(headers)
		for i in wheebox_queryset:
			if CourseExamShedule.objects.filter(course_code=i['course_code']).exists():
				course_name=CourseExamShedule.objects.filter(course_code=i['course_code'])[0]
				course_name=course_name.course_name
			else:
				course_name='-'

			#check for program type to set domain accordingly when hall-ticket data is present
			if 'student_name' in i.keys():
				if i['student_name'] == '-':
					pg_code = i['student_reg'][4:8]
					pg = Program.objects.get(program_code=pg_code)

				else:
					pg_code = i['student_name'][4:8]
					pg = Program.objects.get(program_code=pg_code)

				if pg.program_type == 'non-specific':

					if i['semester_name'] != '-':
						domain = 'Non-Specific'+'-'+i['ex_type']+'-'+i['semester_name']
					else:
						domain = 'Non-Specific'+'-'+i['ex_type']+'-'+i['sem_name']

				elif pg.program_type == 'certification':
					domain = pg_code+'-'+i['batch_name']+'-'+i['ex_type']

				else:
					if i['semester_name'] != '-':
						domain = pg_code+'-'+i['batch_name']+'-'+i['ex_type']+'-'+i['semester_name']
					else:
						domain = pg_code+'-'+i['batch_name']+'-'+i['ex_type']+'-'+i['sem_name']

			#check for program type to set domain accordingly when no hall-ticket data
			else:

				pg_code = i['student_reg'][4:8]
				pg = Program.objects.get(program_code=pg_code)

				if pg.program_type == 'non-specific':
					domain = 'Non-Specific'+'-'+'-'+'-'+i['sem_name']

				elif pg.program_type == 'certification':
					domain = pg_code+'-'+i['b_name']+'-'+'-'

				else:
					domain = pg_code+'-'+i['b_name']+'-'+'-'+'-'+i['sem_name']

			#csv generation when data is from hall-ticket
			if 'student_name' in i.keys():
				if i['student_name'] =='-':
					stud_name = i['student_reg']
					stud_email_id = i['st_email_id']
					row = [stud_name.split(" ")[0],i['st_name'], stud_email_id, i['stud_personal_email'],domain, i['course_code']+':'+course_name,i['stud_personal_phone'],'-']
				else:
					if 'venue_short_name' in i.keys():
						if i['venue_short_name']=='-':
							if 	i['exam_venue_name']=='-':
								created_on_date='-'
							else:
								if 'created_on' in i.keys():
									created_on_date=i['created_on']
								else:
									created_on_date=i['created_on_y']
							row = [i['s_id'],i['stud_name'], i['stud_email_id'],i['stud_personal_email'],domain,i['course_code']+':'+course_name,i['stud_personal_phone'],'-']
						else:
							stud_name = i['stud_name']
							cour = i['course_code']
							hall_tic = 'Yes'
							if 'created_on' in i.keys():
								created_on_date=i['created_on']
							else:
								created_on_date=i['created_on_y']
							row = [i['s_id'], stud_name, i['stud_email_id'],i['stud_personal_email'],domain, cour,i['stud_personal_phone'], i['exam_slot_name_dt_first']]					

			#csv generation when data is from student regisration
			else:
				stud_name = i['student_reg']
				row = [stud_name.split(" ")[0], i['st_name'],i['st_email_id'],i['st_personal_email'],domain,i['c_code']+':'+course_name, i['st_personal_phone'], '-']

			writer.writerow(row)
		return response


	def get(self, request, *args, **kwargs):
		if 'filter-ht' in request.GET:
			return self.form_validation(request, self.form_valid)

		elif 'report_csv' in request.GET:
			return self.form_validation(request, self.csv_form_valid)

		elif 'wheebox_extract' in request.GET:
			return self.form_validation(request, self.csv_wheebox_data)

		return super(BaseHallTicketAttendanceView, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		users_list=[]
		context = super().get_context_data(**kwargs)
		form = self.get_form_class()(self.request.GET)
		if 'program' in self.request.GET:
				
			
				users_list=get_attenlist_halltcktissue(self,program=dict(self.request.GET)['program'],
															location=self.request.GET.get('location'),
														exam_venue=self.request.GET.get('exam_venue'),
														exam_type=self.request.GET.get('exam_type'),
														exam_slot=self.request.GET.get('exam_slot'),
														date=self.request.GET.get('date'),
														)
		else:
			
				users_list=get_attenlist_halltcktissue(self,program=self.request.GET.get('program'),
															location=self.request.GET.get('location'),
														exam_venue=self.request.GET.get('exam_venue'),
														exam_type=self.request.GET.get('exam_type'),
														exam_slot=self.request.GET.get('exam_slot'),
														date=self.request.GET.get('date'),
														)
				# context['init_form_value'] = CurrentExam.objects.filter(is_active=True,)[0].program_id
		# users_list=get_attenlist_halltcktissue(self,program__in=dict(self.request.GET)['program'],
		# 													location=self.request.GET.get('location'),
		# 												exam_venue=self.request.GET.get('exam_venue'),
		# 												exam_type=self.request.GET.get('exam_type'),
		# 												exam_slot=self.request.GET.get('exam_slot'),
		# 												date=self.request.GET.get('date'),
		# 												)

		page = self.request.GET.get('page', 1)

		paginator = Paginator(users_list, 10)
		try:
			users = paginator.page(page)
		except PageNotAnInteger:
		    users = paginator.page(1)
		except EmptyPage:
		    users = paginator.page(paginator.num_pages)

		context['users'] = users
		context['total_no'] = paginator.count
		context['serch'] = self.request.GET.get('search','')
		return context


class StudentsWithoutHallticketView(FormView):
	form_class = ProgramForm

	def get_initial(self):
		initial = super().get_initial()
		# When the user select the multiple programs
		if self.request.GET.get('program'):
			initial['program'] = dict(self.request.GET)['program']
		else:
			pass

		if self.request.GET.get('exam_slot'):
			initial['exam_slot'] = dict(self.request.GET)['exam_slot']
		else:
			pass
		return initial

	def form_valid(self, form):
		return self.render_to_response(self.get_context_data(form=form,))

	def form_validation(self, request, valid_reference):
		form = self.get_form_class()(request.GET)
		if form.is_valid():
			return valid_reference(form)
		else:
			return self.form_invalid(form)

	def queryset_without_hallticket(self):
		ce = CurrentExam.objects.filter(is_active=True,).select_related('program','semester','batch','exam_type')
		if self.request.GET.get('program'):
			if self.request.GET.get('program') != 'undefined':
				ce = ce.filter(program__in=dict(self.request.GET)['program'])
		if ce.exists():
			is_active_student = functools.reduce(operator.or_,
			(
				Q(
					program_code=x.program.program_code,
					semester=x.semester,
					student__batch=x.batch,
					exam_type=x.exam_type,
				) for x in ce.iterator()
			)
			)


			is_student_reg = functools.reduce(operator.or_,
			(
				Q(
					program_code=x.program.program_code,
					semester=x.semester,
					student__batch=x.batch,
				) for x in ce.iterator()
			)
			)
			generated_hall_ticket = HallTicket.objects.filter(is_cancel=False,).annotate(
										program_code=Substr('student__student_id', 5, 4),
										course_code=F('course__course_code'),)
			generated_hall_ticket = generated_hall_ticket.filter(is_active_student).exclude(exam_slot_id=1)


			sr = StudentRegistration.objects.annotate(student_reg=Concat('student__student_id', Value(' ('), 'student__student_name', Value(')')),
													student_name = F('student__student_name'),
													csv_semester_name = F('semester__semester_name'),
													csv_personal_email = F('student__personal_email'),
													csv_personal_phone = F('student__personal_phone'),
													program_code=Substr('student__student_id', 5, 4),
													b_name=F('student__batch__batch_name')).order_by('student__student_id')


			query = sr.filter(is_student_reg)
			if self.request.GET.get('search'):
				search_name = CourseExamShedule.objects.filter(
					course_name__icontains=self.request.GET.get('search').strip()).values_list('course_code', flat=True)
				query = query.filter(Q(student_reg__icontains=self.request.GET.get('search').strip()) | Q(
					course_code__icontains=self.request.GET.get('search').strip()) | Q(course_code__in=search_name))

			#From student registration Table we got all hall-tickets that user have't generated
			if self.request.GET.get('exam_slot'):
				if self.request.GET.get('exam_slot') != 'undefined':
					is_active_exam_slots = functools.reduce(operator.or_,
					(
						Q(
							semester=x.semester,
							exam_type=x.exam_type,
						) for x in ce.iterator()
					)
					)
					ces = CourseExamShedule.objects.filter(exam_slot_id__in=dict(self.request.GET)['exam_slot'])
					ces = ces.filter(is_active_exam_slots)
					if ces:
						ces_filter = functools.reduce(operator.or_,
						(
							Q(
								course_code=x.course_code,
								semester=x.semester,
								student__batch=x.batch,
							) for x in ces.iterator()
						)
						)
						query = query.filter(ces_filter)
					else:
						query = pd.DataFrame().to_dict('records')

			if query:
				#with pandas left join with student_registration and generated_hall_ticket 
				sr_query = pd.DataFrame(list(query.values()))
				if generated_hall_ticket:
					genreted_query = pd.DataFrame(list(generated_hall_ticket.values()))
					del genreted_query['program_code']
					df = pd.merge(sr_query, genreted_query,
						how='left', on=['semester_id', 'course_code','student_id'],indicator=True)
					df = df[df._merge != 'both']
					query = df.to_dict('records')
				else:
					#no hall-ticket generated.
					query = sr_query.to_dict('records')
			else:
				query = pd.DataFrame().to_dict('records')
		else:
			query = pd.DataFrame().to_dict('records')
		return query

	def csv_wheebox_data(self, form):
			response = HttpResponse(content_type="text/csv")
			response['Content-Disposition'] = 'attachment;filename=wheebox_data.csv'
			writer = csv.writer(response)
			headers = ['Student ID','Student Name', 'Student Email-ID', 'Personal Email-ID', 'Domain', 'Course Code/ Course Name', 'Personal Phone','Exam Slot']
			writer.writerow(headers)
			query = self.queryset_without_hallticket()
			if query:
				for i in query:
					student_id = i['student_reg'].split(" ")[0]
					if self.request.GET.get('exam_slot'):
						exam_slot = dict(self.request.GET)['exam_slot']
						pro_code_domian = Program.objects.filter(program_code=i['program_code']).first()
						ce = CurrentExam.objects.filter(is_active=True,program__program_code=i['program_code']).values_list('exam_type',flat=True)
						data = CourseExamShedule.objects.filter(course_code=i['course_code'],
											semester=i['semester_id'],
											batch__batch_name=i['b_name'],
											exam_type__in=ce,
											exam_slot__in = list(map(int, exam_slot))).select_related('exam_slot','exam_type')
						exam_type=[]
						ex_slot = []
						if data:
							for e_type in data:
								exam_type.append(e_type.exam_type.exam_type)
								ex_slot.append(str(e_type.exam_slot.slot_date)+' '+str(e_type.exam_slot.slot_day)+ ' '+str(e_type.exam_slot.slot_name))
							ex_slot = ' , '.join(ex_slot)
							exam_type = ' , '.join(exam_type)
							course_name=data[0].course_name
						else:
							exam_type = " "
							ex_slot = " "
							course_name = " "

						if pro_code_domian.program_type == 'non-specific':
							row = [student_id,i['student_name'],i['student_reg'].split(' ')[0]+"@wilp.bits-pilani.ac.in" ,
									i['csv_personal_email'],'Non Specific'+'-'+exam_type+' -'+i['csv_semester_name'],i['course_code']+" : "+course_name,i['csv_personal_phone'],ex_slot]
						elif pro_code_domian.program_type == 'certification':
							row = [student_id,i['student_name'],i['student_reg'].split(' ')[0]+"@wilp.bits-pilani.ac.in" ,
									i['csv_personal_email'],  i['program_code']+'-'+i['b_name'] +'-'+exam_type , i['course_code']+" : "+course_name,i['csv_personal_phone'],ex_slot]
						else:
							row = [student_id,i['student_name'],i['student_reg'].split(' ')[0]+"@wilp.bits-pilani.ac.in" ,
									i['csv_personal_email'],  i['program_code']+'-'+i['b_name'] +'-'+exam_type+'-'+i['csv_semester_name'], i['course_code']+" : "+course_name,i['csv_personal_phone'],ex_slot]

						writer.writerow(row)
					else:
						ces = CourseExamShedule.objects.filter(course_code=i['course_code'],
											semester=i['semester_id'],
											batch__batch_name=i['b_name'],)
						if ces:
							course_name= ces[0].course_name
						else:
							course_name = '-'

						pro_code_domian = Program.objects.filter(program_code=i['program_code']).first()
						if pro_code_domian.program_type == 'non-specific':
							row = [student_id,i['student_name'],i['student_reg'].split(' ')[0]+"@wilp.bits-pilani.ac.in" ,
							i['csv_personal_email'],'Non Specific'+'-'+i['csv_semester_name'],i['course_code']+" : "+course_name,i['csv_personal_phone'],'-']
						elif pro_code_domian.program_type == 'certification':
							row = [student_id, i['student_name'],i['student_reg'].split(' ')[0] + "@wilp.bits-pilani.ac.in",
							  i['csv_personal_email'], i['program_code'] + '-' + i['b_name'] ,i['course_code'] + " : " + course_name, i['csv_personal_phone'],'-']
						else:
							row = [student_id,i['student_name'],i['student_reg'].split(' ')[0]+"@wilp.bits-pilani.ac.in" ,
							i['csv_personal_email'],  i['program_code']+'-'+i['b_name'] +'-'+i['csv_semester_name'], i['course_code']+" : "+course_name,i['csv_personal_phone'],'-']
						writer.writerow(row)
			else:
				pass
			return response

	def get(self, request, *args, **kwargs):
		if 'filter-ht' in request.GET:
			return self.form_validation(request, self.form_valid)
		elif 'wheebox_extract' in request.GET:
			return self.form_validation(request, self.csv_wheebox_data)
		return super(StudentsWithoutHallticketView, self).get(request, *args, **kwargs)

	def get_context_data(self,*args, **kwargs):
		context = super().get_context_data(**kwargs)
		if self.request.GET.get('program') or self.request.GET.get('exam_slot'):
			queryset = self.queryset_without_hallticket()
			page = self.request.GET.get('page', 1)
			paginator = Paginator(queryset, 10)
			try:
				users = paginator.page(page)
			except PageNotAnInteger:
			    users = paginator.page(1)
			except EmptyPage:
			    users = paginator.page(paginator.num_pages)
			context['table'] = users
			context['total_no'] = paginator.count
			context['serch'] = self.request.GET.get('search','')
		else:
			context['table'] = CourseExamShedule.objects.none()
		return context


class BaseCourseExamScheduleView(TemplateView):
	return_table_func = lambda self, *args, **kwargs: couse_exam_schedule_paging(*args, **kwargs)
	template_name = 'master/view-course-exam-schedule.html'
	ajax_url = 'master:ajax:course-exam-schedule-ajax'
	model = CourseExamShedule

	def get_context_data(self,*args, **kwargs):
		
		semester = self.request.GET.get('semester')
		exam_type = self.request.GET.get('exam_type')
		exam_slot = self.request.GET.get('exam_slot')
		query = CourseExamShedule.objects.all()

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
		data = { 'semester':semester, 'exam_type':exam_type, 'exam_slot':exam_slot }
		context = super(BaseCourseExamScheduleView, self).get_context_data(**kwargs)
		CESTable = self.return_table_func(ajax_url=self.ajax_url, **data)
		context['table'] = CESTable(query)
		context['form'] = course_exam_schedule_form(data)
		context['header_title'] = 'View Course Exam Schedule Details'
		return context



class BaseHallTicketPDF(PDFTemplateView):
	#template_name = 'master/pdf/hall_ticket.html'
	pdf_kwargs = {'encoding' : 'utf-8',}

	def get_student_id(self,**kwargs):
		return kwargs.get('student_id') or None

	def get_context_data(self, **kwargs):
		student_id = self.get_student_id(**kwargs)
		context = super().get_context_data(
			pagesize="A4",
			title="Hall Ticket",
			**kwargs)
		student_info = get_instance_or_none(Student, student_id=student_id)
		program_info = get_instance_or_none(Program, **{"program_code":student_info.student_id[4:8]})
		semester_info = get_instance_or_none(Semester, **{'pk': kwargs.get('sem')})
		ce = CurrentExam.objects.filter(program=program_info, semester=semester_info, is_active=True, batch=student_info.batch)
		#Suppose for the existing ones,template is added for EC3 Makeup and not for EC3 Regualr or vice versa
		if ce[0].hall_tkt_template:
			self.template_name = 'master/pdf/{0}'.format(ce[0].hall_tkt_template)
		#Suppose for the exam type EC3 Grade Awaited only one entry will come in queryset
		elif ce[1]:
			if ce[1].hall_tkt_template:
				self.template_name = 'master/pdf/{0}'.format(ce[1].hall_tkt_template)
			else:
				self.template_name = 'master/pdf/hall_ticket.html'
		#For the existing once still templates are not added for both EC3 Makeup and EC3 Regular then take the default
		else:
			self.template_name = 'master/pdf/hall_ticket.html'
		context['student'] = student_info

		batch_info = student_info.batch
		slt_info = CurrentExam.objects.filter(program = program_info,semester= semester_info,batch=batch_info,is_active = True)
		context['sloot'] = slt_info[0]


		ce_queryset = CurrentExam.objects.filter(program = program_info, is_active = True)
		if (program_info.program_type == Program.NON_SPECIFIC):
			ce_queryset = ce_queryset.filter(batch = student_info.batch, semester = semester_info)
		elif(program_info.program_type == Program.CERTIFICATION):
			ce_queryset = ce_queryset.filter(batch = student_info.batch, semester__semester_name = S.SEMESTER_NAME)
		else:
			ce_queryset = ce_queryset.filter(batch = student_info.batch, semester = semester_info)

		is_active_sem_exmtype = functools.reduce(operator.or_,
		(
			Q(
				student = student_info,
				semester=x.semester,
				exam_type=x.exam_type,
				is_cancel=False,
			) for x in ce_queryset.iterator()
		)
		)

		context['hall_ticket_data'] = HallTicket.filter_hallticket.filter(is_active_sem_exmtype).annotate(
				custom_order=Case(
						When(Q(course__exam_slot__slot_name__contains="FN") | Q(course__exam_slot__slot_name__contains="FORENOON"), then=Value(1)),
						When(Q(course__exam_slot__slot_name__contains="AN") | Q(course__exam_slot__slot_name__contains="AFTERNOON"), then=Value(2)),
						output_field=IntegerField(),
						)
			).order_by('course__exam_slot__slot_date', 'custom_order')
		# fetch_days=set([x.exam_slot.slot_date for x in context['hall_ticket_data']])
		context["semester_default"] = S.SEMESTER_NAME
		context['program'] = program_info
		context['exam_type_values'] = context['hall_ticket_data'].values_list('exam_type__evaluation_type','exam_type__exam_type')
		return context

class BaseStudentPhotoView(TemplateView):
	template_name = 'master/photo_view.html'

	def get_context_data(self, **kwargs):
		student_id = kwargs.get('student_id') or None
		context = super().get_context_data(**kwargs)
		student = get_instance_or_none(Student, student_id=student_id)
		context['title'] = F'{student_id}'
		context['photo'] = student.photo
		return context

class BaseSyncSDMSEmailandPhone(FormView):
    template_name = 'master/sync_sdms_email_and_phone.html'
    form_class = SyncSDMSEmailandPhoneForm

    def get_initial(self):
        self.initial['program'] = self.request.GET.get('program')
        self.initial['program_type'] = self.request.GET.get('program_type')
        self.initial['student-miss-check'] = self.request.GET.get('student-miss-check')
        return self.initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('program'):
            program_data = Program.objects.filter(id=self.request.GET.get('program'))[0]
            students_data = Student.objects.filter(student_id__icontains=program_data.program_code)
            if self.request.GET.get('student-miss-check') == 'std_check':
                students_data = students_data.filter(Q(personal_email__isnull=True)|Q(personal_email__exact='')|Q(personal_phone__isnull=True)|Q(personal_phone__exact=''))

        if self.request.GET.get('program_type'):
            program_data = Program.objects.filter(program_type=self.request.GET.get('program_type')).values_list('program_code', flat=True).distinct()
            students = Student.objects.all()
            if self.request.GET.get('student-miss-check') == 'std_check':
                students = students.filter(Q(personal_email__isnull=True)|Q(personal_email__exact='')|Q(personal_phone__isnull=True)|Q(personal_phone__exact=''))
            students_data= []
            for pg_code in program_data:
                std_data = students.filter(student_id__icontains=pg_code)
                students_data.extend(std_data)
        if 'sync' in self.request.GET:
            job = sync_sdms_email_and_phone.delay(students_data)
        return context

    def get(self, request, *args, **kwargs):
        return super(BaseSyncSDMSEmailandPhone, self).get(request, *args, **kwargs)

class BaseBulkActivateInactivate(FormView):
	template_name = 'master/bulk_activate_inactivate.html'
	form_class = BulkActivateInactivateForm


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		query = CurrentExam.objects.all()
		entries = None
		deactivate_count=None

		if self.request.method == 'POST':

			if self.request.POST.get('program_type'):
				query = query.filter(program__program_type=self.request.POST.get('program_type'))
			if self.request.POST.get('program'):
				to_dict = dict(self.request.POST)
				prgms = to_dict['program']
				prms_list = [int(i) for i in prgms]
				query = query.filter(program__in=prms_list)
			if self.request.POST.get('semester'):
				query = query.filter(semester__semester_name=self.request.POST.get('semester'))
			if self.request.POST.get('evaluation_type'):
				query = query.filter(exam_type__evaluation_type=self.request.POST.get('evaluation_type'))
			if self.request.POST.get('exam_type'):
				query = query.filter(exam_type=int(self.request.POST.get('exam_type')))
			if self.request.POST.get('batch'):
				query = query.filter(batch__batch_name=self.request.POST.get('batch'))

			if self.request.POST.get('enable1') == 'Enable or Activate':
				if query:

					deactivate_count=0
					current_exam_info = CurrentExam.objects.filter(Q(program__program_type=self.request.POST.get('program_type'), semester__semester_name=self.request.POST.get('semester'), is_active=True),~Q(exam_type__evaluation_type=self.request.POST.get('evaluation_type')))

					if self.request.POST.get('batch'):
						current_exam_info= current_exam_info.filter(batch__batch_name=self.request.POST.get('batch'))
					if self.request.POST.get('program'):
						to_dict = dict(self.request.POST)
						prgms = to_dict['program']
						prms_list = [int(i) for i in prgms]
						current_exam_info = current_exam_info.filter(program__in=prms_list)
					if self.request.POST.get('exam_type'):
						et=ExamType.objects.get(id=int(self.request.POST.get('exam_type')))
						current_exam_info = current_exam_info.filter(exam_type__exam_type__icontains=et.exam_type.split(" ")[1])

					for j in current_exam_info:
						j.is_active=0
						j.hall_tkt_change_flag=0
						j.missing_tkt_exception_flag=0
						j.save()
						deactivate_count+=1
				else:
					deactivate_count=0
				if 'chckbox1' in self.request.POST:
					count=0

					for i in query:


						if i.hall_tkt_change_flag==0:
							i.is_active=1
							i.hall_tkt_change_flag=1
							i.missing_tkt_exception_flag=0
							i.save()
							count+=1

					entries = count
				elif 'chckbox2' in self.request.POST:
					count=0
					for i in query:
						if i.missing_tkt_exception_flag==0:
							i.is_active=1
							i.missing_tkt_exception_flag=1
							i.hall_tkt_change_flag=0
							i.save()
							count+=1
					entries = count
				else:
					count =0
					for i in query:
						if i.is_active ==0 or i.hall_tkt_change_flag==1 or i.missing_tkt_exception_flag==1:
							i.is_active=1
							i.hall_tkt_change_flag=0
							i.missing_tkt_exception_flag=0
							i.save()
							count+=1
					entries = count
			if self.request.POST.get('disabled') == 'yes':
				count = 0
				deactivate_count = 0
				for i in query:
					if i.is_active==1 or i.hall_tkt_change_flag==1 or i.missing_tkt_exception_flag==1:
						i.is_active=0
						i.hall_tkt_change_flag=0
						i.missing_tkt_exception_flag=0
						i.save()
						count+=1
				entries = count
			
			entries=entries + deactivate_count

		context['entries'] = entries
		
		return context



