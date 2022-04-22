from django.shortcuts import render, redirect
from django.db.models.functions import Concat
from django.db import IntegrityError, transaction
from .permissions import EMAUserPermissionMixin, CheckHallTicketConditionsMixin
from django.views.generic import View,FormView,TemplateView
from django.urls import reverse_lazy
from .forms import *
from .tables import *
from django.db.models import CharField
from django.db.models import Value, F, Q, Sum, When, OuterRef, Subquery
from master.views import *
from django.forms import modelformset_factory
from django.http import JsonResponse
from ema import default_settings as S
from master.utils.extra_models.querysets import *
import functools
import operator
from .api.student import student_photo_api, get_sdms_student_details
from PIL import Image,ImageFile
from django.core.files import File
from tempfile import NamedTemporaryFile
from master.utils.storage import document_extract_file
from django.http import HttpResponse
import magic
from django.utils import timezone
from .utils import *
import datetime
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.db import connection
import numpy as np


from django.conf import settings
ImageFile.LOAD_TRUNCATED_IMAGES = True

class StudentPhotoView(EMAUserPermissionMixin, View):
	def get(self, request, pk, *args, **kwargs):
		student = Student.objects.get(pk=pk)
		if student.photo.name:
			file = document_extract_file(student)
			mime_type = magic.from_buffer(file.getvalue(), mime=True)
			return HttpResponse(file.getvalue(), content_type=mime_type)

