from django.utils import timezone

EXAM_SLOT_NAME = '-'
EXAM_SLOT_DEFAULT = {'slot_day':1, 'slot_date': timezone.now().date()}
EXAM_TYPE = '-'
EXAM_TYPE_DEFAULT = {'evaluation_type':'-'}
SEMESTER_NAME = '-'
SEMESTER_DEFAULT = {'taxila_sem_name':'-', 'canvas_sem_name':'-'}
BATCH_NAME = '-'
BATCH_DEFAULT = {'year':2019, 'sem_number':'-', 'application_center_batch':'-'}
VENUE_SHORT_NAME = '-'
EXAM_VENUE = {'venue_address':'default address', 'pin_code':'403234', 'student_count_limit':0}
LOCATION = '-'