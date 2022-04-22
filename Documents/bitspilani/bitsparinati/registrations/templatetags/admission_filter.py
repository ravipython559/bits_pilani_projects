from django import template
from registrations.models import ( StudentCandidateApplication as SCA,
 ExceptionListOrgApplicants as ELOA, CandidateSelection as CS ,
 ProgramDomainMapping as PDM,
 PROGRAM_FEES_ADMISSION as PFA,
 FirstSemCourseList as FSCL, ProgramDocumentMap)
from bits_admin.models import (StudentCandidateApplicationArchived, CandidateSelectionArchived, StudentCandidateWorkExperienceArchived)
from registrations.models import *
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
import datetime 
from datetime import date
from datetime import  timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Max
from bits_rest.zest_utils import emi_in_progress, emi_in_decline
from bits import zest_settings as ZEST


register = template.Library()

@register.filter(name='get_degree_other_string')
def get_degree_other_string(value):
	degree =Degree.objects.get(id=int(value))
	return degree.degree_long_name if degree.degree_long_name == 'Others' else  False

@register.filter(name='get_discpline_other_string')
def get_discpline_other_string(value):
	discpline =Discpline.objects.get(id=int(value))
	return discpline.discipline_long_name if discpline.discipline_long_name == 'Others' else False

@register.filter(name='get_payfee_permission')
def get_payfee_permission(email):

	try:
		query = SCA.objects.get(login_email__email=email)
		if query.application_status == settings.APP_STATUS[16][0]: return True
		eloa = ELOA.objects.get( Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=email, 
			exception_type='1', 
			program=query.program )
		return True 
	except SCA.DoesNotExist: pass
	except ELOA.DoesNotExist: pass 

	return False

@register.filter(name='get_payfee_waiver_permission')
def get_payfee_waiver_permission(email):
	return ELOA.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True), employee_email=email,).exists()

@register.filter(name='get_payfee_adm_permission')
def get_payfee_adm_permission(email):
	return ELOA.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
		employee_email=email,exception_type='2').exists()
		
@register.filter(name='get_ELOA_program')
def get_ELOA_program(email):
	eloa = ELOA.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
		employee_email=email,
		exception_type='1')
	return ', '.join(eloa.values_list('program__program_name', flat=True )) if eloa.exists() else False

@register.filter(name='get_ELOA_org')
def get_ELOA_org(email):
	eloa = ELOA.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True), employee_email=email)
	return eloa[0].org.org_name if eloa.exists() else False

@register.filter(name='get_ELOA_org_num')
def get_ELOA_org_num(email):
	eloa = ELOA.objects.filter(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True), employee_email=email)
	return eloa[0].employee_id if eloa.exists() else False
		
#need to change
@register.inclusion_tag('link.html')
def bits_fill_edit_submit_link(*args, **kwargs):

	ctx = {'title':kwargs['title'], 'sr_no':kwargs['sr_no']}

	try:
		query = SCA.objects.get(login_email__email=kwargs['email'])
		ctx['link'] = reverse_lazy('registrationForm:applicant-data')
		ctx['status'] = 'Resubmit' if query.application_status==settings.APP_STATUS[16][0] else 'Complete'

	except SCA.DoesNotExist:
		eloa = ELOA.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=kwargs['email'],
			exception_type__in=['1','2'])

		ctx['link'] = (reverse_lazy('registrationForm:user-waiver-login') if eloa.exists() 
				else reverse_lazy('registrationForm:user-login'))
		ctx['status'] = 'Pending'

	return ctx


@register.inclusion_tag('link.html')
def bits_app_pdf_link(*args, **kwargs):
	ctx = {'title':kwargs['title'], 'sr_no':kwargs['sr_no']}
	try:
		query = SCA.objects.get(login_email__email=kwargs['email'])
		ctx.update({'link':'#', 'status':'NA', 'target':False,} if query.program.program_type == 'certification' 
			else {'link':reverse_lazy('registrationForm:applicantView'), 'status':'Complete', 'target':True,})

	except SCA.DoesNotExist:
		ctx.update({'link':'#', 'status':'Pending', 'target':False,})

	return ctx


