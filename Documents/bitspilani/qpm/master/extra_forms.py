from django import forms
from .models import * 

class SetQpSubmissionsLockForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(SetQpSubmissionsLockForm, self).__init__(*args, **kwargs)

	def clean(self):
		if any(self.errors):return

		lock_flag = self.cleaned_data['lock_flag']
		lock_all_submissions_flag = self.cleaned_data['lock_all_submissions_flag']

		if lock_flag and lock_all_submissions_flag:
			raise forms.ValidationError("lock_flag and lock_all_submissions_flag options cannot be provided together. Please check either of the option.")

		if not lock_flag and not lock_all_submissions_flag:
			raise forms.ValidationError("lock_flag or lock_all_submissions_flag options cannot be empty. Please check either of the option.")


class ExamSlotForm(forms.ModelForm):

	class Meta:
		model = ExamSlot
		fields = ('slot_name','slot_date','slot_day','slot_start_time',)
		widgets = {
            'slot_start_time': forms.TimeInput(format=('%H:%M')),
        }

class AdminQpSubmissionForm(forms.ModelForm):
    class Meta:
        model = QpSubmission
        fields = '__all__'

    def clean(self):
        if self.cleaned_data['acceptance_flag']==True and self.cleaned_data['submission_locked_flag'] == False:
            raise forms.ValidationError("Please check the submission_locked_flag")
        return self.cleaned_data

    def clean_faculty_email_id(self):
        data = self.cleaned_data['faculty_email_id']
        domain = data.split('@')[1]
        domain_list = ["pilani.bits-pilani.ac.in", "hyderabad.bits-pilani.ac.in", "wilp.bits-pilani.ac.in", "goa.bits-pilani.ac.in", "dubai.bits-pilani.ac.in"]
        if domain not in domain_list:
            raise forms.ValidationError("Please enter an Email Address with a valid domain")
        return data

    def clean_email_access_id_1(self):
        if self.cleaned_data['email_access_id_1']:
            data = self.cleaned_data['email_access_id_1']
            domain = data.split('@')[1]
            domain_list = ["pilani.bits-pilani.ac.in", "hyderabad.bits-pilani.ac.in", "wilp.bits-pilani.ac.in", "goa.bits-pilani.ac.in", "dubai.bits-pilani.ac.in"]
            if domain not in domain_list:
                raise forms.ValidationError("Please enter an Email Address with a valid domain")
            return data

    def clean_email_access_id_2(self):
        if self.cleaned_data['email_access_id_2']:
            data = self.cleaned_data['email_access_id_2']
            domain = data.split('@')[1]
            domain_list = ["pilani.bits-pilani.ac.in", "hyderabad.bits-pilani.ac.in", "wilp.bits-pilani.ac.in", "goa.bits-pilani.ac.in", "dubai.bits-pilani.ac.in"]
            if domain not in domain_list:
                raise forms.ValidationError("Please enter an Email Address with a valid domain")
            return data

    def clean_coordinator_email_id_1(self):
        if self.cleaned_data['coordinator_email_id_1']:
            data = self.cleaned_data['coordinator_email_id_1']
            domain = data.split('@')[1]
            domain_list = ["pilani.bits-pilani.ac.in", "hyderabad.bits-pilani.ac.in", "wilp.bits-pilani.ac.in", "goa.bits-pilani.ac.in", "dubai.bits-pilani.ac.in"]
            if domain not in domain_list:
                raise forms.ValidationError("Please enter an Email Address with a valid domain")
            return data

    def clean_coordinator_email_id_2(self):
        if self.cleaned_data['coordinator_email_id_2']:
            data = self.cleaned_data['coordinator_email_id_2']
            domain = data.split('@')[1]
            domain_list = ["pilani.bits-pilani.ac.in", "hyderabad.bits-pilani.ac.in", "wilp.bits-pilani.ac.in", "goa.bits-pilani.ac.in", "dubai.bits-pilani.ac.in"]
            if domain not in domain_list:
                raise forms.ValidationError("Please enter an Email Address with a valid domain")
            return data

    def full_clean(self):
        super(AdminQpSubmissionForm, self).full_clean()
        try:
            self.instance.validate_unique()
        except forms.ValidationError as e:
            self._update_errors(e)

class StaffUserAccessListForm(forms.ModelForm):
    def clean_user_id(self):
        data = self.cleaned_data['user_id']
        domain = data.split('@')[1]
        domain_list = ["pilani.bits-pilani.ac.in", "hyderabad.bits-pilani.ac.in", "wilp.bits-pilani.ac.in", "goa.bits-pilani.ac.in", "dubai.bits-pilani.ac.in"]
        if domain not in domain_list:
            raise forms.ValidationError("Please enter an Email Address with a valid domain")
        return data
