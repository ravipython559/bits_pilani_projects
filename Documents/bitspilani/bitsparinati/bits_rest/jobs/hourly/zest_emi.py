from django_extensions.management.jobs import HourlyJob
from django.db.models import Q
from bits_rest.models import ZestEmiTransaction
from bits_rest.zest_utils import update_approved_emi
from bits_rest import zest_statuses as ZS
from django.core.mail import send_mail
from django.conf import settings

class Job(HourlyJob):
	help = "emi transaction"

	def execute(self):
		zest = ZestEmiTransaction.objects.filter(Q(status__in=ZS.inprogress_status)|Q(status__isnull=True))
		emails = zest.values_list('application__login_email__email', flat=True).distinct()
		try:
			for email in emails.iterator():update_approved_emi(email)
		except Exception as e:
			send_mail("Zest Emi Update Error",e,'<'+settings.FROM_EMAIL+'>',
				['narayan.desai@parinati.in'], fail_silently=True)
		