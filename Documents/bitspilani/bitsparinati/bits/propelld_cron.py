from datetime import date, timedelta
from adhoc.models import AdhocPropelldApplication
from bits_rest.models import PropelldApplication
from django.db.models.functions import *
from django.db.models import *


startdate = date.today()
enddate = startdate + timedelta(days=-7)

def change_status_adhoc():
	NLA = AdhocPropelldApplication.objects.filter(status = 'New Loan Application',created_on__lte=enddate)

	for user in NLA:
		user.status = 'DROPPED'
		user.save()

def change_status():
	NLA = PropelldApplication.objects.filter(status = 'New Loan Application',created_on__lte=enddate)

	for user in NLA:
		user.status = 'DROPPED'
		user.save()	