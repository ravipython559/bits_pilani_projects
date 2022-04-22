from django.contrib import admin,messages
from django.utils.html import format_html
from master.models import *
from django.contrib.admin import AdminSite as BaseAdminSite
from django.utils.translation import ugettext_lazy as _
from master.forms.admin_forms import *
from master.bulk_import_export.resources import *
from django.db.models.functions import Lower
from import_export.admin import ImportMixin,ImportExportMixin,ImportExportModelAdmin
import datetime
from django.utils import timezone
from django.urls import path
from ema.default_settings import *  

class AdminSite(BaseAdminSite):
	site_title = _('Exam Management Application Site Title')
	site_header = _('Exam Management Application Headers')
	index_title = _('Exam Management Application')

admin_site = AdminSite(name='master_admin')


class AdminExamSlot(admin.ModelAdmin):
	form = ExamSlotForm

	def get_queryset (self, request):
		qs = super().get_queryset(request)
		return qs.exclude(slot_name = EXAM_SLOT_NAME)

	def slot_day(self, obj):
		return obj.slot_date.strftime("%A")

	def slot_start_time_format(self, obj):
		return obj.slot_start_time.strftime("%H:%M")

	slot_start_time_format.short_description = 'Slot Start Time'

	list_per_page = 15
	list_display = ('slot_name', 'slot_date', 'slot_day', 'slot_start_time_format',)
	fields = ['slot_name', 'slot_date', 'slot_day', 'slot_start_time',]
	list_display_links = ('slot_name',)

	ordering =['pk',]

	def save_model(self, request, obj, form, change):
		super(AdminExamSlot, self).save_model(request, obj, form, change)
		if change == True:
			messages.success(request, 'Record is updated successfully in EMA and QPM.')
		else:
			messages.success(request, 'Record is added successfully in EMA and QPM.')

admin_site.register(ExamSlot,AdminExamSlot)


class AdminBatch(admin.ModelAdmin):
	def get_queryset (self, request):
		qs = super().get_queryset(request)
		return qs.exclude(batch_name = BATCH_NAME)

	list_per_page=15
	list_display = ('batch_name', 'year', 'sem_number', 'application_center_batch',)
	fields = ['batch_name', 'year', 'sem_number', 'application_center_batch',]
	list_display_links = ('batch_name',)
	search_fields=('batch_name',)
	ordering =['pk',]

	def save_model(self, request, obj, form, change):
		super(AdminBatch, self).save_model(request, obj, form, change)
		if change == True:
			messages.success(request, 'Record is updated successfully in EMA and QPM.')
		else:
			messages.success(request, 'Record is added successfully in EMA and QPM.')

admin_site.register(Batch,AdminBatch)


class AdminSemester(admin.ModelAdmin):
	def get_queryset (self, request):
		qs = super().get_queryset(request)
		return qs.exclude(semester_name = SEMESTER_NAME)

	list_per_page=15
	list_display = ('semester_name', 'taxila_sem_name', 'canvas_sem_name',)
	fields = ['semester_name', 'taxila_sem_name', 'canvas_sem_name',]
	list_display_links = ('semester_name',)
	search_fields=('semester_name',)
	ordering =['pk',]

	def save_model(self, request, obj, form, change):
		super(AdminSemester, self).save_model(request, obj, form, change)
		if change == True:
			messages.success(request, 'Record is updated successfully in EMA and QPM.')
		else:
			messages.success(request, 'Record is added successfully in EMA and QPM.')

admin_site.register(Semester,AdminSemester)


class AdminLocation(admin.ModelAdmin):
	def get_queryset (self, request):
		qs = super().get_queryset(request)
		return qs.exclude(location_name = LOCATION)

	list_per_page=15
	list_display = ('location_name',)
	list_display_links = ('location_name',)
	fields = ['location_name',]
	ordering =['pk',]

admin_site.register(Location, AdminLocation)