class Home(EMAUserPermissionMixin, FormView):
	template_name = 'student/home.html'
	reverse_success_string = 'student:hall-ticket'
	exception_flag = False

	def get_form_class(self, **kwargs):
		return home_form(self.program, self.student)

	def update_student_context_data(self,student_email):
		try:
			student = get_sdms_student_details(student_email)
			if student:
				if (self.student.student_name != student['name']):
					student_params = {'student_name':student['name'],}
					student_info = Student.objects.filter(student_id=self.student.student_id)
					student_info.update(**student_params)
					self.student = get_instance_or_none(Student, **{'student_id':self.student.student_id})
		except Exception as e:
			pass

		
	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		student_id = self.request.user.email.split('@')[0]
		context['student'] = self.student
		context['ce'] = self.ce
		context['ht'] = self.ht
		context['certification_exam_type'] = self.certification_exam_type
		context['no_hallticket_db'] = self.no_hallticket_db
		# for certification we don't have semester dropdown so ajax will not work.so through context we are passing data.
		if self.certification_exam_type:
			ce_queryset = CurrentExam.objects.filter(program=self.program, is_active=True,
													 hall_tkt_change_flag=True, batch=self.student.batch)
			if ce_queryset.exists():
				qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list(
					"exam_type", flat=True).distinct()
				data = HallTicket.objects.filter(student__student_id=student_id, exam_type__in=qu2,
												 is_cancel=False).exclude(exam_slot_id=1).distinct()
				if not data:
					context['cert_url'] = 'student:hall-ticket'
				else:
					context['cert_url'] = 'student:hall-ticket'

			else:
				ce_queryset = CurrentExam.objects.filter(program=self.program, is_active=True,
														 hall_tkt_change_flag=False)
				query1 = HallTicketException.objects.filter(student_id=student_id,
															exception_end_date__gte=datetime.datetime.now().strftime(
																"%Y-%m-%d"))
				query2 = HallTicketException.objects.filter(student_id=student_id,
															exception_end_date=None)
				records = query1 | query2
				if ce_queryset.filter(missing_tkt_exception_flag=True):
					self.ex_f = True
				else:
					self.ex_f = False

				if records.exists():
					qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list(
						"exam_type", flat=True).distinct()
					data = HallTicket.objects.filter(student__student_id=student_id, exam_type__in=qu2,
													 is_cancel=False).exclude(exam_slot_id=1).distinct()

					if not data.exists():
						context['cert_url'] = 'student:hall-ticket'

					else:
						context['cert_url'] = 'student:hall-ticket'

				else:
					if self.ex_f:
						qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("exam_type", flat=True).distinct()

						data = HallTicket.objects.filter(student__student_id=student_id, exam_type__in=qu2, is_cancel=False).exclude(exam_slot_id=1).distinct()
						if not data.exists():
							context['cert_url'] = 'student:hall-ticket'

						else:
							context['cert_url'] = 'student:hall-ticket-preview'
					else:
						context['cert_url'] = 'student:hall-ticket-preview'
		return context

	def get(self, request, *args, **kwargs):

		student_id = request.user.email.split('@')[0]
		self.program = get_instance_or_none(Program, **{"program_code":student_id[4:8]})
		self.student = get_instance_or_none(Student, **{"student_id":student_id})
		self.no_hallticket_db = False


		if not self.student.photo:
			student_photo_api(student_id)

		self.update_student_context_data(request.user.email)

		ce_queryset = CurrentExam.objects.filter(program=self.program, is_active=True, batch=self.student.batch)
		if ce_queryset:
			self.ht = not ce_queryset.filter(hall_tkt_change_flag=True).exists()
		else:
			self.ht = False


		self.ce = not ce_queryset.exists()
		
		if self.ht:
			if ce_queryset.filter(hall_tkt_change_flag=False, missing_tkt_exception_flag=True).exists():

				self.exception_flag = True
				q1 = HallTicketException.objects.filter(Q(student_id=student_id, exception_end_date__gte=datetime.datetime.now().strftime ("%Y-%m-%d")) | Q(student_id=student_id, exception_end_date=None))
				q2 = HallTicketException.objects.filter(student_id=student_id, exception_end_date=None)
				q = q1 | q2

				if not q.exists():

					qu1 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("semester", flat=True).distinct()

					qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("exam_type", flat=True).distinct()

					data = HallTicket.objects.filter(student=self.student, semester__in=qu1, exam_type__in=qu2, is_cancel=False).exclude(exam_slot_id=1).distinct()

					

					if not data.exists():
						
						self.ht = False

					else:
						pass
			
			else:
				self.exception_flag = False


				qu1 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("semester", flat=True).distinct()

				qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("exam_type", flat=True).distinct()

				data = HallTicket.objects.filter(student=self.student, semester__in=qu1, exam_type__in=qu2, is_cancel=False).exclude(exam_slot_id=1).distinct()

				if not data.exists():
					pass
				
				else:
					self.no_hallticket_db = True


		
		else:
			pass
			#Student will be able to choose semester and proceed to generate hall ticket.
			#Student will also be able to modify their hall ticket


		self.certification_exam_type = functools.reduce(lambda x,y:"{0}, {1}".format(x,y) if y else "{0}".format(x),
			list(ce_queryset.values_list("exam_type__exam_type", flat=True) if ce_queryset.count() else ['-',])) if self.program.program_type == Program.CERTIFICATION else ""


		if request.is_ajax():
			response_data={}
			form = self.get_form_class()(request.GET)
			if form.is_valid():

				semester = form.cleaned_data['semester'].pk

				selected_rec = ce_queryset.filter(semester=semester)

				if selected_rec.filter(hall_tkt_change_flag=True).exists():  #check before selecting sem also

					response_data['enabled'] = True
					response_data['url'] = 'student:hall-ticket'
					return JsonResponse(response_data)

				else:
					#check exception table with SEMESTER and STUD_ID
					query1 = HallTicketException.objects.filter(student_id=student_id, exception_end_date__gte=datetime.datetime.now().strftime ("%Y-%m-%d") , semester__id=semester)
					query2 = HallTicketException.objects.filter(student_id=student_id, semester__id=semester, exception_end_date=None)
					records = query1 | query2

					if selected_rec.filter(missing_tkt_exception_flag=True):
						self.ex_f = True
					else:
						self.ex_f = False
					

					if records.exists():
						#check HallTicket with STUD_ID, SEMESTER and EXAM_TYPE
						
						qu1 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("semester", flat=True).distinct()

						qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("exam_type", flat=True).distinct()

						data = HallTicket.objects.filter(student__student_id=student_id, semester=semester, exam_type__in=qu2, is_cancel=False).exclude(exam_slot_id=1).distinct()

						if not data.exists():

							response_data['enabled'] = True
							response_data['url'] = 'student:hall-ticket'
							return JsonResponse(response_data)

						else:
							response_data['enabled'] = True
							response_data['url'] = 'student:hall-ticket'
							return JsonResponse(response_data)

					else:

						if self.ex_f:
							#check hall ticket then allow to generate
							qu1 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("semester", flat=True).distinct()

							qu2 = CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True).values_list("exam_type", flat=True).distinct()

							data = HallTicket.objects.filter(student__student_id=student_id, semester=semester, exam_type__in=qu2, is_cancel=False).exclude(exam_slot_id=1).distinct()

							if not data:

								response_data['enabled'] = True
								response_data['url'] = 'student:hall-ticket'

								return JsonResponse(response_data)

							else:
								response_data['enabled'] = True
								response_data['url'] =  'student:hall-ticket-preview'
								return JsonResponse(response_data)

						else:
							response_data['enabled'] = True
							response_data['url'] =  'student:hall-ticket-preview'
							return JsonResponse(response_data)


		if 'view-courses' in request.GET :

			form = self.get_form_class()(request.GET)
			if form.is_valid():

				return redirect(reverse_lazy(request.GET.get('url'), 
						kwargs={
							'semester':form.cleaned_data['semester'].pk,
						}
					)
				)
			else:
				return self.render_to_response(self.get_context_data(form=form))


		else:
			return super().get(request, *args, **kwargs)


