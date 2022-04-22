from registrations.models import StudentCandidateApplication, Program,\
    CandidateSelection, SpecificAdmissionSummary
import datetime
from django.db.models import Count, Q


def specific_summary_table_population():

    specific_programs = StudentCandidateApplication.objects.filter(Q(program__program_type='specific', program__active_for_applicaton_flag=True) | Q(program__program_type='specific', program__active_for_admission_flag=True))

    distinct_records = specific_programs.values('program','admit_batch', 'admit_sem_cohort').annotate(application_count=Count('id')).order_by()

    for record in distinct_records.values('program').distinct():

        pgm = Program.objects.get(id = record['program'])

        application_count = StudentCandidateApplication.objects.filter(program=pgm, program__program_type='specific').values('program', 'program__program_code','admit_batch', 'admit_sem_cohort').annotate(application_count=Count('id')).order_by()

        #check if the status values are correctly spelled
        status_exclude_list = ['Submitted', 'Application Fees Paid', 'Application Fee Paid,Documents Uploaded In Progress', 'Documents to be Resubmitted']
        status_include_list = ['Shortlisted. Offer Mail Sent', 'Accepted by Applicant', 'Admission Fee Paid']
        reject_count_status = ['Rejected. Reject Mail Sent']

        full_submission_count = StudentCandidateApplication.objects.filter(program=pgm, program__program_type='specific').exclude(application_status__in=status_exclude_list).values('program', 'admit_batch', 'admit_sem_cohort').annotate(application_count=Count('id')).order_by()

        offered_count = StudentCandidateApplication.objects.filter(program=pgm, program__program_type='specific', application_status__in=status_include_list).values('program', 'admit_batch', 'admit_sem_cohort').annotate(application_count=Count('id')).order_by()

        reject_count = StudentCandidateApplication.objects.filter(program=pgm, program__program_type='specific', application_status__in=reject_count_status).values('program', 'admit_batch', 'admit_sem_cohort').annotate(application_count=Count('id')).order_by()

        #CandidateSelection table filters here.

        cs = CandidateSelection.objects.filter(~Q(application=None, student_id=None) | ~Q(student_id="")).values_list('application')
        sca = StudentCandidateApplication.objects.filter(program=pgm, program__program_type='specific', id__in=cs).values('program','admit_batch', 'admit_sem_cohort').annotate(application_count=Count('id')).order_by()

        for application in application_count:

            f_count = 0
            o_count = 0
            r_count = 0
            a_count = 0

            if full_submission_count.exists():
                for val in full_submission_count:
                    if application['admit_batch']==val['admit_batch'] and application['admit_sem_cohort']==val['admit_sem_cohort']:

                        f_count = val['application_count']

            if offered_count.exists():
                for val in offered_count:
                    if application['admit_batch']==val['admit_batch'] and application['admit_sem_cohort']==val['admit_sem_cohort']:

                        o_count = val['application_count']

            if reject_count.exists():
                for val in reject_count:
                    if application['admit_batch']==val['admit_batch'] and application['admit_sem_cohort']==val['admit_sem_cohort']:

                        r_count = val['application_count']


            if sca.exists():
                for val in sca:
                    if application['admit_batch']==val['admit_batch'] and application['admit_sem_cohort']==val['admit_sem_cohort']:

                        a_count = val['application_count']

            sds = SpecificAdmissionSummary.objects.filter(program_code=application['program__program_code'],
                                                        admit_batch=application['admit_batch'],
                                                        admit_sem_cohort=application['admit_sem_cohort']
                                                        ).first()
            if sds:
                sds.application_count = application['application_count']  #
                sds.full_submission_count = f_count
                sds.offered_count = o_count
                sds.admission_count = a_count
                sds.reject_count = r_count
                sds.last_updated_datetime = datetime.datetime.now()
                sds.save()
            else:
                SpecificAdmissionSummary.objects.create(
                    specific_program_id=pgm,#
                    program_code=application['program__program_code'],#
                    admit_batch=application['admit_batch'],#
                    admit_sem_cohort=application['admit_sem_cohort'],#
                    application_count=application['application_count'],#
                    full_submission_count=f_count,
                    offered_count=o_count,
                    admission_count=a_count,
                    reject_count=r_count,
                    last_updated_datetime=datetime.datetime.now(),
                )