@register.inclusion_tag('link.html')
def bits_payfee_link(*args, **kwargs):
	ctx = {'title':kwargs['title'], 'sr_no':kwargs['sr_no']}
	is_eloa = False
	query=False
	try:
		query = SCA.objects.get(login_email__email=kwargs['email'])
		
		pfa = PROGRAM_FEES_ADMISSION.objects.get(program=query.program, 
			latest_fee_amount_flag=True, 
			fee_type='2')
		eloa = ELOA.objects.get( 
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			application=query,
			exception_type='1', 
			program=query.program,
			employee_email=kwargs['email'])

		is_eloa = True
		ctx.update({'target':False, 'link':'#', 'status':'Not Applicable','is_eloa':is_eloa})

	except SCA.DoesNotExist:
		ctx.update({'target':False, 'link':'#', 'status':'Pending','is_eloa':is_eloa})

	except ELOA.DoesNotExist:
		ctx.update({'target':False, 'link':reverse_lazy('registrationForm:payfeeview'),
		 	'status':'Pending','is_eloa':is_eloa} if query.application_status in [settings.APP_STATUS[12][0],settings.APP_STATUS[18][0]] 
			else {'target':True, 'link':reverse_lazy('registrationForm:payfee'), 'status':'Complete','is_eloa':is_eloa})
		
	finally:
		if query and query.program.enable_pre_selection_flag:
			if query.pre_selected_flag is None and query.application_status == settings.APP_STATUS[12][0]:
				ctx.update({'target':False, 'link':'#', 'status':'Pending Shortlisting (Disabled)','is_eloa':is_eloa})
			elif query.pre_selected_flag == 'Rejected':
				ctx.update({'target':False, 'link':'#', 'status':'Not Applicable','is_eloa':False})
			elif query.pre_selected_flag == 'Accepted' and query.application_status == settings.APP_STATUS[18][0]:
				ctx.update({'target':False, 'link':reverse_lazy('registrationForm:payfeeview'), 'status':'Pending','is_eloa':is_eloa})
				if is_eloa:
					ctx.update({'target':False, 'link':'#', 'status':'Not Applicable','is_eloa':is_eloa})
			else :
				ctx.update({'target':True, 'link':reverse_lazy('registrationForm:payfee'), 'status':'Complete','is_eloa':is_eloa})
				if is_eloa:
					ctx.update({'target':False, 'link':'#', 'status':'Not Applicable','is_eloa':is_eloa})	

	return ctx



@register.filter(name='get_admission_permission')
def get_admission_permission(email):
	try:
		query = SCA.objects.get(login_email__email=email)
		return query.application_status == settings.APP_STATUS[11][0]
	except SCA.DoesNotExist:return False

@register.inclusion_tag('link.html')
def bits_upload_link(*args, **kwargs):
	ctx = {'title':kwargs['title'], 'sr_no':kwargs['sr_no'],}
	query = None
	upl_status=[settings.APP_STATUS[0][0],
	settings.APP_STATUS[1][0], settings.APP_STATUS[5][0], settings.APP_STATUS[6][0],
	settings.APP_STATUS[7][0], settings.APP_STATUS[8][0], settings.APP_STATUS[2][0],
	settings.APP_STATUS[3][0], settings.APP_STATUS[4][0], settings.APP_STATUS[9][0],
	settings.APP_STATUS[10][0], settings.APP_STATUS[11][0], settings.APP_STATUS[17][0],]
	try:
		query = SCA.objects.get(login_email__email=kwargs['email'])
		eloa = ELOA.objects.get(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=kwargs['email'],
			exception_type='1',
			program=query.program)
		link, status = reverse_lazy('registrationForm:student-upload'), 'Pending'

	except (SCA.DoesNotExist, ELOA.DoesNotExist):
		link, status = '#', 'Pending'

	if query:
		if query.application_status == settings.APP_STATUS[13][0]:
			link, status = reverse_lazy('registrationForm:student-upload'), 'Pending'

		elif query.application_status == settings.APP_STATUS[14][0]:
			link, status = reverse_lazy('registrationForm:student-upload-edit'), 'Upload in Progress'

		elif query.application_status in upl_status:
			link, status = reverse_lazy('registrationForm:final-upload-file'), 'Complete'

		elif query.application_status == settings.APP_STATUS[16][0]:
			link, status = '#', 'Pending'

		elif query.program.enable_pre_selection_flag and (query.pre_selected_flag is None or query.pre_selected_flag == 'Rejected'):
				link, status = '#', 'Pending'

		elif query.application_status == settings.APP_STATUS[15][0]:
			try:
				CS.objects.get(application = query, prior_status__in = [settings.APP_STATUS[13][0], 
					settings.APP_STATUS[14][0]] )
				link, status = '#', 'Pending'
			except CS.DoesNotExist:
				link, status = reverse_lazy('registrationForm:final-upload-file'), 'Complete'

	ctx.update({'link': link, 'status': status})

	return ctx


@register.filter(name='get_app_status')
def get_app_status(status):
	for x in settings.APP_STATUS:
		if x[0] == status:
			return x[1]
	return status

@register.filter(name='get_ELOA_ap_view_permissions')
def get_ELOA_ap_view_permissions(email):
	upl_status=[settings.APP_STATUS[0][0],
	settings.APP_STATUS[1][0], settings.APP_STATUS[5][0], settings.APP_STATUS[6][0],
	settings.APP_STATUS[7][0], settings.APP_STATUS[8][0], settings.APP_STATUS[2][0],
	settings.APP_STATUS[3][0], settings.APP_STATUS[4][0], settings.APP_STATUS[9][0],
	settings.APP_STATUS[10][0], settings.APP_STATUS[11][0], settings.APP_STATUS[17][0],]

	try:
		sca = SCA.objects.get(login_email__email=email)
		eloa = ELOA.objects.get(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True), 
			employee_email=email, 
			exception_type='1',
			program=sca.program )

		return sca.application_status in upl_status

	except ELOA.DoesNotExist:
		return False

