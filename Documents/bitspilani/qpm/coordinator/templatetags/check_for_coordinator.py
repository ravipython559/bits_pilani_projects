from django import template
from master.models import *
from django.db.models import Q
from table.utils import A, mark_safe
from django.utils.html import escape


register = template.Library()

@register.simple_tag
def check_coordinator_assigned_as_faculty(email):
	coordi = QpSubmission.objects.filter(Q(faculty_email_id=email)|
										Q(email_access_id_1=email)|
										Q(email_access_id_2=email)).exists()

	if coordi:
		return mark_safe("""<li>
								<a href="/coordinator/home"role="button" aria-haspopup="true" aria-expanded="false">Upload Question Paper</a>
							</li>
							<li>
								<a href="/coordinator/QP-submission-status/" role="button" >View QP Submission Status</a>
							</li>""")
	else:
		return ''
