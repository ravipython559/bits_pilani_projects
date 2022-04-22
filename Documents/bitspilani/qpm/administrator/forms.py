from django import forms
from django.db.models import F, Value
from master.models import *

class QPSubmissionStatusForm(forms.Form):

	program_type = forms.ModelChoiceField(empty_label='Choose Program Type',
								queryset=QpSubmission.objects.filter(active_flag=1).distinct().values_list('program_type',flat=True).order_by('program_type'),
								required=False)

	semester_name = forms.ModelChoiceField(empty_label='Choose Semester',
									queryset=QpSubmission.objects.none(),
									required=False)

	batch_name = forms.ModelChoiceField(empty_label='Choose Batch',
											  queryset=QpSubmission.objects.none(),
											  required=False)

	faculty_id = forms.ModelChoiceField(empty_label='Choose Faculty ID',
									queryset=QpSubmission.objects.filter(active_flag=1).distinct().values_list('faculty_email_id',flat=True).order_by('faculty_email_id'),
									required=False)

	exam_type_name = forms.ModelChoiceField(empty_label='Choose Exam Type',
											  queryset=QpSubmission.objects.filter(active_flag=1).annotate(exam_type_name=F('exam_type__exam_type')).values_list("exam_type_name",flat=True).order_by('exam_type_name').distinct(),
											  required=False)

	exam_slot = forms.ModelChoiceField(empty_label='Choose Exam Slot',
									queryset=QpSubmission.objects.none(),
									required=False)

	class Meta:
		model = QpSubmission


	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user')
		super().__init__( *args, **kwargs)
		self.fields['semester_name'].queryset = QpSubmission.objects.filter(active_flag=1).annotate(semester_name=F('semester__semester_name')).values_list("semester_name",flat=True).order_by("semester_name").distinct()
		self.fields['batch_name'].queryset = QpSubmission.objects.filter(active_flag=1).annotate(batch_name=F('batch__batch_name')).values_list("batch_name",flat=True).order_by("batch_name").distinct()
		qp_exam_slots = QpSubmission.objects.filter(active_flag=1).values_list('exam_slot',flat=True).distinct()
		self.fields['exam_slot'].queryset = ExamSlot.objects.filter(id__in=qp_exam_slots).order_by('-slot_date')
		self.fields['semester_name'].widget.attrs = {'class':'form-control',}
		self.fields['program_type'].widget.attrs = {'class':'form-control',}
		self.fields['batch_name'].widget.attrs = {'class':'form-control',}
		self.fields['faculty_id'].widget.attrs = {'class':'form-control',}
		self.fields['exam_type_name'].widget.attrs = {'class':'form-control',}
		self.fields['exam_slot'].widget.attrs = {'class':'form-control',}

class QPSubmissionsDownloadForm(forms.Form):

	program_type = forms.ModelChoiceField(empty_label='Choose Program Type',
								queryset=QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).distinct().values_list('program_type',flat=True).order_by('program_type'),
								required=False)

	semester_name = forms.ModelChoiceField(empty_label='Choose Semester',
									queryset=QpSubmission.objects.none(),
									required=False)

	batch_name = forms.ModelChoiceField(empty_label='Choose Batch',
											  queryset=QpSubmission.objects.none(),
											  required=False)

	faculty_id = forms.ModelChoiceField(empty_label='Choose Faculty ID',
									queryset=QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).distinct().values_list('faculty_email_id',flat=True).order_by('faculty_email_id'),
									required=False)

	exam_type_name = forms.ModelChoiceField(empty_label='Choose Exam Type',
											  queryset=QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).annotate(exam_type_name=F('exam_type__exam_type')).values_list("exam_type_name",flat=True).order_by('exam_type_name').distinct(),
											  required=False)

	exam_slot = forms.ModelChoiceField(empty_label='Choose Exam Slot',
									queryset=QpSubmission.objects.none(),
									required=False)
	date = forms.DateField(input_formats=['%Y-%m-%d %H:%M'],label="Enter Date",help_text="Choose the time stamp after which QP submission details need to be seen",required=False)

	class Meta:
		model = QpSubmission


	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user')
		super().__init__( *args, **kwargs)
		self.fields['semester_name'].queryset = QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).annotate(semester_name=F('semester__semester_name')).values_list("semester_name",flat=True).order_by('semester_name').distinct()
		self.fields['batch_name'].queryset = QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).annotate(batch_name=F('batch__batch_name')).values_list("batch_name",flat=True).order_by('batch_name').distinct()
		qp_exam_slots = QpSubmission.objects.filter(active_flag=1, acceptance_flag=1).values_list('exam_slot',flat=True).distinct()
		self.fields['exam_slot'].queryset = ExamSlot.objects.filter(id__in=qp_exam_slots).order_by('-slot_date')
		self.fields['semester_name'].widget.attrs = {'class':'form-control',}
		self.fields['program_type'].widget.attrs = {'class':'form-control',}
		self.fields['batch_name'].widget.attrs = {'class':'form-control',}
		self.fields['faculty_id'].widget.attrs = {'class':'form-control',}
		self.fields['exam_type_name'].widget.attrs = {'class':'form-control',}
		self.fields['exam_slot'].widget.attrs = {'class':'form-control',}

