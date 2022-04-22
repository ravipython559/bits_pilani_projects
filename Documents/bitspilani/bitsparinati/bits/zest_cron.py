import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bits.settings")
import django
django.setup()

from bits_rest.zest_utils import update_approved_emi
from bits_rest.models import ZestEmiTransaction
from bits_rest import zest_statuses as ZS 
from django.db.models.functions import *
from django.db.models import *

def cron_update_emi():
	emails = ZestEmiTransaction.objects.filter(
		Q(status__in=ZS.inprogress_status)|
		Q(status__isnull=True)
		).values_list('application__login_email__email', flat=True).distinct()
	for email in emails:
		update_approved_emi(email)