from django import template
from registrations.models import Program

register = template.Library()

@register.filter(name='is_CIOT_prog')
def is_CIOT_prog(pg_code):
	return Program.objects.get(program_code = pg_code).program_code == 'CIOT'