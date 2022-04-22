import os
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bits.settings")
#import django
#django.setup()
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def celery_beat_test():
    send_mail('celery beat test','celery beat test from amazon cloud','<'+settings.FROM_EMAIL+'>',
        ['vishal.kerkar@parinati.in','shrikant.pawar@parinati.in'], fail_silently=True)
    email = EmailMultiAlternatives('SUBJECT','msg','<{0}>'.format(settings.FROM_EMAIL),
        ['vishal.kerkar@parinati.in'],
        cc=['shrikant.pawar@parinati.in','gautam.gawas@parinati.in'])
    email.send()

if __name__ == '__main__':
    celery_beat_test()
