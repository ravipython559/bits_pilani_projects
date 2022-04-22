

from master.models import *
from ema import default_settings as S



def run():
	default_slot, slot_c = ExamSlot.objects.get_or_create(slot_name=S.EXAM_SLOT_NAME, defaults=S.EXAM_SLOT_DEFAULT)
	print('ExamSlot:')
	print('Instance:', default_slot, 'Created:',slot_c)
	default_type, type_c = ExamType.objects.get_or_create(exam_type=S.EXAM_TYPE, defaults=S.EXAM_TYPE_DEFAULT)
	print('ExamType:')
	print('Instance:', default_type, 'Created:',type_c)
	default_semester, sem_c = Semester.objects.get_or_create(semester_name=S.SEMESTER_NAME, defaults=S.SEMESTER_DEFAULT)
	print('Semester:')
	print('Instance:', default_semester, 'Created:',sem_c)
	default_batch, batch_c = Batch.objects.get_or_create(batch_name=S.BATCH_NAME, defaults=S.BATCH_DEFAULT)
	print('Batch:')
	print('Instance:', default_batch, 'Created:',batch_c)
	default_loc, loc_c = Location.objects.get_or_create(location_name=S.LOCATION)
	print('Location')
	print('Instance:', default_loc, 'Created:',loc_c)
	S.EXAM_VENUE.update(location=Location.objects.get(location_name=S.LOCATION))
	default_venue, batch_venue = ExamVenue.objects.get_or_create(venue_short_name=S.VENUE_SHORT_NAME, defaults=S.EXAM_VENUE)
	print('Exam Venue:')
	print('Instance:', default_venue, 'Created:', batch_venue)
