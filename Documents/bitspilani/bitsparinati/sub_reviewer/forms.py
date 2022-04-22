from django import forms
from django.conf import settings
from registrations.models import *
from django.utils import timezone
from django.forms.models import inlineformset_factory
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.core.urlresolvers import reverse_lazy
import os


class PlainTextWidget(forms.Widget):
	def render(self, value,doc_name, *args,**kwargs):
		return mark_safe(doc_name) if doc_name  else '-'

class FileURLWidget(forms.Widget):
	def render(self, name, value, attrs=None):
		display_text = 'Doc Link'
		html_tag = '<a{}>{}</a>'
		if value is None: 
			value = '#'
			html_tag = '<span{}>{}</span>'
			display_text = 'To Be Submitted'
		final_attrs = self.build_attrs(attrs, name=name, 
			href=value, target='_blank')
		return format_html(html_tag, flatatt(final_attrs), force_text(display_text))

class SubReviewerForm(forms.ModelForm):
	application_status = forms.ChoiceField(widget=forms.Select(attrs={'style':'width:60%'}),
		choices=[(None,'Choose Status'),
	 (settings.APP_STATUS[1][0],settings.APP_STATUS[1][0]),
	 (settings.APP_STATUS[2][0],settings.APP_STATUS[2][0]),
	 (settings.APP_STATUS[17][0],settings.APP_STATUS[17][0]),
	 ])

	def clean_application_status(self):
		application_status = self.cleaned_data['application_status']
		if not application_status:
			raise forms.ValidationError("select choice")
		return application_status

	class Meta(object):
		model = StudentCandidateApplication
		fields = ('application_status',)

def sub_rev_app_doc(email=None):
	class SubReviewerApplicationDocumentForm(forms.ModelForm):
		document_name = forms.CharField(max_length=254,required=False,
			widget=PlainTextWidget,
			)
		file_link = forms.CharField(max_length=254,required=False,
			widget=FileURLWidget,
			)
		deffered_submission_flag = forms.BooleanField(required=False,)
		exception_notes = forms.CharField(required=False, 
			widget=forms.Textarea(attrs={'cols': 30, 'rows': 3}))

		def __init__(self, *args, **kwargs):
			super(SubReviewerApplicationDocumentForm, self).__init__(*args, **kwargs)
			self.fields['rejection_reason'].empty_label = 'Select Reason'
			self.fields['document_name'].initial = self.instance.document.document_name
			self.fields['deffered_submission_flag'].disabled = not ( self.instance.program_document_map and 
				self.instance.program_document_map.deffered_submission_flag and 
				self.instance.file)
			self.fields['deffered_submission_flag'].initial = (self.instance.program_document_map and 
				self.instance.program_document_map.deffered_submission_flag and
				self.instance.reload_flag)

			p_code = str(self.instance.application.student_application_id)[1:5]
			program_object = Program.objects.filter(program_code=p_code)
			document_submission_flag = program_object[0].document_submission_flag
			if not document_submission_flag:
				if not self.instance.program_document_map.deffered_submission_flag:
					self.fields['rejected_by_bits_flag'].disabled = True
			
			if self.instance.file:
				self.fields['file_link'].initial = reverse_lazy('registrationForm:document-view', kwargs={'pk': self.instance.pk})
				
			else:
				self.fields['file_link'].disabled = True
				self.fields['rejection_reason'].disabled = True
				self.fields['exception_notes'].disabled = True
				self.fields['rejected_by_bits_flag'].disabled = True
				self.fields['accepted_verified_by_bits_flag'].disabled = True
		
		def clean_rejection_reason(self):
			rejected_by_bits_flag = self.cleaned_data.get('rejected_by_bits_flag',False)
			rejection_reason = self.cleaned_data['rejection_reason']
			if rejected_by_bits_flag and not rejection_reason:
				raise forms.ValidationError("select rejected reason")
			return rejection_reason

		def save(self, commit=True):

			instance = super(SubReviewerApplicationDocumentForm, self).save(commit=False)
			
			rejection_reason = self.cleaned_data.get('rejection_reason',None)
			accepted_verified_by_bits_flag = self.cleaned_data.get('accepted_verified_by_bits_flag',None)
			exception_notes = self.cleaned_data.get('exception_notes',None)
			deffered_submission_flag = self.cleaned_data.get('deffered_submission_flag')

			if rejection_reason:
				instance.rejected_by_bits_flag=True
				instance.accepted_verified_by_bits_flag=False
				
			if rejection_reason or accepted_verified_by_bits_flag or exception_notes or deffered_submission_flag:
				instance.inspected_on = timezone.localtime(timezone.now())
				instance.verified_rejected_by = email
				instance.reload_flag = False

			if deffered_submission_flag:
				instance.reload_flag = True
				instance.exception_notes = 'Deferred'

			if commit:instance.save()
			return instance

		class Meta(object):
			model = ApplicationDocument
			fields = ('document_name','file_link','accepted_verified_by_bits_flag',
				'rejected_by_bits_flag','deffered_submission_flag','rejection_reason', 'exception_notes')

		class Media(object):
			js = ('{}bits-static/js/sub-reviewer.js'.format(settings.STATIC_URL),)
	return SubReviewerApplicationDocumentForm


