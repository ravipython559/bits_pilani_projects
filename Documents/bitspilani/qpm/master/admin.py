from django.contrib import admin, messages
from .models import *
from django.contrib.admin import AdminSite as BaseAdminSite
from import_export.admin import ExportMixin, ImportMixin, ImportExportMixin
from django.utils.translation import gettext_lazy as _
from import_export.formats import base_formats
from .resources import *
from .extra_forms import *
import pandas as pd

class AdminSite(BaseAdminSite):
    site_title = _  ('Question Papaer Management Application Site Title')
    site_header = _('Question Papaer Application Headers')
    index_title = _('Question Papaer Application')
    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        ordering = {
            "QP Submissions": 1,
            "Set QP Submission Locks": 2,
            "Semester": 3,
            "Batch": 4,
            "Exam Type": 5,
            "Exam Slot": 6,
            "Staff user access list":7,
        }
        app_dict = self._build_app_dict(request)
        # a.sort(key=lambda x: b.index(x[0]))
        # Sort the apps alphabetically.
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: ordering[x['name']])

        return app_list

# admin_site = AdminSite(name='master')
admin.site = AdminSite()


# class EventAdminSite(AdminSite):
#     def get_app_list(self, request):
#         """
#         Return a sorted list of all the installed apps that have been
#         registered in this site.
#         """
#         ordering = {
#             "QP Submissions": 1,
#             "Set QP Submission Locks": 2,
#             "Semester": 3,
#             "Batch": 4,
#             "Exam Type": 5,
#             "Exam Slot": 6
#         }
#         app_dict = self._build_app_dict(request)
#         # a.sort(key=lambda x: b.index(x[0]))
#         # Sort the apps alphabetically.
#         app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

#         # Sort the models alphabetically within each app.
#         for app in app_list:
#             app['models'].sort(key=lambda x: ordering[x['name']])

#         return app_list
# admin_site = EventAdminSite()

class AdminQpSubmission(ImportMixin, admin.ModelAdmin):
    resource_class = ResQpSubmission
    formats = (base_formats.CSV,)
    form = AdminQpSubmissionForm
    search_fields = ('course_code', 'course_name', 'program_type', 'faculty_email_id', 'email_access_id_1','email_access_id_2', 'coordinator_email_id_1', 'coordinator_email_id_2')
    list_display = ('semester','course_code', 'course_name', 'faculty_email_id', 'email_access_id_1','email_access_id_2','coordinator_email_id_1', 'coordinator_email_id_2','exam_type_field','batch', 'program_type','exam_slot_field','active_flag','submission_locked_flag','acceptance_flag')
    fields = ['semester','course_code', 'course_name', 'faculty_email_id', 'email_access_id_1','email_access_id_2','coordinator_email_id_1', 'coordinator_email_id_2', 'exam_type','batch','program_type','exam_slot','active_flag','submission_locked_flag','acceptance_flag']
    ordering = ('semester__semester_name', 'course_code', 'course_name', 'faculty_email_id', 'exam_type__exam_type', 'batch__batch_name', 'program_type', 'exam_slot__slot_name', 'active_flag','submission_locked_flag',)

    def exam_type_field(self, obj):
        return obj.exam_type

    def exam_slot_field(self, obj):
        return obj.exam_slot

    def changelist_view(self, request, extra_context=None):
        if request.GET.get('_popup'):
            self.list_display = ('course_code', 'course_name',)
        else:
            self.list_display = ('semester','course_code', 'course_name', 'faculty_email_id', 'email_access_id_1','email_access_id_2','coordinator_email_id_1', 'coordinator_email_id_2','exam_type_field','batch', 'program_type','exam_slot_field','active_flag','submission_locked_flag','acceptance_flag')
        return super().changelist_view(request, extra_context)

    def has_import_permission(self, request, obj=None):
        return not request.GET.get('_popup')

    def has_add_permission(self, request, obj=None):
        return not request.GET.get('_popup')

    def get_queryset(self, request):
        qs = super(AdminQpSubmission, self).get_queryset(request)
        if request.GET.get('_popup'):
            df = pd.DataFrame((list(qs.values('course_code', 'course_name', 'id'))))
            val = df.drop_duplicates(subset=['course_code', 'course_name'])

            new_query = qs.filter(id__in=val.id)
            return new_query
        else:
            return qs

    exam_type_field.short_description = 'Exam Type'
    exam_type_field.admin_order_field = 'exam_type__exam_type'

    exam_slot_field.short_description = 'Exam Slot'
    exam_slot_field.admin_order_field = 'exam_slot__slot_date'

