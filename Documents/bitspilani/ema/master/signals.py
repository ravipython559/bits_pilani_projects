from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from ema import default_settings as S
from django.dispatch import receiver
from master.models import *
from django.utils import timezone
from master.utils.extra_models.querysets import *
from .tasks import *

def hall_ticket_update_or_create(instance):
	current_exam = CurrentExam.objects.filter(
		program__program_code=instance.student.student_id[4:8], 
		semester=instance.semester, batch=instance.student.batch,
		is_active=True
		)

	for ce in current_exam.iterator():
		ces = get_instance_or_none(CourseExamShedule, course_code=instance.course_code,
			exam_type=ce.exam_type, semester=ce.semester, batch=ce.batch)#fix me
		if ces:
			ht_queryset = HallTicket.objects.filter(
					course__course_code=ces.course_code,
					student=instance.student, semester=ce.semester,
					is_cancel=False,
				)
			if not ht_queryset.exists():
				ht, created = HallTicket.objects.get_or_create(
					course=ces,
					student=instance.student,
					semester=ce.semester,
					exam_type=ce.exam_type,
					exam_slot__slot_name=S.EXAM_SLOT_NAME,
					exam_venue__venue_short_name=S.VENUE_SHORT_NAME,
					is_cancel=False,
					defaults={
						'exam_slot':ExamSlot.objects.get(slot_name=S.EXAM_SLOT_NAME),
						'exam_venue':ExamVenue.objects.get(venue_short_name=S.VENUE_SHORT_NAME),
					}
				)

@receiver(post_save, sender=CourseExamShedule)
def course_exam_schedule(sender, instance, created, **kwargs):

	evsm = ExamVenueSlotMap.objects.filter(
		exam_slot=instance.exam_slot,
		exam_type=instance.exam_type,
	)
	instance.exam_venue_slot_maps.set(evsm)

	# student_registration = StudentRegistration.objects.filter(course_code=instance.course_code)
	# for sr in student_registration.iterator():
	# 	hall_ticket_update_or_create(sr)


@receiver(post_save, sender=ExamVenueSlotMap)
def exam_venue_slot_map(sender, instance, created, **kwargs):

	ces = CourseExamShedule.objects.filter(
		exam_slot=instance.exam_slot,
		exam_type=instance.exam_type,
	)
	instance.course_exam_schedule.set(ces)


@receiver(pre_save, sender=ExamType)
def exam_type_pre_save(sender, instance, **kwargs):
    try:
        instance._pre_save_instance = ExamType.objects.get(pk=instance.pk)
    except ExamType.DoesNotExist:
        ExamType._pre_save_instance = instance

@receiver(post_save, sender=ExamType)
def save_exam_type_profile(sender, instance, created, **kwargs):
	if created:
		payload = {'exam_type':instance.exam_type, 'evaluation_type':instance.evaluation_type}
		sync_ema_data_to_qpm.delay(payload)
	else:
		pre_save_instance = instance._pre_save_instance
		payload = {'exam_type':instance.exam_type, 'evaluation_type':instance.evaluation_type, 'pre_exam_type':pre_save_instance.exam_type, 'pre_evaluation_type':pre_save_instance.evaluation_type}
		sync_ema_data_to_qpm.delay(payload)

#delete code is commented because this delete will delete ema field child records also.So we hided delete sync code as of now.

# @receiver(post_delete, sender=ExamType)
# def delete_exam_type_profile(sender, instance, *args, **kwargs):
# 	payload = {'exam_type':instance.exam_type, 'evaluation_type':instance.evaluation_type}
# 	delete_sync_ema_data_to_qpm.delay(payload)

@receiver(pre_save, sender=Batch)
def batch_pre_save(sender, instance, **kwargs):
    try:
        instance._pre_save_instance = Batch.objects.get(pk=instance.pk)
    except Batch.DoesNotExist:
        Batch._pre_save_instance = instance

@receiver(post_save, sender=Batch)
def save_batch_profile(sender, instance, created, **kwargs):
	if created:
		payload = {'batch_name':instance.batch_name, 'year':instance.year, 'sem_number':instance.sem_number}
		sync_ema_batch_data_to_qpm.delay(payload)
	else:
		pre_save_instance = instance._pre_save_instance
		payload = {'batch_name':instance.batch_name, 'year':instance.year, 'sem_number':instance.sem_number, 'pre_batch_name':pre_save_instance.batch_name, 'pre_year':pre_save_instance.year, 'pre_sem_number':pre_save_instance.sem_number}
		sync_ema_batch_data_to_qpm.delay(payload)

