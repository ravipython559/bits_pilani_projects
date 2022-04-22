from registrations.models import *

def specific_pg(email):
	try:
		pg = ProgramDomainMapping.objects.filter(email = email)
	except ProgramDomainMapping.DoesNotExist:
		pg = ProgramDomainMapping.objects.filter(email_domain__iexact = email.split('@')[1])
	return pg
