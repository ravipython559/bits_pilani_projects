from import_export import resources,widgets
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from . import default_settings
from .models import *

def get_instance_or_none(model, **query_kwargs):
	try:
		instance = model.objects.get(**query_kwargs)
	except Exception as e:
		instance = None
	return instance

class TextWidget(widgets.Widget):
	def clean(self, *args, **kwargs):
		val = super(TextWidget, self).clean(*args, **kwargs).strip() or None
		if val is None:
			raise ValueError('One of field is empty.Please correct the file and try again.')
		return val

class EmailWidget(widgets.Widget):
	def clean(self, *args, **kwargs):
		val = super(EmailWidget, self).clean(*args, **kwargs).strip() or None
		if val is None:
			raise ValueError('One of field is empty.Please correct the file and try again.')
		if val:
			try:
				validate_email(val)
				domain = val.split('@')[1]
				domain_list = ["pilani.bits-pilani.ac.in", "hyderabad.bits-pilani.ac.in", "wilp.bits-pilani.ac.in", "goa.bits-pilani.ac.in", "dubai.bits-pilani.ac.in"]
				if domain not in domain_list:
					raise ValueError('Please enter an Email Address with a valid domain')
			except:
				raise ValueError('Please enter an Email Address with a valid domain')
		return val

class OptionalEmailWidget(widgets.Widget):
	def clean(self, *args, **kwargs):
		val = super(OptionalEmailWidget, self).clean(*args, **kwargs).strip() or None

		if val:
			try:
				validate_email(val)
				domain = val.split('@')[1]
				domain_list = ["pilani.bits-pilani.ac.in", "hyderabad.bits-pilani.ac.in", "wilp.bits-pilani.ac.in", "goa.bits-pilani.ac.in", "dubai.bits-pilani.ac.in"]
				if domain not in domain_list:
					raise ValueError('Please enter an Email Address with a valid domain')
			except:
				raise ValueError('Please enter an Email Address with a valid domain')
		return val

class ProgramTextWidget(widgets.Widget):
	def clean(self, *args, **kwargs):
		val = super(ProgramTextWidget, self).clean(*args, **kwargs).strip() or None
		program_types = ['SPECIFIC', 'NON-SPECIFIC', 'CLUSTER', 'CERTIFICATION']
		if val is None:
			raise ValueError('One of field is empty.Please correct the file and try again.')
		if val:
			val = val.upper()
			if val not in program_types:
				raise ValueError('Program Type should be in one of the list: {}'.format(program_types))
		return val

class BatchForeignKeyWidget(widgets.ForeignKeyWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(BatchForeignKeyWidget, self).clean(value)
		if val:
			return self.get_queryset(value, row, *args, **kwargs).get(**{self.field: val})
		else:
			return get_instance_or_none(Batch, batch_name=default_settings.BATCH_NAME)


class ForeignKeyWidget(widgets.ForeignKeyWidget):
	def clean(self, value, *args, **kwargs):
		val = super(ForeignKeyWidget, self).clean(value=value.strip(), *args, **kwargs)
		if val:
			return val
		else:
			raise ValueError("One of field is empty.Please correct the file and try again.")

class BooleanWidgetForNull(widgets.BooleanWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(BooleanWidgetForNull, self).clean(value, row=row, *args, **kwargs) or None
		if val is None:
			val=0
		return val

class ActiveBooleanWidgetForNull(widgets.BooleanWidget):
	def clean(self, value, row=None, *args, **kwargs):
		val = super(ActiveBooleanWidgetForNull, self).clean(value, row=row, *args, **kwargs) or None
		if val is None:
			val=1
		return val