class HallTicketView(EMAUserPermissionMixin, CheckHallTicketConditionsMixin, FormView):
	template_name = 'student/hall-ticket-details.html'
	prefix = 'hallticket'
	success_url = 'student:student-hall-ticket.pdf'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['hide_crop'] = True
		context['semester'] = self.semester
		# context['exam_type'] = self.exam_type
		context['student'] = self.student
		context['stud_reg'] = self.stud_reg
		context['program_code'] = self.program.program_code

		check_for_image = check_valid_image(self.student)
		if check_for_image=='crop_required':
			context['hide_crop'] = False
		elif check_for_image=='crop_not_required':
			context['hide_crop'] = True
		elif check_for_image=='incorrect_format':
			context['incorrect_format'] = True
		if 'formset' not in context:
			context['formset'] = self.get_form()
		return context

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['queryset'] = HallTicket.objects.none()
		return kwargs

	def get_initial(self):
		return self.initial_form_data

	def get_initial_form_data(self):

		if self.stud_reg.exists():

			ht_queryset = HallTicket.filter_hallticket.annotate(
						custom_order=Case(
						When(Q(exam_slot__slot_name__contains="FN") | Q(exam_slot__slot_name__contains="FORENOON"), then=Value(1)),
						When(Q(exam_slot__slot_name__contains="AN") | Q(exam_slot__slot_name__contains="AFTERNOON"), then=Value(2)),
						output_field=IntegerField(),
						)
						   )

			ht_queryset = ht_queryset.filter(
				functools.reduce(operator.or_,
					(Q(course__course_code=q.course_code, course__semester=q.semester, student=q.student, semester=q.semester) for q in self.stud_reg.iterator())
				),	
				is_cancel=False,
			).distinct().order_by('exam_slot__slot_date', 'exam_slot__slot_start_time', 'custom_order') 

			initial_list = [
				{
					'id': x.pk,
					'course': x.course,
					'course_code': x.course.course_code,
					'course_name': x.course.course_name,
					'student': x.student,
					'semester': x.semester,
					'exam_type':x.exam_type,
					'exam_slot':x.exam_slot,
					'exam_venue':x.exam_venue,
					'location':x.exam_venue.location
					# 'custom_order_field':x.exam_slot.slot_date
				} for x in ht_queryset.iterator()
			]

			if ht_queryset.exists():
				self.stud_reg = self.stud_reg.exclude(
					functools.reduce(operator.or_,
						(Q(course_code=q.course.course_code, student=q.student, semester=q.semester) for q in ht_queryset.iterator())
					)
				).distinct()

				

			initial_list += [
				{
					'course_code': x.course_code,
					'course_name': x.course_name, 
					'student': x.student,
					'semester': x.semester,
				} for x in self.stud_reg.iterator() if x]

		else:
			initial_list = []

		return initial_list

	def get_form_class(self):
		params = {
			# 'exam_type':self.exam_type, 
			'semester':self.semester, 
			'program':self.program, 
			'stud_reg':StudentRegistration.objects.filter(student=self.student,
			 semester=self.semester,
			 # course_code__in = Subquery(
				# CourseExamShedule.objects.filter(
				# 	semester = self.semester, 
				# 	# exam_type = self.exam_type
				# 	).values('course_code'))
			 ), 
			'student':self.student,
			'ce_details':self.current_exam,
			'ces_details':self.ces,
		}

		return modelformset_factory(HallTicket, 
			form=get_hall_ticket_detail_form(**params), 
			formset=HallTicketDetailFormSet,
			extra=len(self.initial_form_data),can_delete=True,
			)

		

	def form_invalid(self, formset):
		"""If the form is invalid, render the invalid form."""
		return self.render_to_response(self.get_context_data(formset=formset))

	def form_valid(self, formset):
		if 'preview' in self.request.POST:
			
			l = formset.cleaned_data



			
			self.template_name = 'student/preview_hall_ticket.html' #preview template
			
			return self.render_to_response(self.get_context_data(formset=formset, abc=[]))
		elif 'revert' in self.request.POST:
			return self.render_to_response(self.get_context_data(formset=formset))
		elif 'save-hall-ticket' in self.request.POST:
			try:
				form_changed = False
				check_image = check_valid_image(self.student)
				if check_image=='crop_required' or check_image=='incorrect_format':
					raise ValueError("Image is Missing or in Incorrect Format. Hall Ticket cannot be Generated")
				for form in formset.forms:

					if form.changed_data:
						form_changed = True

						check_for_hallticket = get_filter_queryset(HallTicket, **{"student__student_id":form.cleaned_data['student'].student_id,"is_cancel":False,
																	'course__course_code':form.cleaned_data['course_code']
																	})
						curr_exm = CurrentExam.objects.filter(is_active=True,program__program_code=form.cleaned_data['student'].student_id[4:8]).values_list('exam_type_id',flat=True)
						exam_course_ids = check_for_hallticket.values_list('course__course_code',flat=True)
						OEA = OnlineExamAttendance.objects.filter(student_id=form.cleaned_data['student'].student_id,makeup_allowed=False,semester__semester_name=form.cleaned_data['semester'].semester_name,course_code__in=exam_course_ids,exam_type__in=curr_exm).values_list('course_code',flat=True)
						
						if form.cleaned_data['course_code'] in OEA:
							raise ValueError("You have made Invalid Edits to your Hallticket data.The changes made are hence Rejected")

				with transaction.atomic():
					default_exam_slot = ExamSlot.objects.get(slot_name=S.EXAM_SLOT_NAME)
					default_exam_venue = ExamVenue.objects.get(venue_short_name=S.VENUE_SHORT_NAME)


					is_first_time=True
					for form in formset.forms:
						if form_changed == True:

							if form.cleaned_data:

								if is_first_time:
									ht = HallTicket.objects.filter(
																semester=formset[0].cleaned_data['semester'],
																student=formset[0].cleaned_data['student'],
																is_cancel=False
																)
									for each in ht:
										each.is_cancel = True
										each.cancel_on = timezone.now()
										each.save()
									is_first_time=False

								HallTicket.objects.create(
									semester=form.cleaned_data['semester'],
									course=form.cleaned_data['course'],
									exam_type=form.cleaned_data['exam_type'],
									exam_slot=form.cleaned_data['exam_slot'],
									exam_venue=form.cleaned_data['exam_venue'],
									student=form.cleaned_data['student'],
									is_cancel=False
								)
						else:
							pass

				return self.render_to_response(self.get_context_data(formset=formset,
					home=reverse_lazy('student:index'),
					success_url=reverse_lazy(self.success_url,kwargs={'sem':self.kwargs.get('semester')})))

			except Exception as e:
				error_massage={'message':e}
				return self.render_to_response(self.get_context_data(formset=formset,error=error_massage))


	def initial_instances(self, request, semester):
		student_id = request.user.email.split('@')[0]
		self.semester = get_instance_or_none(Semester, **{"pk":semester})
		self.student = get_instance_or_none(Student, **{"student_id":student_id})
		self.program = get_instance_or_none(Program, **{"program_code":student_id[4:8]})

		self.current_exam = CurrentExam.objects.filter(is_active=True, batch=self.student.batch,
			program=self.program, semester=self.semester,
		)
		exam_venue_lock = ExamVenueLock.objects.filter(student_id=student_id, semester_id=self.semester, lock_flag=1).values_list('exam_venue', flat=True)
		if exam_venue_lock:
			evsm_lock_exam_types = ExamVenueSlotMap.objects.filter(exam_venue__in=exam_venue_lock).values_list('exam_type', flat=True)
			self.current_exam = self.current_exam.filter(exam_type__in=evsm_lock_exam_types)

		self.ces = CourseExamShedule.objects.filter(
			functools.reduce(operator.or_,(
				Q(
					exam_type=q.exam_type, 
					batch=q.batch, 
					semester=q.semester
					) for q in self.current_exam.iterator()
				)
			),
			# course_code__in=Subquery(self.stud_reg.values('course_code'))
		)  if self.current_exam  else  CourseExamShedule.objects.none()

		self.stud_reg = StudentRegistration.objects.filter(
			student = self.student, 
			semester = self.semester,
			).annotate(
			course_name = Subquery(CourseExamShedule.objects.filter(
				course_code=OuterRef('course_code'),
				# semester=self.semester,
				# batch=self.student.batch,
				).values('course_name')[:1]),
		)

		self.initial_form_data = self.get_initial_form_data()


	def get(self, request, semester, *args, **kwargs):
		if request.META.get('HTTP_REFERER'):
			self.initial_instances(request, semester)
			return super().get(request, *args, **kwargs)
		else:
			return HttpResponseRedirect(reverse_lazy('student:index'))

	def post(self, request, semester, *args, **kwargs):
		self.initial_instances(request, semester)
		# if 'print-hall-ticket' in self.request.POST:
		# 	return HttpResponseRedirect(reverse_lazy('student:hall-ticket-pdf'))
		return super().post(request, *args, **kwargs)


