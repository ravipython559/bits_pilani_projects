from django import forms
from ema import default_settings as S   

class UserChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		return "{0}".format(obj.email)

class SemesterModelChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		if obj.semester_name == S.SEMESTER_NAME:
			return "{0}".format('----------')
		else:
			return super().label_from_instance(obj)

class BatchModelChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		if obj.batch_name == S.BATCH_NAME:
			return "{0}".format('----------')
		else:
			return super().label_from_instance(obj)

class ExamTypeChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		if obj.exam_type == S.EXAM_TYPE:
			return "{0}".format('----------')
		else:
			return super().label_from_instance(obj)

class ExamSlotChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		if obj.slot_name == S.EXAM_SLOT_NAME:
			return "{0}".format('----------')
		else:
			return super().label_from_instance(obj)

class LocationChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		if obj.location_name == S.LOCATION:
			return "{0}".format('----------')
		else:
			return super().label_from_instance(obj)