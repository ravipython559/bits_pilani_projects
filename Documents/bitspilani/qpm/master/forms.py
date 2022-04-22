from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from master.models import *
# from master.utils.extra_models.querysets import get_instance_or_none, get_date_day_or_empty
from django.core.exceptions import ValidationError
from django.core.validators import (_lazy_re_compile, EmailValidator)
import re
from django.db.models import Q, Value, When, Case
# from master.forms.form_fields import *
from django.db.models import IntegerField

from django.utils.translation import ugettext_lazy as _

class SemesterModelChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		return super().label_from_instance(obj)

class BatchModelChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		return super().label_from_instance(obj)

class ExamSlotChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		return super().label_from_instance(obj)


class QpSubmissionForm(forms.ModelForm):
    semester = SemesterModelChoiceField(empty_label=None)
    batch = BatchModelChoiceField(empty_label=None, queryset=Batch.objects.all())
    exam_slot = ExamSlotChoiceField(empty_label=None, queryset=ExamSlot.objects.all())

    def clean_exam_slot(self):
        exam_slot = self.cleaned_data['exam_slot']
        return exam_slot

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam_type
    class Meta(object):
        model = QpSubmission
        exclude = ('exam_venue_slot_maps', 'inserted_on', 'last_update_on',)
