from django import template
from registrations.models import *
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
import datetime
from dateutil.relativedelta import relativedelta
register = template.Library()


@register.filter(name='is_offer_letter')
def is_offer_letter(pk):
	sca = StudentCandidateApplication.objects.get(pk=pk)
	if sca.application_status in [settings.APP_STATUS[9][0],settings.APP_STATUS[11][0]]:
		return True

	else:return False