import requests
from django.conf import settings

AC_DOMAIN = settings.AC_DOMAIN
AC_API_URL = '{domain}/bits/api/v1/call/hall-ticket/{student_id}'

def authentication(user, authenticate=True):
	if authenticate:
		r = requests.post(
			AC_API_AUTH_URL.format(domain=AC_DOMAIN),
			data={'email':user.email}
		)
		r.raise_for_status()
		return r.json()
	else:
		return {'token': 'dummytoken12345byvishal'}


def get_headers():
	return {
		'Content-type': 'application/json',
		#'Authorization':'token %s' % (auth['token'],),
	}


def api_call_data(student_id, url):
	r = requests.get(
		url.format(
			domain=AC_DOMAIN,
			student_id = '2018MT50996', # Student Id is hardcoded for time being
		), 
		headers=get_headers(auth),
	)
	r.raise_for_status()
	return r.json()