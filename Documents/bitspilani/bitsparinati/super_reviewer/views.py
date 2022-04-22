from django.shortcuts import render
from registrations.models import *
from django.conf import settings
from django.db.models import Value,Count,F,Q,CharField, Case, When
from django.contrib.auth.decorators import login_required
from .bits_decorator import *
import cPickle
from django.forms.models import (modelformset_factory, inlineformset_factory,
                                 formset_factory)
from .forms import *
from django.db.models.functions import Concat
from django.views.decorators.http import require_http_methods
from datetime import datetime
from super_reviewer.dynamic_views import BaseApplicantDetail
from django.utils.decorators import method_decorator
from django.utils import timezone

@login_required
@is_super_reviewer
def sr_home(request):
      '''
      Super Reviewer home page...
      Will display list of candidates with status 1.Escalated. Under review by Super Reviewer
      '''
      query = CandidateSelection.objects.filter(
            application__application_status=settings.APP_STATUS[15][0]
            ).annotate(
            request_type=Case(
                        When(prog_ch_flag=True, then=Value('Program Change')),
                        default=Value('Offer Status Change'),
                        output_field=CharField(),
                        ),
            )

      return render(request, 'super_reviewer/sr_home.html', {"queryResult": query})


# View to process offer status change...

@login_required
@is_super_reviewer
@require_http_methods(["POST","GET"])
def sr_offer_change(request):
  CSFormset = formset_factory(SuperofferForm,extra=0, can_delete=False)
  if request.method == 'POST':
    cs_formset = CSFormset(request.POST,prefix='CSForm')
    super_comment = SuperEscCommentForm(request.POST)
    if cs_formset.is_valid() and super_comment.is_valid():
      comment = super_comment.cleaned_data['super_comment']
      if 'Approve' in request.POST:
        for f in cs_formset:
          if f.cleaned_data['su_rev_app'] == True:
            app_student_id = f.cleaned_data['application_student_id']
            cs = CandidateSelection.objects.get(
                  application__student_application_id = app_student_id )
            cs.su_rev_com = comment
            cs.su_rev_app = True
            cs.app_rej_by_su_rev_dt = timezone.localtime(timezone.now())
            cs.prior_status = ''
            cs.application.application_status = settings.APP_STATUS[1][0]
            cs.application.save()
            cs.es_to_su_rev = False
            cs.save()
      elif 'Reject' in request.POST:
        for f in cs_formset:
          if f.cleaned_data['su_rev_app'] == True:
            app_student_id = f.cleaned_data['application_student_id']
            cs = CandidateSelection.objects.get(
                  application__student_application_id = app_student_id )
            cs.su_rev_app = False
            cs.es_to_su_rev = False
            cs.su_rev_com = comment
            cs.application.application_status = cs.prior_status
            cs.prior_status = ''
            cs.app_rej_by_su_rev_dt = timezone.localtime(timezone.now())
            cs.application.save()
            cs.save()

      return  redirect(reverse('super_reviewer:sr-home'))

  else:

    cs = CandidateSelection.objects.filter(
          application__application_status=settings.APP_STATUS[15][0],
          prog_ch_flag=False
          ).annotate(
          full_name = F('application__full_name'),
          application_student_id = F('application__student_application_id'),
          program_applied_for = F('application__program__program_name'),
          created_on_datetime = F('application__created_on_datetime') ,
          app_id = F('application__id') ,
          ).values(
          'full_name',
          'application_student_id',
          'program_applied_for',
          'created_on_datetime',
          'su_rev_app',
          'es_com',
          'app_id')
    

    cs_formset = CSFormset(prefix='CSForm',initial=cs)
    super_comment = SuperEscCommentForm()


  return render(request, 'super_reviewer/sr_offer_change.html',
        {
        'cs_formset':cs_formset,
        'super_comment':super_comment,
        })
# ...View to process offer status change ends


