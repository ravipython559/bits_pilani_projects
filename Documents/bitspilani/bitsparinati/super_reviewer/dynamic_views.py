from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.shortcuts import render
from registrations.models import *
from django.db.models.functions import *
from django.db.models import *
from django.conf import settings
import logging
logger = logging.getLogger("main")
import cPickle

class BaseApplicantDetail(TemplateView):
	def get_context_data(self, application_id=None, **kwargs):
		context = super(BaseApplicantDetail, self).get_context_data(
			application_id=application_id, **kwargs)
		app = StudentCandidateApplication.objects.get(id=application_id)
		context['teaching_mode_check'] = self.def_teaching_mode_check(app)
		context['is_specific'] = app.program.program_type == 'specific'
		# code to hide employment and mentor details
		sca_attributes = app.__dict__.keys()
		for x in sca_attributes:
			setattr(app, '%s_hide' %(x), False)

		rejected_attributes = FormFieldPopulationSpecific.objects.filter(
		program=app.program,
		show_on_form=False,
		).values_list('field_name', flat=True)

		for x in rejected_attributes:
			setattr(app, '%s_hide' %(x), True)

		try:
			cs = CandidateSelection.objects.get(application = app)
			bits_comment = cs.selection_rejection_comments
		except CandidateSelection.DoesNotExist:
			cs=None
			bits_comment = None

		context['bits_rej_reason'] = ( 
				', '.join(cPickle.loads(str(cs.bits_rejection_reason))) if 
				cs and
				not cs.bits_rejection_reason == cPickle.dumps(None) and
				cs.bits_rejection_reason	
			else None 
		)

		context['bits_comment'] = bits_comment

		context['form'] = app
		context['edu1'] = StudentCandidateWorkExperience.objects.filter(application=app)
		context['qual1'] = StudentCandidateQualification.objects.filter(application=app)
		context['uploadFiles'] = ApplicationDocument.objects.filter(application=app)
		return context

	#code to hide teaching mode
	def def_teaching_mode_check(self,app):
		return FormFieldPopulationSpecific.objects.filter(
				program = app.program,
				show_on_form=True,
				field_name__in=['teaching_mode','programming_flag','alternate_email_id'],
			).values_list('field_name', flat=True)