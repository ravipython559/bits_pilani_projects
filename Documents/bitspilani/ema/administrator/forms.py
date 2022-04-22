from django import forms
from master.models import *
from ema import default_settings as S  
from master.forms.form_fields import SemesterModelChoiceField
from django.db.models.functions import Concat
from django.db.models import Value

class CustomM(forms.ModelMultipleChoiceField):
	def _check_values(self, value):
		"""
		Given a list of possible PK values, return a QuerySet of the
		corresponding objects. Raise a ValidationError if a given value is
		invalid (not a valid PK, not in the queryset, etc.)
		"""
		key = self.to_field_name or 'pk'
		# deduplicate given values to avoid creating many querysets or
		# requiring the database backend deduplicate efficiently.
		try:
			value = frozenset(value)
		except TypeError:
			# list of lists isn't hashable, for example
			raise ValidationError(
			    self.error_messages['list'],
			    code='list',
			)
		for pk in value:
			try:
				self.queryset.filter(**{key: pk})
			except (ValueError, TypeError):
				raise ValidationError(
					self.error_messages['invalid_pk_value'],
					code='invalid_pk_value',
					params={'pk': pk},
				)
		qs = self.queryset.filter(**{'%s__in' % key: value})
		pks = {str(o)for o in qs}
		for val in value:
			if str(val) not in pks:
				raise ValidationError(
					self.error_messages['invalid_choice'],
					code='invalid_choice',
					params={'value': val},
				)
		return qs

class ApplicationCenterSyncForm(forms.Form):

	semester = SemesterModelChoiceField(empty_label=None, 
		queryset=Semester.objects.all().order_by('semester_name'),
		)

	course_list = CustomM(
		to_field_name = "course_list",
		queryset=CourseExamShedule.objects.annotate(course_list=Concat('course_code',Value(':'),'course_name')).values_list("course_list",flat=True).distinct(),
		help_text='Hold down "Control", or "Command" on a Mac, to select more than one.')

	# course_list = forms.ModelMultipleChoiceField(
	# 	queryset=CourseExamShedule.objects.all(),
	# 	help_text='Hold down "Control", or "Command" on a Mac, to select more than one.')

	def __init__(self, *args, **kwargs):
		super().__init__( *args, **kwargs)
		self.fields['semester'].widget.attrs = {'class':'form-control'}
		self.fields['course_list'].widget.attrs = {'class':'form-control'}


	def clean_semester(self):
		semester = self.cleaned_data.get('semester')
		if semester.semester_name == S.SEMESTER_NAME:
			raise forms.ValidationError("Choose the semester for which registration data needs to be pulled")
		return semester

	def clean_course_list(self):
		course_list = self.cleaned_data.get('course_list')
		if len(course_list)>10:
			raise forms.ValidationError("At a time not more than 10 Courses can be Synced")
		return course_list



