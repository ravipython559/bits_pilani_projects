import requests
from django.conf import settings
from django.utils import timezone
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
import io
from registrations.models import StudentCandidateQualification, SaleForceAuthResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail

def sending_mail(key_params):
    subject = "Specific Admission Summary Data"
    msg_plain = render_to_string('specific_email_content.txt', {'error_code': key_params})
    msg_html = render_to_string('specific_email_content.html', {'error_code': key_params})
    send_mail(subject, msg_plain,
              '<' + settings.FROM_EMAIL + '>',
              ['bits.wilp@accionlabs.com', 'shantanu@hyderabad.bits-pilani.ac.in'],
              html_message=msg_html, fail_silently=True)


def send_alert_mail(key_params):
    subject = "SALEFORCE SYNC FAILURE"
    msg_plain = render_to_string('salesforce_failure_alert_mail.txt', {'error_code': key_params})
    msg_html = render_to_string('salesforce_failure_alert_mail.html', {'error_code': key_params})
    send_mail(subject, msg_plain,
              '<' + settings.FROM_EMAIL + '>',
              ['bits.wilp@accionlabs.com', 'shantanu@hyderabad.bits-pilani.ac.in'],
              html_message=msg_html, fail_silently=True)


def request_call(method, url, **kwargs):
    try:
        response = method(url, **kwargs)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        sf_error = getattr(response, 'json', lambda: {'sf_error': None})
        status_code = getattr(response, 'status_code', 400)
        raise Exception({'error': str(err), 'sf_error': sf_error(), 'status': status_code})
    return response.json(), response.status_code


def authentication(session):
    data = {'username': settings.SF_USERNAME, 'password': settings.SF_PASSWORD,
            'client_id': settings.SF_CLIENT_ID, 'client_secret': settings.SF_CLIENT_SECRET,
            'grant_type': settings.SF_GRANT_TYPE,
            }

    return request_call(session.post, settings.SF_AUTH_URL, data=data)

def sf_api_call(obj_name, data, ref_id, log_model, key_params, is_inserted=False, access_token_expired=False):
    final_block_execution = True
    key_params_for_failure_case = {}
    key_params_for_failure_case['obj_name'] = obj_name
    key_params_for_failure_case['data'] = data
    key_params_for_failure_case['ref_id'] = ref_id
    key_params_for_failure_case['log_model'] = log_model
    key_params_for_failure_case['key_params'] = key_params
    key_params_for_failure_case['is_inserted'] = is_inserted
    content = JSONRenderer().render(data)
    stream = io.BytesIO(content)
    data = JSONParser().parse(stream)
    key_params['is_inserted'] = is_inserted
    key_params['reference_id'] = ref_id
    key_params['dataset'] = data
    key_params['response'] = {}

    try:

        with requests.Session() as session:
            sf_auth_resp = SaleForceAuthResponse.objects.last()
            if not sf_auth_resp:
                auth, status_code = authentication(session)
                s = SaleForceAuthResponse.objects.create(json_resp=auth, status_code=status_code)
                s.save()
            if access_token_expired == True:
                auth, status_code = authentication(session)
                s = SaleForceAuthResponse.objects.last()
                s.json_resp = auth
                s.status_code = status_code
                s.save()
            sf_auth_resp = SaleForceAuthResponse.objects.last()
            key_params['response']['auth'] = {'authentication': sf_auth_resp.json_resp, 'status_code': sf_auth_resp.status_code}

            headers = {
                'Content-type': 'application/json',
                'Authorization': '%s %s' % (sf_auth_resp.json_resp['token_type'], sf_auth_resp.json_resp['access_token']),
            }


            key_params['sent_to_sf_on'] = timezone.now()
            if is_inserted:
                url = '%s/services/data/v44.0/composite/tree/%s/' % (sf_auth_resp.json_resp['instance_url'], obj_name)
                if obj_name == 'B2B_Admission_Details__c':
                    url = '%s/services/data/v51.0/composite/tree/%s/' % (sf_auth_resp.json_resp['instance_url'], obj_name)
                response, status_code = request_call(session.post, url, json=data, headers=headers)
            else:
                url = '%s/services/data/v44.0/composite/sobjects' % (sf_auth_resp.json_resp['instance_url'],)
                if obj_name == 'B2B_Admission_Details__c':
                    url = '%s/services/data/v51.0/composite/sobjects' % (sf_auth_resp.json_resp['instance_url'],)
                response, status_code = request_call(session.patch, url, json=data, headers=headers)

            key_params['status'] = status_code
            key_params['response']['model'] = {'response': response, 'status_code': status_code}

    except Exception as e:
        key_params['status'] = 400
        key_params['response']['error'] = str(e)
        if obj_name == 'B2B_Admission_Details__c':
            # If anything fails on Insert it comes into Exception block
            replace_singlequote = str(e).replace("\'", '')
            replace_doublequote = replace_singlequote.replace('\"', '')
            sending_mail(replace_doublequote)
        else:
            replace_singlequote = str(e).replace("\'", '')
            replace_doublequote = replace_singlequote.replace('\"', '')
            if "INVALID_SESSION_ID" in replace_doublequote:
                final_block_execution = False
                sf_api_call(key_params_for_failure_case['obj_name'], key_params_for_failure_case['data'],
                            key_params_for_failure_case['ref_id'], key_params_for_failure_case['log_model'],
                            key_params_for_failure_case['key_params'], key_params_for_failure_case['is_inserted'],
                            access_token_expired=True)
            else:
                send_alert_mail(replace_doublequote)


    finally:
        if final_block_execution == True:
            if obj_name == 'B2B_Admission_Details__c':
                # log.status 200 will come on update
                if key_params['status'] == 200:
                    # If anything fails on update, success will be False
                    if response[0]['success'] == False:
                        key_params['status'] = 400
                        key_params['response']['error'] = str(response[0]['errors'])
                        replace_singlequote = str(response[0]['errors']).replace("\'", '')
                        replace_doublequote = replace_singlequote.replace('\"', '')
                        sending_mail(replace_doublequote)
            else:
                # log.status 200 will come on update
                if key_params['status'] == 200:
                    # If anything fails on update, success will be False
                    if response[0]['success'] == False:
                        key_params['status'] = 400
                        key_params['response']['error'] = str(response[0]['errors'])
                        replace_singlequote = str(response[0]['errors']).replace("\'", '')
                        replace_doublequote = replace_singlequote.replace('\"', '')
                        send_alert_mail(replace_doublequote)
            log = log_model.objects.create(**key_params)
            return log