class StudentHallTicketPDF(EMAUserPermissionMixin,BaseHallTicketPDF):
	
	def get_student_id(self,**kwargs):
		return self.request.user.email.split('@')[0]


class PhotoUpdateView(EMAUserPermissionMixin,View):
	form_class = PhotoEditForm

	def get_form_kwargs(self):
		kwargs = {}

		if self.request.method in ('POST', 'PUT'):
			kwargs.update({
				'data': self.request.POST,
				'files': self.request.FILES,
			})
		return kwargs

	def post(self, request, pk, *args, **kwargs):
		if request.is_ajax():
			student = Student.objects.get(pk=pk)
			form = self.form_class(**self.get_form_kwargs())

			if form.is_valid():
				tmp_file = NamedTemporaryFile(delete=True)
				x = form.cleaned_data.get('x')
				y = form.cleaned_data.get('y')
				w = form.cleaned_data.get('width')
				h = form.cleaned_data.get('height')
				r = form.cleaned_data.get('rotate')

				with Image.open(document_extract_file(student)) as image:
					rotated_image = image.rotate(r*(-1), expand=1)
					crop_image = rotated_image.crop((x, y, w+x, h+y))
					resized_image = crop_image.resize((150, 150), Image.ANTIALIAS)
					resized_image.save(tmp_file, format=image.format)
				student.photo = File(tmp_file, name='{0}.{1}'.format(student.student_id,image.format))
				image_data_as_matrix = np.array(resized_image)
				if settings.ENABLE_FACE_DETECTION and not check_for_face(image_data_as_matrix):
					return JsonResponse({'success':False})

				student.save()
				return JsonResponse({'success':True,'image_url':reverse_lazy('student:photo-view', kwargs={'pk':student.pk})})
			return JsonResponse({'success':False,})