@register.inclusion_tag('registration_view_link_table.html')
def bits_registration_view_link(email,*args, **kwargs):
	upl_status=[settings.APP_STATUS[0][0],
	settings.APP_STATUS[1][0], settings.APP_STATUS[5][0], settings.APP_STATUS[6][0],
	settings.APP_STATUS[7][0], settings.APP_STATUS[8][0], settings.APP_STATUS[2][0],
	settings.APP_STATUS[3][0], settings.APP_STATUS[4][0], settings.APP_STATUS[9][0],
	settings.APP_STATUS[10][0], settings.APP_STATUS[11][0], settings.APP_STATUS[15][0],
	settings.APP_STATUS[17][0],settings.APP_STATUS[18][0],settings.APP_STATUS[19][0]]

	app = SCA.objects.get(login_email__email=email)
	context={}
	context['fullname']=app.full_name
	context['c_o_d'] = app.created_on_datetime
	context['location'] = app.current_location
	context['program_name'] = app.program.program_name
	context['app_status'] = app.application_status
	context['app_ap_id'] = app.application_id
	try:
		eloa = ELOA.objects.get(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True), 
			employee_email=email, exception_type='1', program = app.program)
		context['link'] = (reverse_lazy('registrationForm:student-application-views') if app.application_status in upl_status 
			else reverse_lazy('registrationForm:student-application-edit'))
	except ELOA.DoesNotExist:
		stat = upl_status + [settings.APP_STATUS[13][0],settings.APP_STATUS[14][0]]
		context['link'] = ( reverse_lazy('registrationForm:student-application-views') if app.application_status in stat 
		else reverse_lazy('registrationForm:student-application-edit') )

	return context
	
@register.filter(name='get_reviewers_status')
def get_reviewers_status(email):
	APP_CHOICE=[settings.APP_STATUS[x][0] for x in range(12)]
	APP_CHOICE.append(settings.APP_STATUS[15][0])
	APP_CHOICE.append(settings.APP_STATUS[17][0])
	try:
		SCA.objects.get(application_status__in=APP_CHOICE,
			login_email__email=email,)
	except SCA.DoesNotExist:
		return False
	else:
		return True

@register.inclusion_tag('application_status_table.html')
def bits_reviewed_status(*args, **kwargs):
	app = SCA.objects.get(login_email__email=kwargs['email']) #retrieved all fields of respective email in app object
	app_id = app.student_application_id

	try:
		eloa = ELOA.objects.get(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=kwargs['email'],
			exception_type='2',
			program = app.program)
		if app.application_status == settings.APP_STATUS[9][0]:
			return {'app_id':app_id,'status':settings.APP_STATUS[9][1], 
			'action':'View/Download Offer Letter','link': reverse_lazy('registrationForm:offer-letter'), 
			'target':'_blank','email':kwargs['email'],}

	except ELOA.DoesNotExist: pass 

	if app.application_status == settings.APP_STATUS[11][0]:
		return {'app_id':app_id,'status':settings.APP_STATUS[11][1],
		'action':settings.APP_STATUS[11][2],'link': settings.APP_STATUS[11][3],
		'target':'_blank','email':kwargs['email'],}

	for x in settings.APP_STATUS:
		if x[0] == app.application_status:
			return {'app_id':app_id, 'status':x[1],'action':x[2],
			 'link': x[3], 'target':'' ,'email':kwargs['email'],}


@register.inclusion_tag('applicant_view_url.html')
def bits_applicantView_urls_link(*args, **kwargs):
	bits_urls = []
	waiver = None
	try:
		query = SCA.objects.get(login_email__email=kwargs['email'])
		waiver = ELOA.objects.get(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=kwargs['email'],
			exception_type='1',
			program = query.program)
		if query.program.program_type != 'certification':
			bits_urls.append({'link':reverse_lazy('registrationForm:applicantView'),
			 'target':'_blank',
			 'url':'Download Application PDF' })

		bits_urls.append({'link':reverse_lazy('registrationForm:payfee'),
				'target':'_blank', 'url':'Download Fee Receipt' })

	except SCA.DoesNotExist:
		return False

	except ELOA.DoesNotExist:
		if query.application_status == settings.APP_STATUS[12][0]:
			bits_urls.append({'link':reverse_lazy('registrationForm:payfeeview'),
				'target':'', 'url':'Pay Fees' })
		else:
			bits_urls.append({'link':reverse_lazy('registrationForm:payfee'),
				'target':'_blank', 'url':'Download Fee Receipt' })

	if query.application_status == settings.APP_STATUS[11][0]:
		bits_urls.append({'link':reverse_lazy('registrationForm:pay-admission-fee'),
				'target':'_blank', 'url':'Download Admission Fee Receipt' })

	elif query.application_status == settings.APP_STATUS[14][0]:
		bits_urls.append({'link':reverse_lazy('registrationForm:student-upload-edit'),
				'target':'', 'url':'Edit Upload Documents' })

	elif query.application_status == settings.APP_STATUS[13][0]:
		bits_urls.append({'link':reverse_lazy('registrationForm:student-upload'),
				'target':'', 'url':'Upload Documents' })

	elif query.application_status == settings.APP_STATUS[3][0]:
		bits_urls.append({'link':reverse_lazy('registrationForm:reload-documentation'),
				'target':'', 'url':'Resubmit Documents' })

	return {'bits_urls':bits_urls}


