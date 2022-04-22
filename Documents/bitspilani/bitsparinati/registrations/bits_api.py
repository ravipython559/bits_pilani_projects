from bits_admin.models import MetaApi
from registrations.models import *
import requests
import json
from django.conf import settings
import logging
logger = logging.getLogger("main")

def get_country(country):
	name = str(country.name)
	return 'United States' if name =='United States of America' else name

def get_location(x):
	if x.application.country.code == 'IN':
		return ('-' if x.application.work_location.location_name=='Not Applicable' else x.application.work_location.location_name.split('(')[0].strip())
	else:
		return 'Others'

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def name_verify_api(query,user_name):
	url = settings.SDMS_URL
	headers = {'Content-type': 'application/json',
		'AuthToken': '7b302a26-b9e3-4584-a573-196517dfe8a7' ,}
	list_of_verify_name = []
	for x in  query:
		ctx = {}
		ctx['ID_NO'] = x.student_id 
		ctx['STUD_NAME'] = x.verified_student_name or x.application.full_name
		ctx['POST_ADD1'] = x.application.address_line_1[:50]
		ctx['POST_ADD2'] = x.application.address_line_2 if x.application.address_line_2 else ' '
		ctx['POST_ADD3'] = x.application.address_line_3 if x.application.address_line_3 else ' '
		ctx['POST_CITY'] = x.application.city
		ctx['POST_STATE'] = dict(STATE_CHOICES)[x.application.state]
		ctx['POST_PIN'] = x.application.pin_code if x.application.pin_code else '111111'
		ctx['EMAIL_ADD'] = x.application.login_email.email
		ctx['STATE_ALT'] = dict(STATE_CHOICES)[x.application.state] if str(x.application.country.name) != 'India' else None
		ctx['MOBILE_NO'] = x.application.mobile.national_number
		ctx['DOB'] = x.application.date_of_birth.strftime('%d-%m-%Y')
		ctx['LOCATION'] = get_location(x)
		#ctx['EXAM_CENTRE'] = x.application.current_location.location_name.split('(')[0].strip().upper() if x.application.current_location else 'PLEASE CHOOSE YOUR EXAM CENTER'
		ctx['EXAM_CENTRE'] = 'PLEASE CHOOSE YOUR EXAM CENTER'
		ctx['CURRENT ORGANIZATION'] = x.application.current_organization
		ctx['COUNTRY'] = get_country(x.application.country)
		ctx['Gender'] = dict(GENDER_CHOICES)[x.application.gender]
		ctx['AWARD_NUMBER'] = ''
		ctx['LIST_NUMBER'] = ''
		ctx['Degree_Serial_Number'] = ''
		ctx['GRADUATED_FLAG'] = None
		ctx['MENTOR_NAME'] = x.m_name
		ctx['MENTOR_ORGANIZATION'] = None
		ctx['MENTOR_DESIGNATION'] = x.m_des
		ctx['MENTOR_QUALIFICATION'] = None
		ctx['MENTOR_EMAIL'] = x.m_email
		ctx['MENTOR_CONTACT_NO'] = x.m_mob_no.national_number if x.m_mob_no else None
		ctx['MENTOR_ADDRESS'] = None
		ctx['CURRENT_WORK_DESIGNATION'] = x.application.current_designation
		ctx['CURRENT_WORK_DOMAIN'] = 'PLEASE CHOOSE YOUR DOMAIN' if x.application.current_org_industry.industry_name == 'Not Applicable' else x.application.current_org_industry.industry_name
		ctx['SEM_ADMIT'] = x.application.admit_batch
		ctx['COUNTRY_CODE'] = x.application.mobile.country_code
		
		if x.application.program.program_type == 'certification':
			year, month = str(x.application.total_work_experience_in_months).split('.')
			experience = 12 * int(year) + int(month)
		else:
			experience = int(x.application.total_work_experience_in_months) / 30

		ctx['TOTAL_WORK_EXPERIENCE'] = experience
		list_of_verify_name.append(ctx)
	list_of_json_response=[]
	a = []
	for x in batch(list_of_verify_name, 500):
		logger.info("*********before the api*****")
		r = requests.post(url, data=json.dumps(x), headers=headers, verify=False)
		logger.info("*********after the api*****")
		r.raise_for_status()
		MetaApi.objects.create(user=user_name, 
		api_request=json.dumps(x),
		api_response=json.dumps(r.json()))
		a.append(MetaApi.objects.last().id)
		list_of_json_response.extend(r.json())
	# request.session['synced_ids'] = a
	return list_of_json_response,a