# View to process program change...
@login_required
@is_super_reviewer
@require_http_methods(["POST","GET"])
def sr_program_change(request):
  CSFormset = formset_factory(SuperprogramForm,extra=0, can_delete=False)
  if request.method == 'POST':
    cs_formset = CSFormset(request.POST,prefix='CSForm')
    super_comment = SuperEscCommentForm(request.POST)
    if cs_formset.is_valid() and super_comment.is_valid():
      comment = super_comment.cleaned_data['super_comment']
      if 'Approve' in request.POST:
        for f in cs_formset:
          if f.cleaned_data['su_rev_app'] == True:
            app_student_id = f.cleaned_data['application_student_id']
            cs = CandidateSelection.objects.get(
                  application__student_application_id = app_student_id )
            cs.su_rev_com = comment
            cs.su_rev_app = True
            tmp_student_id = cs.student_id
            cs.old_student_id = tmp_student_id
            cs.student_id = None
            cs.es_to_su_rev = False
            cs.app_rej_by_su_rev_dt = timezone.localtime(timezone.now())
            cs.application.application_status = settings.APP_STATUS[16][0]
            old_program = cs.application.program
            cs.application.program = cs.new_sel_prog
            # cs.new_sel_prog = old_program
            new_application_id = 'A{0}{1:04d}'.format(cs.application.program.program_code,
                  cs.application.id)
            cs.new_application_id ='{0}-{1}'.format(new_application_id,
              cs.application.student_application_id) #new-old
            cs.application.save()
            cs.save()
            pdm = ProgramDocumentMap.objects.filter(program = cs.application.program )
            ses = StudentElectiveSelection.objects.filter(student_id=cs,
                                            course__program=old_program).delete()
            if pdm.exists():
              ApplicationDocument.objects.filter(application = cs.application).exclude(
                document__in =  pdm.values_list('document_type')
                ).delete()
            # ApplicationDocument.objects.filter(application = cs.application,
            #   document__mandatory_document = True ).delete()



      elif 'Reject' in request.POST:
        for f in cs_formset:
          if f.cleaned_data['su_rev_app'] == True:
            app_student_id = f.cleaned_data['application_student_id']
            cs = CandidateSelection.objects.get(
                  application__student_application_id = app_student_id )
            cs.prog_ch_flag = False
            cs.application.application_status = cs.prior_status
            cs.prior_status = ''
            cs.su_rev_com = comment
            cs.su_rev_app = False
            cs.es_to_su_rev = False
            cs.app_rej_by_su_rev_dt = timezone.localtime(timezone.now())
            cs.new_sel_prog = None
            cs.application.save()
            cs.save()

      return  redirect(reverse('super_reviewer:sr-home'))
  else:
    eloa = ExceptionListOrgApplicants.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),).values_list(
      'employee_email').distinct()
    cs = CandidateSelection.objects.filter(
      application__application_status=settings.APP_STATUS[15][0],
      prog_ch_flag=True
      ).exclude(
      application__login_email__email__in = eloa
      ).annotate(
      full_name = F('application__full_name'),
      application_student_id = F('application__student_application_id'),
      created_on_datetime = F('application__created_on_datetime') ,
      app_id = F('application__id') ,
      ).values(
      'full_name',
      'application_student_id',
      'prior_status',
      'new_sel_prog',
      'created_on_datetime',
      'su_rev_app',
      'es_com',
      'new_application_id',
      'app_id'
      )

    cs_formset = CSFormset(prefix='CSForm',initial=cs)
    super_comment = SuperEscCommentForm()

  return render(request, 'super_reviewer/sr_program_change.html',
        {
        'cs_formset':cs_formset,
        'super_comment':super_comment,
        })
# ...View to process program change ends

@method_decorator([login_required, is_super_reviewer],name='dispatch')
class ApplicantDetail(BaseApplicantDetail):
  template_name = 'super_reviewer/application_form_view.html'

