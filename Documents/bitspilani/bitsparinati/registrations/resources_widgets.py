from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from import_export import widgets
from decimal import Decimal
from django.utils import timezone

class ProgramWidget(widgets.ForeignKeyWidget):
	def clean(self, value, *args, **kwargs):
		return super(ProgramWidget, self).clean(value=value.upper().strip(), *args, **kwargs)


class EmailWidget(widgets.CharWidget):
	def clean(self, value):
		email = value.strip()
		try:
			validate_email(email)
			# if len(email)>50:
			# 	raise ValidationError('Email string length more than 50')
		except Exception as e:
			raise ValidationError("Email type error :{0}".format(e))
		return email 


class FTWidget(widgets.CharWidget):
	def clean(self, value):
		fee_type = value.strip()
		if not fee_type:
			raise ValidationError('Fee type field is empty')
		return fee_type


class FAWidget(widgets.DecimalWidget):
	def clean(self, value):
		if self.is_empty(value):
			raise ValidationError('Fee Amount field is empty')
		if Decimal(value) <= 0:
				raise ValidationError("Fee amount must be greater than zero")
		return Decimal(value)


class EEFWidget(widgets.BooleanWidget):
	def clean(self, value):
		value = value.strip()
		true_values = ["1", 1]
		return True if value in true_values else False


class EAFWidget(widgets.BooleanWidget):
	def clean(self, value):
		value = value.strip()
		true_values = ["1", 1]
		return True if value in true_values else False


class EZFWidget(widgets.BooleanWidget):
	def clean(self, value):
		value = value.strip()
		true_values = ["1", 1]
		return True if value in true_values else False


class UDFieldWidget(widgets.DateWidget):
		def render(self, value):
			return timezone.localtime(value).strftime("%d-%m-%Y %I:%M %p")


class CourseWidget(widgets.ForeignKeyWidget):
	def clean(self, value, *args, **kwargs):
		return super(CourseWidget, self).clean(value=value.strip(), *args, **kwargs)