@register.inclusion_tag('applicant_view_url.html')
def bits_applicant_form_view_urls_link(*args, **kwargs):
	try:
		query = SCA.objects.get(login_email__email=kwargs['email'])
	except SCA.DoesNotExist:
		return False
	else:
		bits_urls = []
		if query.application_status == settings.APP_STATUS[14][0]:
			#Application Fee Paid,Documents Uploaded In Progress
			urls={}
			urls['link'] = reverse_lazy('registrationForm:student-upload-edit')
			urls['target'] = ''
			urls['url'] = 'Edit Upload Documents'
			bits_urls.append(urls)

		elif query.application_status == settings.APP_STATUS[13][0]:
			#Fees Paid
			urls={}
			urls['link'] = reverse_lazy('registrationForm:student-upload')
			urls['target'] = ''
			urls['url'] = 'Upload Documents'
			bits_urls.append(urls)

	return {'bits_urls':bits_urls}

@register.filter(name='get_admission_fee_status')
def get_admission_fee_status(email):
	
	try:
		query = SCA.objects.get(application_status=settings.APP_STATUS[9][0],
			login_email__email=email,)

		ELOA.objects.get(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=email, 
			exception_type='2', 
			program = query.program,)

	except SCA.DoesNotExist:
		return False
	except ELOA.DoesNotExist:
		return True 
	return	False

@register.filter(name='get_app_program')
def get_app_program(email):
	app = SCA.objects.get(application_status__in=[
		settings.APP_STATUS[9][0],settings.APP_STATUS[12][0]],
			login_email__email=email,)
	return app.program.program_name

@register.filter(name='get_admission_fee_payed_status')
def get_admission_fee_payed_status(email):
	
	try:
		SCA.objects.get(application_status__in=[settings.APP_STATUS[11][0],
			# settings.APP_STATUS[6][0],
			settings.APP_STATUS[9][0]],
			login_email__email=email,)
	except SCA.DoesNotExist:
		return False
	else:
		return True

@register.filter(name='get_app_program_fee_payed')
def get_app_program_fee_payed(email):
	app = SCA.objects.get(application_status=settings.APP_STATUS[11][0],
			login_email__email=email,)
	return app.program.program_name

@register.filter(name='get_admission_stsc_status')
def get_admission_stsc_status(email):
	
	try:
		SCA.objects.get(application_status__in=[
			# settings.APP_STATUS[6][0],
			settings.APP_STATUS[9][0]],
			login_email__email=email,)
	except SCA.DoesNotExist:
		return False
	else:
		return True

@register.filter(name='is_ELOA_mail_send_shortlist')
def is_ELOA_mail_send_shortlist(email):
	try:
		query = SCA.objects.get(login_email__email=email,
			application_status__in=[settings.APP_STATUS[6][0], 
			settings.APP_STATUS[9][0]]
		)

		eloa = ELOA.objects.get(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email = email, 
			exception_type = '2', 
			program = query.program,
		)

	except (SCA.DoesNotExist, ELOA.DoesNotExist):
		return False

	return True
	
@register.filter(name='get_roll_no')
def get_roll_no(email):
	query = SCA.objects.get(login_email__email=email)
	if query.application_status == settings.APP_STATUS[11][0]:
		return CS.objects.get(application=query).student_id
	else:
		return False

@register.filter(name='is_ELOA_admission')
def is_ELOA_admission(email):
	query = SCA.objects.get(login_email__email=email)
	try:
		ELOA.objects.get(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=email,
			exception_type='2',
			program = query.program )

	except ELOA.DoesNotExist:
		return False
	return True


@register.filter(name='get_waiver_roll_no')
def get_waiver_roll_no(email):
	query = SCA.objects.get(login_email__email=email)
	if query.application_status == settings.APP_STATUS[9][0]:
		return CS.objects.get(application=query).student_id
	else:
		return False


@register.filter(name='is_specific_user')
def is_specific_user(email):
	s_e = PDM.objects.filter(email = email).exists()
	s_d = PDM.objects.filter(email_domain__iexact = email.split('@')[1]).exists()
	return True if s_e or s_d else False  

@register.filter(name='is_CIOT_user')
def is_CIOT_user(email):
	try:
		query = SCA.objects.get(login_email__email=email)
	except SCA.DoesNotExist: return False
	return True if query.program.program_code == 'CIOT' else False