admin.site.register(QpSubmission,AdminQpSubmission)

class AdminSetQpSubmissionsLock(admin.ModelAdmin):
    form = SetQpSubmissionsLockForm
    # pass
    list_display = ('semester','batch', 'exam_type', 'lock_flag', 'lock_all_submissions_flag',)

admin.site.register(SetQpSubmissionsLock, AdminSetQpSubmissionsLock)

class AdminExamSlot(admin.ModelAdmin):
    form = ExamSlotForm

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

    # def response_add(self, request, obj, post_url_continue=None):
    #     msg = "Record is added successfully in QPM and EMA."
    #     self.message_user(request, msg, level=messages.SUCCESS)
    #     return self.response_post_save_add(request, obj)

    # def response_change(self, request, obj):
    #     msg = "Record is updated successfully in QPM and EMA."
    #     self.message_user(request, msg, level=messages.SUCCESS)
    #     return self.response_post_save_change(request, obj)

    def save_model(self, request, obj, form, change):
        super(AdminExamSlot, self).save_model(request, obj, form, change)
        if change == True:
            messages.success(request, 'Record is updated successfully in QPM and EMA.')
        else:
            messages.success(request, 'Record is added successfully in QPM and EMA.')

admin.site.register(ExamSlot,AdminExamSlot)

class AdminBatch(admin.ModelAdmin):

    list_per_page=15
    list_display = ('batch_name', 'year', 'sem_number')
    fields = ['batch_name', 'year', 'sem_number']
    list_display_links = ('batch_name',)
    ordering =['pk',]

    def save_model(self, request, obj, form, change):
        super(AdminBatch, self).save_model(request, obj, form, change)
        if change == True:
            messages.success(request, 'Record is updated successfully in QPM and EMA.')
        else:
            messages.success(request, 'Record is added successfully in QPM and EMA.')

admin.site.register(Batch,AdminBatch)

class AdminExamType(admin.ModelAdmin):

    fields = ['exam_type', 'evaluation_type',]
    list_display = ('exam_type', 'evaluation_type',)
    list_display_links = ('exam_type',)
    ordering =['pk',]

    def save_model(self, request, obj, form, change):
        super(AdminExamType, self).save_model(request, obj, form, change)
        if change == True:
            messages.success(request, 'Record is updated successfully in QPM and EMA.')
        else:
            messages.success(request, 'Record is added successfully in QPM and EMA.')

admin.site.register(ExamType, AdminExamType)

# admin.site.register(ExamSlot)
class AdminSemester(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        super(AdminSemester, self).save_model(request, obj, form, change)
        if change == True:
            messages.success(request, 'Record is updated successfully in QPM and EMA.')
        else:
            messages.success(request, 'Record is added successfully in QPM and EMA.')
        

admin.site.register(Semester, AdminSemester)


class AdminStaffUserAccessList(admin.ModelAdmin):
    form = StaffUserAccessListForm
    list_display = ('user_id','created_datetime','created_by_user_id', 'coordinator_flag')
    fields = ['user_id','coordinator_flag']

    def save_model(self, request, obj, form, change):
        obj.created_by_user_id = request.user.email
        super().save_model(request, obj, form, change)
admin.site.register(StaffUserAccessList, AdminStaffUserAccessList)

from django_celery_results.models import TaskResult
from django_celery_results.admin import TaskResultAdmin
admin.site.unregister(TaskResult)

# from django.contrib import auth

# admin.site.unregister(auth.models.User)
# admin.site.unregister(auth.models.Group)