class onlineexamatandancestatus(EMAUserPermissionMixin,TemplateView):
	template_name = 'student/online_exam_attandancestatus.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		student_id = str(self.request.user.email).split('@')[0]
		context['onlineexamatandance'] = OnlineExamAttendance.objects.filter(student_id=student_id)
		return context

@method_decorator([login_required(login_url=settings.LOGIN_URL, redirect_field_name='target'),], name='dispatch')
class examschedule(TemplateView):
	template_name='student/exam_schedule.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		student_id = str(self.request.user.email).split('@')[0]

		ce_id=CurrentExam.objects.filter(program__program_code=student_id[4:8], is_active=True)
		if ce_id.exists():
			stud_cour=StudentRegistration.objects.filter(student__student_id=student_id, semester__in=ce_id.values_list('semester', flat=True) )
			if stud_cour.exists():
				cour_ext=CourseExamShedule.objects.filter(course_code__in=stud_cour.values_list('course_code',flat=True) ,semester__in=stud_cour.values_list('semester',flat=True) ,batch=stud_cour[0].student.batch)
				
				cour_ext = cour_ext.filter(exam_type__in=ce_id.values_list('exam_type', flat=True), semester__in=ce_id.values_list('semester', flat=True), 
						batch__in=ce_id.values_list('batch', flat=True))
				context['exam_schedule'] = cour_ext.order_by('course_name', 'course_code', 'exam_slot__slot_date', 'exam_slot__slot_start_time')
			else:
				context['exam_schedule'] = stud_cour.none()
		else:
			context['exam_schedule']=ce_id.none()
		return context
