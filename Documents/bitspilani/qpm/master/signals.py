from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, post_delete
from .models import *
from .tasks import *

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
		sync_qpm_data_to_ema.delay(payload)
	else:
		pre_save_instance = instance._pre_save_instance
		payload = {'exam_type':instance.exam_type, 'evaluation_type':instance.evaluation_type, 'pre_exam_type':pre_save_instance.exam_type, 'pre_evaluation_type':pre_save_instance.evaluation_type}
		sync_qpm_data_to_ema.delay(payload)

#delete code is commented because this delete will delete ema field child records also.So we hided delete sync code as of now.

# @receiver(post_delete, sender=ExamType)
# def delete_exam_type_profile(sender, instance, *args, **kwargs):
# 	payload = {'exam_type':instance.exam_type, 'evaluation_type':instance.evaluation_type}
# 	delete_sync_qpm_data_to_ema.delay(payload)

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
		sync_qpm_batch_data_to_ema.delay(payload)
	else:
		pre_save_instance = instance._pre_save_instance
		payload = {'batch_name':instance.batch_name, 'year':instance.year, 'sem_number':instance.sem_number, 'pre_batch_name':pre_save_instance.batch_name, 'pre_year':pre_save_instance.year, 'pre_sem_number':pre_save_instance.sem_number}
		sync_qpm_batch_data_to_ema.delay(payload)

# @receiver(post_delete, sender=Batch)
# def delete_batch_profile(sender, instance, *args, **kwargs):
# 	payload = {'batch_name':instance.batch_name}
# 	delete_sync_qpm_batch_data_to_ema.delay(payload)

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
		sync_qpm_semester_data_to_ema.delay(payload)
	else:
		pre_save_instance = instance._pre_save_instance
		payload = {'semester_name':instance.semester_name, 'pre_semester_name':pre_save_instance.semester_name}
		sync_qpm_semester_data_to_ema.delay(payload)

# @receiver(post_delete, sender=Semester)
# def delete_semester_profile(sender, instance, *args, **kwargs):
# 	payload = {'semester_name':instance.semester_name}
# 	delete_sync_qpm_semster_data_to_ema.delay(payload)

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
		sync_qpm_exam_slot_data_to_ema.delay(payload)
	else:
		pre_save_instance = instance._pre_save_instance
		payload = {'slot_name':instance.slot_name, 'slot_date':instance.slot_date, 'slot_day':instance.slot_day, 'slot_start_time':instance.slot_start_time, 'pre_slot_name':pre_save_instance.slot_name, 'pre_slot_date':pre_save_instance.slot_date, 'pre_slot_day':pre_save_instance.slot_day, 'pre_slot_start_time':pre_save_instance.slot_start_time}
		sync_qpm_exam_slot_data_to_ema.delay(payload)

# @receiver(post_delete, sender=ExamSlot)
# def delete_exam_slot_profile(sender, instance, *args, **kwargs):
# 	payload = {'slot_name':instance.slot_name}
# 	delete_sync_qpm_exam_slot_data_to_ema.delay(payload)