class AdminExamVenue(admin.ModelAdmin):
	def get_queryset (self, request):
		qs = super().get_queryset(request)
		return qs.exclude(venue_short_name = VENUE_SHORT_NAME)


	list_per_page = 15
	form = ExamVenueForm

	list_display = ('location', 'venue_short_name', 'venue_address','pin_code', 'student_count_limit', 'is_active',)
	list_display_links = ('venue_short_name',)
	fields = ['location', 'venue_short_name', 'venue_address', 'pin_code', 'student_count_limit', 'is_active', ]
	ordering =['pk']

admin_site.register(ExamVenue, AdminExamVenue)


class AdminExamType(admin.ModelAdmin):
	def get_queryset (self, request):
		qs = super().get_queryset(request)
		return qs.exclude(exam_type = EXAM_TYPE)

	fields = ['exam_type', 'evaluation_type',]
	list_display = ('exam_type', 'evaluation_type',)
	list_display_links = ('exam_type',)
	ordering =['pk',]

	def save_model(self, request, obj, form, change):
		super(AdminExamType, self).save_model(request, obj, form, change)
		if change == True:
			messages.success(request, 'Record is updated successfully in EMA and QPM.')
		else:
			messages.success(request, 'Record is added successfully in EMA and QPM.')

admin_site.register(ExamType, AdminExamType)



class AdminLocationCoordinator(admin.ModelAdmin):
	list_per_page=15
	form=LocationCoordinatorForm

	fields = ['coordinator_email_id', 'location', 'name',]
	list_display = ('coordinator_email_id', 'location', 'name',)

admin_site.register(LocationCoordinator,AdminLocationCoordinator)

admin_site.register(Program)


