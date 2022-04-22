"""
WSGI config for bits project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bits.settings")
# from django.conf import settings
# settings.configure()
os.environ['HTTPS'] = "on"
os.environ['wsgi.url_scheme'] = 'https'
os.environ['RDS_DB_NAME'] = 'bitsdb'
os.environ['RDS_USERNAME'] = 'root'
os.environ['RDS_PASSWORD'] = r'b!t$Db2017rd$'
os.environ['RDS_HOSTNAME'] = 'bitsdbmumbai.cosqzd7ygxjn.ap-south-1.rds.amazonaws.com'
os.environ['RDS_PORT'] = '3306'

application = get_wsgi_application()


# def application(environ, start_response):
#     if environ['mod_wsgi.process_group'] != '': 
#         import signal
#         os.kill(os.getpid(), signal.SIGINT)
#     return ["killed"]


# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "abcde.settings")

# application = get_wsgi_application()


# def application(environ, start_response):
#     if environ['mod_wsgi.process_group'] != '': 
#         import signal
#         os.kill(os.getpid(), signal.SIGINT)
#     return ["killed"]