@register.inclusion_tag('link.html')
def bits_specific_fill_edit_submit_link(*args, **kwargs):

	try:
		query = SCA.objects.get(login_email__email=kwargs['email'])

	except SCA.DoesNotExist:
		s_e = PDM.objects.filter(email = kwargs['email']).exists()
		s_d = PDM.objects.filter(email_domain__iexact = kwargs['email'].split('@')[1]).exists()
		if s_e or s_d :
			link = reverse_lazy('application_specific:specific_user_program')
		else:
			link = ''

		
		status = 'Pending'

	else:
		#submitted or others
		link = reverse_lazy('registrationForm:applicant-data')
		status = 'resubmit' if query.application_status == settings.APP_STATUS[16][0] else 'Complete'

	return {'link':link,'title':kwargs['title'],
	'status':status,'sr_no':kwargs['sr_no']}



@register.filter(name='get_admission_reviewer_offer_letter')
def get_admission_reviewer_offer_letter(email):
	
	try:
		SCA.objects.get(application_status__in=[
			settings.APP_STATUS[9][0],
			settings.APP_STATUS[11][0],],
			login_email__email=email,)
	except SCA.DoesNotExist:
		return False
	else:
		return True

# preview offer letter start
@register.filter(name='get_preview_offer_letter')
def get_preview_offer_letter(email):
	
	try:
		SCA.objects.get(application_status=settings.APP_STATUS[5][0],
			login_email__email=email,)
	except SCA.DoesNotExist:
		return False
	else:
		return True

@register.filter(name='offer_letter_assigned')
def offer_letter_assigned(email):

	app = SCA.objects.get(login_email__email=email)
	try:
		ap_exp = ApplicantExceptions.objects.get(applicant_email=app.login_email.email,
			program = app.program,transfer_program__isnull=False)

		if ap_exp.transfer_program and (ap_exp.transfer_program.offer_letter_template or ap_exp.offer_letter ):
			return True
		else:
			return False
				
	except ApplicantExceptions.DoesNotExist:pass 

	if app.program.offer_letter_template:
		return True
	else:
		return False

@register.filter(name='pg_loc_assigned')
def pg_loc_assigned(email):

	app = SCA.objects.get(login_email__email=email)
	prog = app.program
	try:
		ae = ApplicantExceptions.objects.get(applicant_email = email,
			program = prog)
		prog = ae.transfer_program if ae.transfer_program else prog

	except ApplicantExceptions.DoesNotExist:
		pass

	try:
		ProgramLocationDetails.objects.get(program = prog,
			location = app.current_location
			)
		return True
				
	except ProgramLocationDetails.DoesNotExist:return False	

@register.simple_tag(takes_context = True)
def cookie(context, cookie_name): 
	request = context['request']
	result = request.COOKIES.get(cookie_name,None) 

@register.filter(name='is_employed')
def is_employed(email):
	sca = SCA.objects.get(login_email__email = email)
	return False if sca.current_employment_status=='2' else  True

@register.filter(name='get_course_list')
def get_course_list(application):
	fscl = FirstSemCourseList.objects.filter(
		program__program_code=application.program.program_code,
		admit_year =application.admit_year,
		active_flag=True
	)
	return True if fscl.exists() else False

@register.filter(name='esc_applicant')
def esc_applicant(status):
	return True if status == settings.APP_STATUS[15][0] else False

@register.simple_tag
def display_url(value):	
	return str(value).split(' ')[0]

@register.filter(name='rev_or_surev_comment')
def rev_or_surev_comment(value):
	try:
		cs = CS.objects.get(application__id =value)
	except CS.DoesNotExist:
		return False
	else:
		if not cs.su_rev_com and not cs.es_com:return False
		return """
		Escalation Comments {0}
		
		""".format(cs.es_com)

@register.simple_tag
def application_fees_paid(value):	
	return value

@register.filter(name='is_hr_men_filled')
def is_hr_men_filled(email):
	try:
		cs = CS.objects.get(
				application__login_email__email = email,
				application__application_status__in = [
				settings.APP_STATUS[11][0],
				settings.APP_STATUS[9][0]
				],
				)
		ap_exp = ApplicantExceptions.objects.get(applicant_email=email,
		program = cs.application.program)
		is_mentor_required = not ap_exp.mentor_waiver and cs.application.program.mentor_id_req
		is_hr_required = not ap_exp.hr_contact_waiver and cs.application.program.hr_cont_req
			 
	except CS.DoesNotExist:
		return False

	except ApplicantExceptions.DoesNotExist:
		check_mentor = cs.application.program.mentor_id_req and not cs.m_email
		check_hr = cs.application.program.hr_cont_req and not cs.hr_cont_email
		return check_mentor or check_hr

	else :
		check_mentor = is_mentor_required and not cs.m_email
		check_hr = is_hr_required and not cs.hr_cont_email
		return check_mentor or check_hr

@register.simple_tag
def hr_men_link():	
	return '''
	<a href={0}>Provide Mentor and HR Contact Details</a>
	'''.format(reverse_lazy('reviewer:accept-offer-later'))

@register.filter(name='is_resubmit_status')
def is_resubmit_status(email):
	sca = SCA.objects.get(login_email__email=email)
	return True if sca.application_status==settings.APP_STATUS[16][0] else False

