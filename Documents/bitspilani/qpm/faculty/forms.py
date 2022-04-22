from django.forms import ModelForm
from master.models import *
from django import forms
from django.db.models import Q
import os

class QpfacultysubmissionForm(forms.Form):
	semester = forms.ModelChoiceField(empty_label = 'Choose Semester',required=False, queryset = Semester.objects.none())
	batch = forms.ModelChoiceField(empty_label = 'Choose Batch',required=False, queryset = Batch.objects.none())
	course_code = forms.ChoiceField()
	exam_type = forms.ModelChoiceField(empty_label = 'Choose Exam Type',required=False, queryset = QpSubmission.objects.none(),)
	exam_slot = forms.ModelChoiceField(empty_label = 'Choose Exam Slot',required=False, queryset = ExamSlot.objects.all())
	qp_guidelines_flag = forms.BooleanField(required=False)
	qp_correct_flag = forms.BooleanField(required=False)
	qp_path = forms.FileField(required=False)

	def __init__(self, *args, **kwargs):
		self.request = kwargs.pop('request')
		super(QpfacultysubmissionForm, self).__init__(*args, **kwargs)
		self.fields['semester'].widget.attrs['class'] = 'form-control'
		self.fields['batch'].widget.attrs['class'] = 'form-control'
		self.fields['course_code'].widget.attrs['class'] = 'form-control'
		self.fields['exam_type'].widget.attrs['class'] = 'form-control'
		self.fields['qp_path'].widget.attrs['class'] ='form-control'

		self.fields['exam_slot'].widget = forms.HiddenInput()

		query = QpSubmission.objects.filter((Q(faculty_email_id=self.request.user.email)|
											Q(email_access_id_1=self.request.user.email)|
											Q(email_access_id_2=self.request.user.email))
											,active_flag=True,).exclude(acceptance_flag=True)

		self.fields['semester'].queryset = Semester.objects.filter(id__in=query.values_list('semester',flat=True)).order_by('semester_name').distinct()
		self.fields['batch'].queryset =Batch.objects.filter(id__in=query.values_list('batch',flat=True)).order_by('batch_name').distinct()

		if self.request.POST.get('semester') and self.request.POST.get('batch') :
			query = query.filter(semester = self.request.POST.get('semester'),batch=self.request.POST.get('batch'))
		elif self.initial:
			if 'semester' in self.initial and 'batch' in self.initial :
				query = query.filter(semester = self.initial['semester'],batch=self.initial['batch'])


		course_code = query.distinct()
		course_code_choices = [('', 'Choose Course')] + [(course.course_code,course.course_code+' - '+course.course_name) for course in course_code]

		self.fields['course_code'].choices  = course_code_choices
		self.fields['exam_type'].queryset = ExamType.objects.filter(id__in=query.values_list('exam_type',flat=True)).distinct()

		# if self.initial:
		# 	if 'acceptance_flag' in self.initial:
		# 		if self.initial['acceptance_flag']:
		# 			self.fields['semester'].queryset = Semester.objects.filter(id__in=QpSubmission.objects.filter(faculty_email_id=self.request.user.email,active_flag=True,).distinct().values_list('semester',flat=True))
		# 			self.fields['batch'].queryset =Batch.objects.filter(id__in=QpSubmission.objects.filter(faculty_email_id=self.request.user.email,active_flag=True,).distinct().values_list('batch',flat=True))
		# 			query = QpSubmission.objects.filter(faculty_email_id=self.request.user.email,active_flag=True,)
		# 			course_code = query.distinct()
		# 			course_code_choices = [('', 'Choose Course')] + [(course.course_code,course.course_code+' - '+course.course_name) for course in course_code]
		# 			self.fields['course_code'].choices  = course_code_choices
		# 			self.initial['course_code'] = self.initial['course_code']
		# 			self.fields['exam_type'].queryset = ExamType.objects.filter(id__in=QpSubmission.objects.filter(faculty_email_id=self.request.user.email,active_flag=True,).exclude(acceptance_flag=True).values_list('exam_type',flat=True))

	class Meta:
		model = QpSubmission

	def clean(self):

		if 'exam_type' in self.cleaned_data:
			if self.cleaned_data['exam_type'] == None:
				raise ValidationError({
					'exam_type': ValidationError("This field is required.")
				})

		if 'course_code' in self.cleaned_data:
			if self.cleaned_data['course_code'] == None:
				raise ValidationError({
					'course_code': ValidationError("This field is required.")
				})

		if 'batch' in self.cleaned_data:
			if self.cleaned_data['batch'] == None:
				raise ValidationError({
					'batch': ValidationError("This field is required.")
				})

		if 'semester' in self.cleaned_data:
			if self.cleaned_data['semester'] == None:
				raise ValidationError({
					'semester': ValidationError("This field is required.")
				})


		SetQpSubmissionsLock_query= SetQpSubmissionsLock.objects.filter(semester=self.cleaned_data["semester"]
																	,batch=self.cleaned_data["batch"]
																	,exam_type=self.cleaned_data["exam_type"]).first()
		if SetQpSubmissionsLock_query:
			raise forms.ValidationError("You are not allowed to submit form.")
		try:
			query = QpSubmission.objects.get((Q(faculty_email_id=self.request.user.email)|
												Q(email_access_id_1=self.request.user.email)|
												Q(email_access_id_2=self.request.user.email)|
												Q(coordinator_email_id_1=self.request.user.email)|
												Q(coordinator_email_id_2=self.request.user.email)),
												semester=self.cleaned_data["semester"],
												batch=self.cleaned_data["batch"],
												course_code=self.cleaned_data["course_code"],
												exam_type = self.cleaned_data["exam_type"])
		except QpSubmission.DoesNotExist:
			raise forms.ValidationError("QP Submission Query Does not exist Please choose drop down starting from semester,batch,course and exam type")

		if query.submission_locked_flag:
			raise forms.ValidationError("You are not allowed to submit form.")

		lock_all_submissions_flag=SetQpSubmissionsLock.objects.filter(lock_all_submissions_flag=True)
		if lock_all_submissions_flag:
			if lock_all_submissions_flag[0].lock_all_submissions_flag:
				raise forms.ValidationError("You are not allowed to submit form.")
		return self.cleaned_data

	def clean_qp_correct_flag(self):
		if self.cleaned_data["qp_correct_flag"]:
			pass
		else:
			raise forms.ValidationError("Please check this box to confirm adherence to QP requirements and guidelines before submitting the QP")
		return self.cleaned_data["qp_correct_flag"]


	def clean_qp_guidelines_flag(self):
		if self.cleaned_data["qp_guidelines_flag"]:
			pass
		else:
			raise forms.ValidationError("Please check this box to confirm adherence to QP requirements and guidelines before submitting the QP")
		return self.cleaned_data["qp_guidelines_flag"]


	def clean_qp_path(self):
		if self.cleaned_data["qp_path"]:
			if self.initial:
				if 'qp_path' in self.initial and 'qp_path' in self.cleaned_data:
					if self.cleaned_data["qp_path"] == self.initial['qp_path']:
						raise forms.ValidationError("Please upload the file before submitting the form")

			ext = os.path.splitext(self.cleaned_data["qp_path"].name)[1]
			valid_extensions = ['.pdf', '.doc', '.docx', '.zip',]
			if not ext.lower() in valid_extensions:
				raise forms.ValidationError("Please upload only a MS Word, PDF or a zip file. Other file formats are NOT accepted")
			if self.cleaned_data["qp_path"].size > 5242880:
				raise forms.ValidationError("Please upload the file size below 5 MB")
		else:
			raise forms.ValidationError("Please upload the file before submitting the form")
		return self.cleaned_data["qp_path"]
