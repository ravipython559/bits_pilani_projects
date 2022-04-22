from django.apps import AppConfig


class MasterConfig(AppConfig):
    name = 'master'

    def ready(self):
    	import master.signals