@register.filter(name='is_waiver_prog_perm')
def is_waiver_prog_perm(email):

	try:
		query = SCA.objects.get(login_email__email=email)
		pg_code = query.program.program_code
		eloa = ELOA.objects.filter(
			Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
			employee_email=email,
			exception_type__in=['1','2'],
			program = query.program)
	except SCA.DoesNotExist:
		return False

	return eloa.exists()

@register.simple_tag
def display_waiver_spec_y_m_d(months):	

	return '{0} Years {1} Months'.format(months/12,months%12)
	
@register.simple_tag
def display_y_m_d(email):
	sca=SCA.objects.get(login_email__email = email)
	exp=StudentCandidateWorkExperience.objects.filter(application = sca)
	tmp = timedelta(days=0)
	for x in exp:
		tmp += x.end_date - x.start_date
	tmp += sca.last_updated_on_datetime.date() - sca.current_org_employment_date
	d = date.fromordinal(tmp.days)
	return '{0} Years {1} Months {2} days'.format(d.year-1,d.month-1,d.day-1)


@register.simple_tag
def c_w_e(email):
	st = SCA.objects.get(login_email__email = email)
	diff = relativedelta(st.last_updated_on_datetime.date(), st.current_org_employment_date)
	return '{0} Years {1} Months {2} days'.format(diff.years,diff.months,diff.days)

@register.inclusion_tag('offer_status_table.html')
def bits_offer_status_td(app_stud_id):
	ctx = {}
	sca = SCA.objects.get( id = app_stud_id.value() )
	ctx['admit_batch'] = sca.admit_batch
	ctx['fullname'] = sca.full_name
	ctx['c_o_d'] = sca.created_on_datetime
	ctx['program_name'] = sca.program
	ctx['app_status'] = sca.application_status
	ctx['id'] = sca.id
	ctx['app_stud_id'] = sca.student_application_id
	return ctx

@register.filter(name='esc_applicant_check')
def esc_applicant_check(app_stud_id):
	sca = SCA.objects.get( id = app_stud_id.value() )

	return True if sca.application_status == settings.APP_STATUS[15][0] else False

@register.filter(name='is_in')
def is_in(app_stud_id, applicant):
	if applicant is None:return False
	return applicant.filter(id = app_stud_id.value()).exists()

@register.filter(name='is_in_dict')
def is_in_dict(app_stud_id, mark_data):

	if mark_data is None:return False

	for key,value in mark_data.items():
		if int(key) == int(app_stud_id.value()):return True
	else:
		return False

@register.assignment_tag
def is_in_dict_pg(app_stud_id, mark_data):

	if mark_data is None:return ''

	for key,value in mark_data.items():
		if int(key) == int(app_stud_id.value()):return value
	else:
		return ''

@register.simple_tag
def display_new_program(pg):
	return Program.objects.get(id = int(pg.value())).program_name

@register.filter(name='times') 
def times(number):
	return range(1,number+1)

@register.assignment_tag
def list_pages( total_page, current_page ):
	start_index = current_page - 3 if current_page >= 3 else 0
	end_index = current_page + 3 if current_page <= total_page - 3 else total_page
	return range(start_index+1,end_index+1)

@register.filter(name='chk_max_stuID')
def chk_max_stuID(app_id):
	app = SCA.objects.get(id=int(app_id))
	pfa = PFA.objects.get(program=app.program,
		fee_type = '1',latest_fee_amount_flag=True)
	max_id = CS.objects.filter(
		application__admit_year=pfa.admit_year,
		application__program = pfa.program,
		student_id__contains = pfa.program.program_code,
		).aggregate(Max('student_id'))
	pg_code = pfa.program.program_code
	student_max_id = int(max_id['student_id__max'][-3:]) if max_id['student_id__max'] else 0

	if student_max_id >= 999 and \
		( app.application_status==settings.APP_STATUS[9][0] or 
			app.application_status==settings.APP_STATUS[11][0] ):
		for x in filter(lambda x: x != '', pfa.program.alternative_program_code.split(',')):
			max_id = CS.objects.filter(
				application__admit_year=pfa.admit_year,
				application__program = pfa.program,
				student_id__contains = x,
				).aggregate(Max('student_id'))
			student_max_id = int(max_id['student_id__max'][-3:]) if max_id['student_id__max'] else 0
			if student_max_id < 999 :return False
		else:
			return True

	return False

@register.filter(name='stuID_exists')
def stuID_exists(app_id):
	try:
		app = SCA.objects.get(id=int(app_id))
		cs = CS.objects.get(application = app)
	except (CS.DoesNotExist,TypeError):
		return False
	return True if cs.student_id else False

@register.filter(name='id_gen_st_check1')
def id_gen_st_check1(app_id):
	app = SCA.objects.get(id=int(app_id))
	if app.application_status==settings.APP_STATUS[9][0] or app.application_status==settings.APP_STATUS[11][0]:

		try:
			eloa = ELOA.objects.get(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True),
				employee_email=app.login_email.email,exception_type='2',
				program=app.program)
		except ELOA.DoesNotExist:
			if app.application_status==settings.APP_STATUS[9][0]:
				return False
		return True
	return False