class AcceptRejectForm(forms.Form):
	acceptance_flag = forms.BooleanField(required=False)
	rejected_flag = forms.BooleanField(required=False)
	alternate_qp_path = forms.FileField(required=False)
	rejection_comments = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter Revision / Review Comments'}),required=False)

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user')
		super(AcceptRejectForm, self).__init__(*args, **kwargs)
		self.fields['rejection_comments'].widget.attrs['class'] = 'form-control'

		if self.initial:
			if self.initial['submission_locked_flag']:
				self.fields['rejection_comments'].widget.attrs['readonly'] = 'readonly'
				self.fields['rejected_flag'].widget.attrs['disabled'] = 'disabled'
				self.fields['acceptance_flag'].widget.attrs['disabled'] = 'disabled'


	def clean(self):
		if self.cleaned_data['acceptance_flag'] and self.cleaned_data['rejected_flag']:
			raise forms.ValidationError("Please check either the acceptance checkbox or the rejection checkbox and try again.")

		if self.cleaned_data['rejected_flag']:
			if self.cleaned_data['rejection_comments']:
				pass
			else:
				raise forms.ValidationError("Please provide appropriate rejection comments.")

	def clean_alternate_qp_path(self):
		if self.cleaned_data["alternate_qp_path"]:
			if self.cleaned_data['acceptance_flag'] or self.cleaned_data['rejected_flag']:
				pass
			else:
				if self.initial:
					if 'acceptance_flag' in self.initial or 'rejected_flag' in self.initial:
						pass
					else:
						raise forms.ValidationError("Please check either accept or reject and choose file.")

			ext = os.path.splitext(self.cleaned_data["alternate_qp_path"].name)[1]
			valid_extensions = ['.pdf', '.doc', '.docx', '.zip',]
			if not ext.lower() in valid_extensions:
				raise forms.ValidationError("Please upload only a MS Word, PDF or a zip file. Other file formats are NOT accepted")
			if self.cleaned_data["alternate_qp_path"].size > 5242880:
				raise forms.ValidationError("Please upload the file size below 5 MB")
		return self.cleaned_data["alternate_qp_path"]
	class Meta:
		model = QpSubmission

class ManageQpLockUnlockForm(forms.Form):

	def __init__(self, *args, **kwargs):
		super().__init__( *args, **kwargs)
		self.fields['semester_name'].widget.attrs = {'class':'form-control', 'style':'width:60%',}
		self.fields['program_type'].widget.attrs = {'class':'form-control', 'style':'width:50%',}
		self.fields['batch_name'].widget.attrs = {'class':'form-control', 'style':'width:60%',}
		self.fields['course_code'].widget.attrs = {'style':'width:55%; background-color:lightgray','readonly':'true',}
		self.fields['exam_type'].widget.attrs = {'class':'form-control', 'style':'width:60%',}
		self.fields['exam_slot'].widget.attrs = {'class':'form-control', 'style':'width:80%',}

	program_type = forms.ChoiceField(choices=PROGRAM_CHOICES, required=True, label='Program Type')

	semester_name = forms.ModelChoiceField(empty_label='Choose Semester',
										   label='Semester',
										   queryset=Semester.objects.all().order_by('-semester_name'),
										   required=False)

	batch_name = forms.ModelChoiceField(empty_label='Choose Batch',
										label='Batch',
										queryset=Batch.objects.all().order_by('-batch_name'),
										required=False)

	exam_type = forms.ModelChoiceField(empty_label='Choose Exam Type',
									   label='Exam Type',
											queryset=ExamType.objects.all(),
											required=False)

	exam_slot = forms.ModelChoiceField(empty_label='Choose Exam Slot',
									   label='Exam Slot',
									   queryset=ExamSlot.objects.all(),
									   required=False)

	course_code = forms.CharField(label='Course Code and Name', required=False)