from import_export import resources, widgets
from import_export.fields import Field 
from .models import *
from . import resources_widgets
from .resources_headers import *
from django.core.exceptions import ValidationError


class ResQpSubmission(resources.ModelResource):
	semester = Field(attribute='semester', column_name=QPSUB_HEADER['semester'],
		widget=resources_widgets.ForeignKeyWidget(Semester, 'semester_name')) 
	course_code = Field(attribute='course_code', column_name=QPSUB_HEADER['course_code'], 
		widget=resources_widgets.TextWidget())
	course_name = Field(attribute='course_name', column_name=QPSUB_HEADER['course_name'], 
		widget=resources_widgets.TextWidget())
	faculty_email_id = Field(attribute='faculty_email_id', column_name=QPSUB_HEADER['faculty_email_id'], 
		widget=resources_widgets.EmailWidget())
	email_access_id_1 = Field(attribute='email_access_id_1', column_name=QPSUB_HEADER['email_access_id_1'], 
			widget=resources_widgets.OptionalEmailWidget())
	email_access_id_2 = Field(attribute='email_access_id_2', column_name=QPSUB_HEADER['email_access_id_2'], 
			widget=resources_widgets.OptionalEmailWidget())
	coordinator_email_id_1 = Field(attribute='coordinator_email_id_1', column_name=QPSUB_HEADER['coordinator_email_id_1'],
			widget=resources_widgets.OptionalEmailWidget())
	coordinator_email_id_2 = Field(attribute='coordinator_email_id_2', column_name=QPSUB_HEADER['coordinator_email_id_2'],
			widget=resources_widgets.OptionalEmailWidget())
	exam_type = Field(attribute='exam_type', column_name=QPSUB_HEADER['exam_type'],
		widget=resources_widgets.ForeignKeyWidget(ExamType, 'exam_type'))
	batch = Field(attribute='batch', column_name=QPSUB_HEADER['batch'],
		widget=resources_widgets.BatchForeignKeyWidget(Batch, 'batch_name'))
	program_type = Field(attribute='program_type', column_name=QPSUB_HEADER['program_type'], 
		widget=resources_widgets.ProgramTextWidget())
	exam_slot = Field(attribute='exam_slot', column_name=QPSUB_HEADER['exam_slot'],
		widget=resources_widgets.ForeignKeyWidget(ExamSlot, 'slot_name'))


	def before_import(self, dataset, using_transactions, dry_run, **kwargs):
		# import pdb;pdb.set_trace()
		diff_col = set(self.get_diff_headers()) - set(dataset.headers)
		if diff_col:
			raise ValidationError("Column {} not found in dataset".format(diff_col))

	class Meta:
		model = QpSubmission
		fields = ['semester','course_code', 'course_name', 'faculty_email_id','email_access_id_1','email_access_id_2','coordinator_email_id_1','coordinator_email_id_2','exam_type','batch','program_type','exam_slot',]
		import_id_fields = ('semester','course_code', 'exam_type','batch')
