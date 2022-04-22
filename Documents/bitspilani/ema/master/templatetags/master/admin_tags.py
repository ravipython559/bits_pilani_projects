from django import template
from django.utils import timezone
from master.models import *
from ema.default_settings import * 


register = template.Library()

@register.inclusion_tag('admin/master/examvenueslotmap/non_added_field.html')
def non_field_display():
	evsm = ExamVenueSlotMap.objects.all() 
	ev = ExamVenue.objects.exclude(examvenueslotmap_ev__in=evsm).exclude(venue_short_name=VENUE_SHORT_NAME) 
	default_slot, slot_c = ExamSlot.objects.get_or_create(slot_name="-", 
		defaults={'slot_day':1, 'slot_date': timezone.now().date()})
	default_type, type_c = ExamType.objects.get_or_create(exam_type="-", 
		defaults={'evaluation_type':'-'})

	# vis=[ {'exam_venue':x, 'exam_slot':default_slot, 'exam_type':default_type} for x in ev ]

	return {
		'dummy_slot_list':[ {'exam_venue':x, 'exam_slot':default_slot, 'exam_type':default_type} for x in ev ]
	}