@register.filter(name='status_check_student_id')
def status_check_student_id(app_id):
	app = SCA.objects.get(id=int(app_id))
	if app.application_status != settings.APP_STATUS[9][0] or app.application_status != settings.APP_STATUS[11][0]:
		return True
	try:
		eloa = ELOA.objects.get(Q(fee_amount__lt = 0.01)|Q(fee_amount__isnull=True), 
			employee_email=app.login_email.email, exception_type='2', program=app.program)
	except ELOA.DoesNotExist:
		if app.application_status==settings.APP_STATUS[9][0]: return True

	return False

@register.filter(name='is_verified')
def is_verified(email):
	try:
		cs = CS.objects.get(application__login_email__email=email)
	except CS.DoesNotExist:
		return False
	return True if cs.verified_student_name else False

@register.simple_tag
def vr_name(email):
	return CS.objects.get(application__login_email__email = email
		).verified_student_name

@register.simple_tag
def get_stu_id(email):
	return CS.objects.get(application__login_email__email=email).student_id

@register.filter(name='is_payment_and_reviewer')
def is_payment_and_reviewer(rev):
	if rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[1][0]:
		return False
	if rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[2][0]:
		return False
	return True if rev.reviewer and rev.payment_reviewer else False

@register.filter(name='only_payment_reviewer')
def only_payment_reviewer(rev):
	if rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[1][0]:
		return False
	if rev.reviewer and rev.payment_reviewer:
		return False
	return True if rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[2][0] else False

@register.filter(name='pr_check_in_admin')
def pr_check_in_admin(user):
	try:
		rev = user.reviewer
	except : return False
	return rev.reviewer and rev.user_role == Reviewer.REVIEWER_CHOICES[2][0]

@register.filter(name='is_regen_offer_button')
def is_regen_offer_button(student_application_id):
	try:
		sca = SCA.objects.get(
			student_application_id=student_application_id,
			application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[11][0]],
			)
		return True
	except SCA.DoesNotExist:
		return False

@register.filter(name='is_pld_record')
def is_pld_record(student_application_id):
	try:
		sca = SCA.objects.get(student_application_id=student_application_id,)
		pld = ProgramLocationDetails.objects.get(program=sca.program, location=sca.current_location)
		return True
	except ProgramLocationDetails.DoesNotExist: return False

@register.filter(name='is_payment_reviewer_flag')
def is_payment_reviewer_flag(rev): return rev.reviewer and rev.payment_reviewer

@register.filter(name='get_certificate_payfee_text')
def get_certificate_payfee_text(email):
	try:
		sca = StudentCandidateApplication.objects.get(login_email__email=email, 
			program__program_type='certification')
		return True
	except StudentCandidateApplication.DoesNotExist: return False

@register.filter(name='get_deffered_mandatory_doc_status')
def get_deffered_mandatory_doc_status(email):
	try:
		query = SCA.objects.get(login_email__email=email,
			application_status__in=[settings.APP_STATUS[9][0],settings.APP_STATUS[11][0]],
			)
		uploaded_docs_pk = ApplicationDocument.objects.filter(
			application=query,
			accepted_verified_by_bits_flag=True,
			).exclude(
				Q(file='')|Q(file__isnull=True)
				).values_list('document__pk')

		missing_docs = ProgramDocumentMap.objects.filter(
				Q(deffered_submission_flag=True)|Q(mandatory_flag=True
			),
			program=query.program
			).exclude(
			document_type__in=uploaded_docs_pk
			)
		return True if missing_docs else False
	except SCA.DoesNotExist: return False

	return False
	
@register.filter(name='get_deffered_mandatory_offer_status')
def get_deffered_mandatory_offer_status(email):
	missing_document_query = ApplicationDocument.objects.filter(Q( Q(file='')|Q(file__isnull=True),
        Q(program_document_map__deffered_submission_flag=True)|Q(program_document_map__mandatory_flag=True))|Q
        (Q(file__isnull=False),Q(program_document_map__deffered_submission_flag=True),Q(reload_flag=True),
        Q(exception_notes='Deferred'))|
        Q(Q(file__isnull=False),Q(rejected_by_bits_flag=True)),
        application__login_email__email=email,
        application__application_status__in=[settings.APP_STATUS[5][0],
            settings.APP_STATUS[6][0],
            settings.APP_STATUS[9][0],
            settings.APP_STATUS[11][0]],
    )

	return missing_document_query.exists()

