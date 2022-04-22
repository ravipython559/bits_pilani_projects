from celery import shared_task

@shared_task
def api_call(func, sf_api_obj, instance, serializer, log_model, log_param, serializer_fields):
	return func(sf_api_obj, instance, serializer, log_model, log_param, serializer_fields)