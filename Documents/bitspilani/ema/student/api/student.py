import requests
import base64
from django.conf import settings
from django.core.files import File
from master.utils.extra_models.querysets import get_instance_or_none
from master.models import Student
import io
import os
import json

def student_photo_api(student_id):
	student = get_instance_or_none(Student, **{"student_id":student_id})
	if student:
		try:
			req = requests.get('%s/bits/api/v1/call/hall-ticket/%s/' %(settings.AC_DOMAIN, student_id), verify=False)
			req.raise_for_status()
			data = req.json() 

			for app in data['ad_arch'] + data['ad'] + data['historical_data']:
				if app['applicant_photo']:
					photo_file = io.BytesIO(bytes(base64.b64decode(app['applicant_photo'])))
					student.photo = File(photo_file, name='%s%s' %(student_id, os.path.splitext(app['file_name'])[-1]))
					student.save()
		except Exception as e:
			pass


def get_sdms_student_details(stud_email):
	try:
		headers = {
			'Content-type': 'application/json',
			settings.SDMS_API_AUTHHEADER : settings.SDMS_API_AUTHKEY ,
		}
		params = {"student_id":"{}".format(stud_email).lower()}
		response = requests.get(settings.SDMS_API_URL, params=params, headers=headers)
		response.raise_for_status()
		return response.json()
	except Exception as e:
		pass