class AdminCourseExamShedule(ImportMixin, admin.ModelAdmin):

	list_per_page=15
	form=CourseExamSheduleForm
	resource_class = ResCourseExamSchedule
	formats = DEFAULT_FORMATS
	search_fields = ('course_code', 'course_name', 'comp_code',)
	list_display = ('semester', 'course_code', 'course_name', 'batch_field', 'comp_code', 'unit', 'exam_type_field', 'exam_slot_field',)
	list_filter = ('semester', 'exam_type', 'exam_slot', )
	list_display_links = ('course_code',)
	import_template_name = 'import_export/import-page.html'
	def response_change(self, request, obj):
		msg = _('''Entry Successfully Saved. A prior entry with the same course code,
			exam type and semester was found and was updated with this entry''')
		self.message_user(request, msg, messages.SUCCESS)
		return self.response_post_save_change(request, obj)

	def batch_field(self, obj):
		return obj.batch

	batch_field.admin_order_field = 'batch__batch_name'
	batch_field.short_description = 'Batch'

	def exam_type_field(self, obj):
		return obj.exam_type

	exam_type_field.admin_order_field = 'exam_type__exam_type'
	exam_type_field.short_description = 'Exam Type'

	def exam_slot_field(self, obj):
		return obj.exam_slot

	exam_slot_field.admin_order_field = 'exam_slot__slot_date'
	exam_slot_field.short_description = 'Exam Slot'

	# def import_action(self, request, *args, **kwargs):
	# 	"""
 #        Perform a dry_run of the import to make sure the import will not
 #        result in errors.  If there where no error, save the user
 #        uploaded file to a local temp file that will be used by
 #        'process_import' for the actual import.
 #        """
	# 	if not self.has_import_permission(request):
	# 		raise PermissionDenied

	# 	context = self.get_import_context_data()

	# 	import_formats = self.get_import_formats()
	# 	form_type = self.get_import_form()
	# 	form_kwargs = self.get_form_kwargs(form_type, *args, **kwargs)
	# 	form = form_type(import_formats,
	# 					 request.POST or None,
	# 					 request.FILES or None,
	# 					 **form_kwargs)

	# 	if request.POST and form.is_valid():
	# 		input_format = import_formats[
	# 			int(form.cleaned_data['input_format'])
	# 		]()
	# 		import_file = form.cleaned_data['import_file']

	# 		csv_reader = csv.reader(codecs.iterdecode(import_file, 'utf-8'))
	# 		try:
	# 			count = 0
	# 			for row in csv_reader:
	# 				count = count + 1
	# 		except Exception as e:
	# 			return HttpResponse('Incorrect string value at row {}'.format(count))

	# 		# first always write the uploaded file to disk as it may be a
	# 		# memory file or else based on settings upload handlers
	# 		tmp_storage = self.write_to_tmp_storage(import_file, input_format)

	# 		# then read the file, using the proper format-specific mode
	# 		# warning, big files may exceed memory

	# 		try:
	# 			data = tmp_storage.read(input_format.get_read_mode())
	# 			if not input_format.is_binary() and self.from_encoding:
	# 				data = force_str(data, self.from_encoding)
	# 			dataset = input_format.create_dataset(data)
	# 		except UnicodeDecodeError as e:
	# 			return HttpResponse(_(u"<h1>Imported file has a wrong encoding: %s</h1>" % e))
	# 		except Exception as e:
	# 			return HttpResponse(
	# 				_(u"<h1>%s encountered while trying to read file: %s</h1>" % (type(e).__name__, import_file.name)))

	# 		# prepare kwargs for import data, if needed
	# 		res_kwargs = self.get_import_resource_kwargs(request, form=form, *args, **kwargs)
	# 		resource = self.get_import_resource_class()(**res_kwargs)

	# 		# prepare additional kwargs for import_data, if needed
	# 		imp_kwargs = self.get_import_data_kwargs(request, form=form, *args, **kwargs)
	# 		result = resource.import_data(dataset, dry_run=True,
	# 									  raise_errors=False,
	# 									  file_name=import_file.name,
	# 									  user=request.user,
	# 									  **imp_kwargs)

	# 		context['result'] = result

	# 		if not result.has_errors() and not result.has_validation_errors():
	# 			initial = {
	# 				'import_file_name': tmp_storage.name,
	# 				'original_file_name': import_file.name,
	# 				'input_format': form.cleaned_data['input_format'],
	# 			}
	# 			confirm_form = self.get_confirm_import_form()
	# 			initial = self.get_form_kwargs(form=form, **initial)
	# 			context['confirm_form'] = confirm_form(initial=initial)
	# 	else:
	# 		res_kwargs = self.get_import_resource_kwargs(request, form=form, *args, **kwargs)
	# 		resource = self.get_import_resource_class()(**res_kwargs)

	# 	context.update(self.admin_site.each_context(request))

	# 	context['title'] = _("Import")
	# 	context['form'] = form
	# 	context['opts'] = self.model._meta
	# 	context['fields'] = [f.column_name for f in resource.get_user_visible_fields()]

	# 	request.current_app = self.admin_site.name
	# 	return TemplateResponse(request, [self.import_template_name],
	# 							context)

	class Media:
		static_url = getattr(settings, 'STATIC_URL', '/static/') 
		js = [ static_url+'ema_static_content/js/list_filter_collapse.js', ]

admin_site.register(CourseExamShedule,AdminCourseExamShedule)


class AdminExamVenueSlotMap(admin.ModelAdmin):
	form = ExamVenueSlotMapForm

	def location(self, obj):
		return obj.exam_venue.location

	def venue_name(self, obj):
		return obj.exam_venue.venue_short_name

	def venue_address(self, obj):
		return obj.exam_venue.venue_address

	def pincode(self, obj):
		return obj.exam_venue.pin_code

	def is_active(self, obj):
		return obj.exam_venue.is_active	

	def exam_slot_value(self,obj):
		return '' if obj.exam_slot.slot_name== '-' else obj.exam_slot

	def exam_type_value(self, obj):
		return '' if obj.exam_type.exam_type == '-' else obj.exam_type

	def custom_add_view(self, request, exam_venue, form_url='', extra_context=None):
		extra_context = extra_context or {}
		extra_context['exam_venue_preselected'] = ExamVenue.objects.get(pk=exam_venue)
		return super().add_view(request, form_url=form_url, extra_context=extra_context)

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('customize-add/<int:exam_venue>/', self.admin_site.admin_view(self.custom_add_view), name='customize-add'),
		]
		return custom_urls + urls

	list_display = ('location', 'venue_name', 'venue_address', 'pincode', 'exam_type_value', 'exam_slot_value', 'student_count_limit', 'is_active')
	search_fields = ('exam_venue__venue_short_name', 'exam_venue__venue_address',)
	list_filter = ('exam_venue__location__location_name','exam_slot__slot_name', 'exam_slot__slot_day', 'exam_slot__slot_date', 'student_count_limit')
	list_display_links = ('venue_name',)

