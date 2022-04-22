from import_export import resources,widgets
from master.utils.extra_models.querysets import get_instance_or_none
from django.core.exceptions import ValidationError
from ema import default_settings as S
from master.models import Batch, Semester

class TextWidget(widgets.Widget):
	def clean(self, *args, **kwargs):
		val = super(TextWidget, self).clean(*args, **kwargs).strip() or None
		if val is None:
			raise ValueError('One of field is empty.Please correct the file and try again.')
		return val

class SemesterWidget(widgets.Widget):
	def clean(self, *args, **kwargs):
		val = super(SemesterWidget, self).clean(*args, **kwargs).strip() or None
		if val:
			semester_object = Semester.objects.filter(semester_name=val).first()
			val = semester_object
			return val
		else:
			semester_object = Semester.objects.filter(id=1).first()
			return semester_object

class ForeignKeyWidget(widgets.ForeignKeyWidget):
	def clean(self, value, *args, **kwargs):
		val = super(ForeignKeyWidget, self).clean(value=value.strip(), *args, **kwargs)
		if val:
			return val
		else:
			raise ValueError("One of field is empty.Please correct the file and try again.")

class NumberIntWidget(widgets.IntegerWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(NumberIntWidget, self).clean(value, row=row, *args, **kwargs) or None
		if val is None:
			raise ValueError('One of field is empty.Please correct the file and try again.')
		return val

class SemesterForeignKeyWidget(widgets.ForeignKeyWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(SemesterForeignKeyWidget, self).clean(value)
		if val:
			return self.get_queryset(value, row, *args, **kwargs).get(**{self.field: val})
		else:
			return get_instance_or_none(Semester, semester_name=S.SEMESTER_NAME)

class BatchForeignKeyWidget(widgets.ForeignKeyWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(BatchForeignKeyWidget, self).clean(value)
		if val:
			return self.get_queryset(value, row, *args, **kwargs).get(**{self.field: val})
		else:
			return get_instance_or_none(Batch, batch_name=S.BATCH_NAME)

class BooleanWidgetForNull(widgets.BooleanWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(BooleanWidgetForNull, self).clean(value, row=row, *args, **kwargs) or None
		if val is None:
			val=0
		return val

class ExamVenueLockForeignKeyWidget(widgets.ForeignKeyWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(ExamVenueLockForeignKeyWidget, self).clean(value)
		if val:
			return self.get_queryset(value, row, *args, **kwargs).get(**{self.field: val})
		else:
			return get_instance_or_none(ExamVenue, venue_short_name=S.VENUE_SHORT_NAME)

class ExceptionEndDate(widgets.DateWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(ExceptionEndDate, self).clean(value, row=row, *args, **kwargs) or None
		return val

class SemesterExceptionForeignKeyWidget(widgets.ForeignKeyWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(SemesterExceptionForeignKeyWidget, self).clean(value)
		if val:
			return self.get_queryset(value, row, *args, **kwargs).get(**{self.field: val})
		else:
			raise ValueError('One of field is empty.Please correct the file and try again.')
		return val
			