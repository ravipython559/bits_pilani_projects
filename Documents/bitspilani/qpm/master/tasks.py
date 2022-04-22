from celery import shared_task
import requests
from qpm.settings import *


@shared_task(time_limit=70000)
def sync_qpm_data_to_ema(payload):
	url = EMA_HOST_URL+'/administrator/views/sync-qpm-examtype/'
	a = requests.post(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def delete_sync_qpm_data_to_ema(payload):
	url = EMA_HOST_URL+'/administrator/views/sync-qpm-examtype/'
	a = requests.delete(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def sync_qpm_batch_data_to_ema(payload):
	url = EMA_HOST_URL+'/administrator/views/sync-qpm-batch/'
	a = requests.post(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def delete_sync_qpm_batch_data_to_ema(payload):
	url = EMA_HOST_URL+'/administrator/views/sync-qpm-batch/'
	a = requests.delete(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def sync_qpm_semester_data_to_ema(payload):
	url = EMA_HOST_URL+'/administrator/views/sync-qpm-semester/'
	a = requests.post(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def delete_sync_qpm_semster_data_to_ema(payload):
	url = EMA_HOST_URL+'/administrator/views/sync-qpm-semester/'
	a = requests.delete(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def sync_qpm_exam_slot_data_to_ema(payload):
	url = EMA_HOST_URL+'/administrator/views/sync-qpm-examslot/'
	a = requests.post(url, data=payload)
	return 'success'

@shared_task(time_limit=70000)
def delete_sync_qpm_exam_slot_data_to_ema(payload):
	url = EMA_HOST_URL+'/administrator/views/sync-qpm-examslot/'
	a = requests.delete(url, data=payload)
	return 'success'