admin_site.register(ExamVenueSlotMap, AdminExamVenueSlotMap)

class AdminCurrentExam(admin.ModelAdmin):
	form = CurrentExamForm

	list_per_page=15
	list_display=('exam_type_field','program_field','semester_field','batch_field','location','is_active','hall_tkt_change_flag', 'missing_tkt_exception_flag','exm_slot_fn','exm_slot_an', 'hall_tkt_template',)
	list_display_links=('program_field',)
	search_fields = ('program__program_code','program__program_name')

	def exam_type_field(self, obj):
		return format_html('{result}<p style = "width:175px;"></p>', result=obj.exam_type)

	exam_type_field.admin_order_field= 'exam_type__exam_type'
	exam_type_field.short_description = 'Exam Type'

	def program_field(self, obj):
		return format_html('{result}<p style = "width:350px;"></p>', result=obj.program)

	program_field.admin_order_field= 'program__program_code'
	program_field.short_description = ('Program')

	def semester_field(self, obj):
		return format_html('{result}<p style = "width:150px;"></p>', result=obj.semester)

	semester_field.admin_order_field = 'semester__semester_name'
	semester_field.short_description = 'Semester'

	def batch_field(self, obj):
		return format_html('{result}<p style = "width:120px;"></p>', result=obj.batch)

	batch_field.admin_order_field = 'batch__batch_name'
	batch_field.short_description = 'Batch'

admin_site.register(CurrentExam, AdminCurrentExam)

# -------- To be commented, Not to be shown to admin ------------

class AdminStudent(ImportMixin, admin.ModelAdmin):
	form = StudentForm
	resource_class = ResStudent
	formats = DEFAULT_FORMATS
	import_template_name = 'import_export/import-page.html'
	search_fields = ('student_id__icontains', 'student_name__icontains', 'batch__batch_name__contains', 'personal_email__icontains')
	list_display = ('student_id', 'student_name', 'batch_field','personal_email', 'personal_phone', 'created_on_field')
	fields = ['student_id', 'student_name', 'batch','personal_email', 'personal_phone']
	list_display_links = ('student_id',)

	def created_on_field(self, obj):
		return obj.created_on

	created_on_field.short_description='Created / Last Updated Datetime'
	created_on_field.admin_order_field='created_on'

	def batch_field(self, obj):
		return obj.batch

	batch_field.admin_order_field = 'batch__batch_name'
	batch_field.short_description = 'Batch'

admin_site.register(Student,AdminStudent)


class AdminStudentRegistration(ImportMixin, admin.ModelAdmin):
	form = StudentRegistrationForm
	resource_class = ResStudentRegistration
	formats = DEFAULT_FORMATS
	change_list_template = 'admin/master/studentregistration/change_list.html'
	list_display = ('course_code', 'student_field', 'semester',)
	fields = ['course_code', 'student', 'semester',]
	list_display_links = ('student_field',)
	search_fields = ('course_code__contains', 'student__student_id__contains', 'semester__semester_name__contains')
	autocomplete_fields = ["student"]
	import_template_name = 'import_export/import-page.html'

	def student_field(self, obj):
		return obj.student

	student_field.admin_order_field = 'student__student_id'
	student_field.short_description = 'Student'

	def get_form(self, request, obj=None, **kwargs):
		form = super(AdminStudentRegistration, self).get_form(request, obj, **kwargs)
		form.base_fields['student'].queryset = Student.objects.all().order_by('student_id')
		return form

admin_site.register(StudentRegistration,AdminStudentRegistration)


