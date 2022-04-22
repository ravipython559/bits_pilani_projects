from django import forms
from django.db.models import (Max, Q, Case, When, F, Value, TextField, CharField, IntegerField, BooleanField)
from master.models import *

class QPSubmissionCoordinatorForm(forms.Form):

	submission_status_choice = (
		(None,'Choose Submission Status'),
		('pendingsubmission','Pending Submission'),
		('pendingreview','Pending Review'),
		('sentforresubmission','Sent for Resubmission'),
		('accepted','Accepted'),
		('acceptedanddownloaded','Accepted and Downloaded'),
		)

	semester_name = forms.ModelChoiceField(empty_label='Choose Semester',
									queryset=QpSubmission.objects.none(),
									required=False)

	submission_status = forms.ChoiceField(widget=forms.Select(attrs={'class':'input'}),
		choices=submission_status_choice,
		required=False,
		# label='Choose Submission Status',
		)

	exam_type_name = forms.ModelChoiceField(empty_label='Choose Exam Type',
											  queryset=QpSubmission.objects.none(),
											  required=False)

	exam_slot = forms.ModelChoiceField(empty_label='Choose Exam Slot',
									queryset=QpSubmission.objects.none(),
									required=False)


	class Meta:
		model = QpSubmission

	def __init__(self, *args, **kwargs):
		self.request = kwargs.pop('request')
		super().__init__( *args, **kwargs)
		qpsub = QpSubmission.objects.filter(active_flag=1)

		self.fields['semester_name'].queryset = qpsub.filter(Q(coordinator_email_id_1 = self.request.user.email) | 
															Q(coordinator_email_id_2 = self.request.user.email)).annotate(semester_name=F('semester__semester_name')).values_list("semester_name",flat=True).order_by("semester_name").distinct()
		self.fields['exam_type_name'].queryset = qpsub.filter(Q(coordinator_email_id_1 = self.request.user.email) | 
															Q(coordinator_email_id_2 = self.request.user.email)).annotate(exam_type_name=F('exam_type__exam_type')).values_list("exam_type_name",flat=True).order_by('exam_type_name').distinct()
		qp_exam_slots = qpsub.filter(Q(coordinator_email_id_1 = self.request.user.email) | 
									Q(coordinator_email_id_2 = self.request.user.email)).values_list('exam_slot',flat=True).distinct()
		self.fields['exam_slot'].queryset = ExamSlot.objects.filter(id__in=qp_exam_slots).order_by('-slot_date')
		self.fields['semester_name'].widget.attrs = {'class':'form-control',}
		self.fields['submission_status'].widget.attrs = {'class':'form-control',}
		self.fields['exam_type_name'].widget.attrs = {'class':'form-control',}
		self.fields['exam_slot'].widget.attrs = {'class':'form-control',}