def saleforce_api(sf_api_obj, instance, serializer, log_model, log_param, serializer_fields=None):
    s = serializer([instance], many=True, sf_fields=serializer_fields)
    if s.data[0]['attributes']['type'] == 'Education__c':
        if not instance.application:
            # we are writing this code when application is not found in the instance, so manually adding the
            # application from the database to json.
            split_qualification_id = s.data[0]['attributes']['referenceId'].split('_')[2]
            a = StudentCandidateQualification.objects.get(id=split_qualification_id)
            if a.application_id:
                std_application_id = a.application.student_application_id
                s.data[0]['Application_Id__c'] = std_application_id
                s.data[0]['Reference_Key__c'] = std_application_id + s.data[0]['Reference_Key__c']
                s.data[0]['attributes']['referenceId'] = std_application_id + s.data[0]['attributes']['referenceId']
            else:
                time.sleep(2)
                a = StudentCandidateQualification.objects.get(id=split_qualification_id)
                if a.application_id:
                    std_application_id = a.application.student_application_id
                    s.data[0]['Application_Id__c'] = std_application_id
                    s.data[0]['Reference_Key__c'] = std_application_id + s.data[0]['Reference_Key__c']
                    s.data[0]['attributes']['referenceId'] = std_application_id + s.data[0]['attributes']['referenceId']
                else:
                    time.sleep(1)
                    a = StudentCandidateQualification.objects.get(id=split_qualification_id)
                    if a.application_id:
                        std_application_id = a.application.student_application_id
                        s.data[0]['Application_Id__c'] = std_application_id
                        s.data[0]['Reference_Key__c'] = std_application_id + s.data[0]['Reference_Key__c']
                        s.data[0]['attributes']['referenceId'] = std_application_id + s.data[0]['attributes'][
                            'referenceId']

    data = {'records': s.data}
    ref_id = s.data[0]['attributes']['referenceId']

    log = log_model.objects.filter(reference_id=ref_id, status=str(status.HTTP_201_CREATED),
                                   is_inserted=True).last()
    if log:
        del data['records'][0]['attributes']['referenceId']
        data['records'][0]['id'] = log.response['model']['response']['results'][0]['id']
        return sf_api_call(sf_api_obj, data, ref_id, log_model, log_param)
    else:
        return sf_api_call(sf_api_obj, data, ref_id, log_model, log_param, is_inserted=True)