class AdminHallTicket(admin.ModelAdmin):
	list_display = ('student_field', 'semester', 'course_field','exam_type_field','exam_slot_field','exam_venue_field','is_cancel',)
	fields = ['student', 'semester', 'course','exam_type','exam_slot','exam_venue','is_cancel',]
	list_display_links = ('student_field',)
	search_fields = ('student__student_id',)
	# def has_delete_permission(self, request, obj=None):
	# 	return False

	def has_add_permission(self, request, obj=None):
		return False

	def has_change_permission(self, request, obj=None):
		return False

	def student_field(self, obj):
		return obj.student

	student_field.admin_order_field = 'student__student_id'
	student_field.short_description = 'Student'

	def course_field(self, obj):
		return obj.course

	course_field.admin_order_field = 'course__course_code'
	course_field.short_description = 'Course'

	def exam_type_field(self, obj):
		return obj.exam_type

	exam_type_field.admin_order_field = 'exam_type__exam_type'
	exam_type_field.short_description = 'Exam Type'

	def exam_slot_field(self, obj):
		return obj.exam_slot

	exam_slot_field.admin_order_field = 'exam_slot__slot_date'
	exam_slot_field.short_description = 'Exam Slot'

	def exam_venue_field(self, obj):
		return obj.exam_venue

	exam_venue_field.admin_order_field = 'exam_venue__venue_short_name'
	exam_venue_field.short_description = 'Exam Venue'

admin_site.register(HallTicket,AdminHallTicket)
# ----------------------------------------------------------------


class OnlineExamAttendanceAdmin(ImportExportMixin,admin.ModelAdmin):
	resource_class = OnlineExamAttendanceResource
	change_list_template = 'admin/master/onlineexamattendance/change_list.html'
	fields = ['student_id','exam_type','course_code','semester',
							'makeup_allowed','course_name','exam_date','total_questions',
							'total_attempted','total_blank','image_uploaded','test_start_time',
							'test_end_time','submission_type',]
	list_display_links = ('student_id','course_code')
	search_fields = ('student_id', 'course_code',)
	list_display = ('student_id','exam_type','course_code','semester',
							'makeup_allowed','course_name','exam_date','total_questions',
							'total_attempted','total_blank','image_uploaded','test_start_time',
							'test_end_time','submission_type',)
	import_template_name = 'import_export/import-page.html'
	form =	OnlineExamAttendanceForm

	def get_import_formats(self):
		formats = (
			base_formats.CSV,
		)
		return [f for f in formats if f().can_export()]

admin_site.register(OnlineExamAttendance,OnlineExamAttendanceAdmin)


class ExamVenueLockAdmin(ImportExportModelAdmin):
	resource_class = ExamVenueLockResource
	change_list_template = 'admin/master/examvenuelock/change_list.html'
	fields = ['student_id','exam_venue','semester', 'lock_flag']
	search_fields = ('student_id', 'exam_venue__venue_short_name',)
	list_display = ('student_id','exam_venue','semester', 'lock_flag',)
	list_display_links = ('student_id',)
	import_template_name = 'import_export/import-page.html'

	def get_import_formats(self):
		formats = (
			base_formats.CSV,
		)
		return [f for f in formats if f().can_export()]

admin_site.register(ExamVenueLock, ExamVenueLockAdmin)


class HallTicketExceptionAdmin(ImportMixin,admin.ModelAdmin):

	resource_class = ResHallTicketException
	formats = DEFAULT_FORMATS
	form=HallTicketExceptionForm
	import_template_name = 'import_export/import-page.html'


	class Media:
		static_url = getattr(settings, 'STATIC_URL', '/static/') 
		js = [ static_url+'ema_static_content/js/list_filter_collapse.js', ]

admin_site.register(HallTicketException, HallTicketExceptionAdmin)


class UploadStudentPhotoAdmin(admin.ModelAdmin):

	def save_model(self, request, obj, form, change):
		stu_obj = Student.objects.get(student_id=obj.student_id)
		if not stu_obj.photo:
			stu_obj.photo = obj.student_photo
			stu_obj.save()
			obj.save()

admin_site.register(UploadStudentPhoto, UploadStudentPhotoAdmin)