@register.filter(name='get_deff_offer_status')
def get_deff_offer_status(email):
	ad = ApplicationDocument.objects.filter(application__login_email__email=email)
	list_docs_submitted = []
	for each_ad in ad:
		list_docs_submitted.append(each_ad.document.id)
	application_id = ad[0].application.student_application_id
	pdm = ProgramDocumentMap.objects.filter(program__program_code=application_id[1:5])
	deff_docs_ids = []
	for each_pdm in pdm:
		if each_pdm.deffered_submission_flag == True:
			deff_docs_ids.append(each_pdm.document_type.id)
	# to check atleast one deff doc is not present
	s = False
	for each in deff_docs_ids:
		if each not in list_docs_submitted:
			s = True
			break
	# not submitted all deff docs
	def_docs_not_submitted = []
	def_docs_submitted = []
	for each in deff_docs_ids:
		if each not in list_docs_submitted:
			def_docs_not_submitted .append(each)
		else:
			def_docs_submitted.append(each)
	# no deff docs for the particular program id
	if len(deff_docs_ids) == 0:
		return False
	#not submitted all deff docs
	elif len(def_docs_not_submitted )==len(deff_docs_ids):
		return True
	elif s==False:
		# submitted deff doc but got deferred for later submission or rejected
		for each_ad in ad:
			if each_ad.document.id in def_docs_submitted:
				if each_ad.reload_flag == True and each_ad.exception_notes == 'Deferred':
					s = True
					break
				if each_ad.rejected_by_bits_flag == True:
					s = True
					break
		return s
	else:
		return s


@register.simple_tag
def deff_mandatory_doc_submission_link():
	return '''
	<a href={0}>Submit Missing Documents</a>
	'''.format(reverse_lazy('reviewer:submit-deferred-mandatory-docs'))


@register.filter(name='get_deff_mandat_status_at_acceptance')
def get_deff_mandat_status_at_acceptance(email):
	try:
		query = SCA.objects.get(login_email__email=email,
			application_status=settings.APP_STATUS[6][0],
			)
		uploaded_docs_pk = ApplicationDocument.objects.filter(
			application=query,
			accepted_verified_by_bits_flag=True,
			).exclude(
				Q(file='')|Q(file__isnull=True)
				).values_list('document__pk')

		missing_docs = ProgramDocumentMap.objects.filter(
				Q(deffered_submission_flag=True)|Q(mandatory_flag=True
			),
			program=query.program
			).exclude(
			document_type__in=uploaded_docs_pk
			)
		return True if missing_docs else False
	except SCA.DoesNotExist: return False

	return False

@register.filter(name = 'get_elective_list')
def get_elective_list(email):
	try:
		cs = CS.objects.get(application__login_email__email = email,)
		fscl = FSCL.objects.filter(program = cs.application.program,
			admit_year =cs.application.admit_year,is_elective = True).exists()
		return True if cs.student_id and fscl else False

	except CS.DoesNotExist: return False

@register.simple_tag
def elective_selection_link():
	return '''
	<a href ={0}>Choose Course Electives</a>
	'''.format(reverse_lazy('registrationForm:choose-electives'))

@register.inclusion_tag('bits_rest/emi_progress.html')
def is_emi_in_progress(email):
	return ({'link':ZEST.ZEST_PORTAL_LINK,'is_progress': True} 
		if emi_in_progress(email) else {'is_progress': False})

@register.filter(name='is_emi_status_declined')
def is_emi_status_declined(email):
	return True	if emi_in_decline(email) else False

@register.filter(name='get_deffered_mandatory_doc_submitted_status')
def get_deffered_mandatory_doc_submitted_status(email):
	try:
		query = SCA.objects.get(login_email__email=email,
			application_status__in=[settings.APP_STATUS[0][0]],
			)
		uploaded_docs_pk = ApplicationDocument.objects.filter(
			application=query
			).exclude(
				Q(file='')|Q(file__isnull=True)
				).values_list('document__pk')

		missing_docs = ProgramDocumentMap.objects.filter(
				Q(deffered_submission_flag=True)|Q(mandatory_flag=True
			),
			program=query.program
			).exclude(
			document_type__in=uploaded_docs_pk
			)
		return True if missing_docs else False
	except SCA.DoesNotExist: return False

	return False

@register.filter(name='subject_list')
def subject_list(user):
	sub_list=['English (E)','Mathematics (M)','Physics (P)','Chemistry (C)','Biology (B)','','',]
	return sub_list

@register.filter(name='pcmb_list')
def pcmb_list(user):
	pcmb_list=['PCM %','PCB %',]
	return pcmb_list

@register.filter(name='is_pre_sel_rej_button')
def is_pre_sel_rej_button(app_id):
	try:
		sca = SCA.objects.get(
			id=int(app_id),
			program__enable_pre_selection_flag = True,
			application_status__in=[settings.APP_STATUS[12][0]],
			)
		return True
	except SCA.DoesNotExist:
		return False

@register.filter(name='calculate_hcl_sem_fee')
def calculate_hcl_sem_fee(adm_fee,value):	
	return (adm_fee-value)

@register.filter(name='get_rej_reason_sel_comments')
def get_rej_reason_sel_comments(email):
	
	try:
		SCA.objects.get(application_status__in=[
			settings.APP_STATUS[7][0],
			settings.APP_STATUS[8][0],],
			login_email__email=email,)
	except SCA.DoesNotExist:
		return False
	else:
		return True