# @receiver(post_delete, sender=Batch)
# def delete_batch_profile(sender, instance, *args, **kwargs):
# 	payload = {'batch_name':instance.batch_name}
# 	delete_sync_ema_batch_data_to_qpm.delay(payload)

@receiver(pre_save, sender=Semester)
def semster_pre_save(sender, instance, **kwargs):
    try:
        instance._pre_save_instance = Semester.objects.get(pk=instance.pk)
    except Semester.DoesNotExist:
        Semester._pre_save_instance = instance

@receiver(post_save, sender=Semester)
def save_semester_profile(sender, instance, created, **kwargs):
	if created:
		payload = {'semester_name':instance.semester_name}
		sync_ema_semester_data_to_qpm.delay(payload)
	else:
		pre_save_instance = instance._pre_save_instance
		payload = {'semester_name':instance.semester_name, 'pre_semester_name':pre_save_instance.semester_name}
		sync_ema_semester_data_to_qpm.delay(payload)

# @receiver(post_delete, sender=Semester)
# def delete_semester_profile(sender, instance, *args, **kwargs):
# 	payload = {'semester_name':instance.semester_name}
# 	delete_sync_ema_semster_data_to_qpm.delay(payload)

@receiver(pre_save, sender=ExamSlot)
def exam_slot_pre_save(sender, instance, **kwargs):
    try:
        instance._pre_save_instance = ExamSlot.objects.get(pk=instance.pk)
    except ExamSlot.DoesNotExist:
        ExamSlot._pre_save_instance = instance

@receiver(post_save, sender=ExamSlot)
def save_exam_slot_profile(sender, instance, created, **kwargs):
	if created:
		payload = {'slot_name':instance.slot_name, 'slot_date':instance.slot_date, 'slot_day':instance.slot_day, 'slot_start_time':instance.slot_start_time}
		sync_ema_exam_slot_data_to_qpm.delay(payload)
	else:
		pre_save_instance = instance._pre_save_instance
		payload = {'slot_name':instance.slot_name, 'slot_date':instance.slot_date, 'slot_day':instance.slot_day, 'slot_start_time':instance.slot_start_time, 'pre_slot_name':pre_save_instance.slot_name, 'pre_slot_date':pre_save_instance.slot_date, 'pre_slot_day':pre_save_instance.slot_day, 'pre_slot_start_time':pre_save_instance.slot_start_time}
		sync_ema_exam_slot_data_to_qpm.delay(payload)

# @receiver(post_delete, sender=ExamSlot)
# def delete_exam_slot_profile(sender, instance, *args, **kwargs):
# 	payload = {'slot_name':instance.slot_name}
# 	delete_sync_ema_exam_slot_data_to_qpm.delay(payload)


# @receiver(post_save, sender=StudentRegistration)
# def student_registrations(sender, instance, created, **kwargs):
# 	hall_ticket_update_or_create(instance)

# @receiver(post_save, sender=CurrentExam)
# def update_of_ce(sender, instance, created, **kwargs):
# 	if instance.is_active:
# 		sr_queryset = StudentRegistration.objects.annotate(pg_code=Substr('student__student_id', 5, 4),)
# 		sr_queryset = sr_queryset.filter(
# 			pg_code=instance.program.program_code,
# 			semester=instance.semester,
# 			student__batch=instance.batch,
# 			)

# 		ces_queryset = CourseExamShedule.objects.filter(
# 			course_code__in=Subquery(sr_queryset.values('course_code')),
# 			exam_type=instance.exam_type,
# 			semester=instance.semester,
# 			batch=instance.batch,
# 		)

# 		for ces in ces_queryset.iterator():
# 			for sr in sr_queryset.filter(student__batch=instance.batch, course_code=ces.course_code).iterator():
# 				ht_queryset = HallTicket.objects.filter(
# 					course__course_code=ces.course_code, 
# 					student=sr.student, semester=instance.semester,
# 					is_cancel=False,
# 				)
# 				if not ht_queryset.exists():
# 					ht, created = HallTicket.objects.get_or_create(
# 						course__course_code=ces.course_code, 
# 						student=sr.student,
# 						semester=instance.semester,
# 						exam_type=instance.exam_type,
# 						exam_slot__slot_name=S.EXAM_SLOT_NAME,
# 						exam_venue__venue_short_name=S.VENUE_SHORT_NAME,
# 						is_cancel=False,
# 						defaults={
# 							'course':ces,
# 							'exam_slot':ExamSlot.objects.get(slot_name=S.EXAM_SLOT_NAME),
# 							'exam_venue':ExamVenue.objects.get(venue_short_name=S.VENUE_SHORT_NAME),
# 						}
# 					)
