from registrations.models import SaleForceAsyncTask
from registrations.tasks import api_call
from .api import saleforce_api as sf_api
from django.utils import timezone

def saleforce_async_api(sf_api_obj, instance, serializer, log_model, log_param, serializer_fields=None, seconds=5):
	job = api_call.apply_async(
		(sf_api, sf_api_obj, instance, serializer, log_model, log_param, serializer_fields),
		eta=timezone.localtime(timezone.now()) + timezone.timedelta(seconds=seconds)
		# queue='saleforce', #using default queue can change if you want
		# countdown=10 # not yet decided
	)
	SaleForceAsyncTask.objects.create(job=job.id, status=job.state, 
		model_type=log_model._meta.model.__name__,
		context={
			'sf_api_obj':sf_api_obj,
			'serializer_fields':serializer_fields,
			'log_param': {
				k: {'module':v.__module__, 'pk':v.pk, 'classname':v._meta.model.__name__} 
				for k, v in log_param.items()
			},
			'model':{
				'module':instance.__module__, 
				'pk':instance.pk, 
				'classname':instance._meta.model.__name__,
			},
			'serializer_model':{
				'module':serializer.__module__,  
				'classname':serializer.__name__,
			},
			'log_model':{
				'module':log_model.__module__,  
				'classname':log_model._meta.model.__name__,
			},

		}
	)