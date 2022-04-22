from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from .google_drive import db_bkup
from .bits_mail import *
from .celery_beat_test import *
from .s3_backup import s3_bucket_backup
from .specific_data_summary import specific_summary_table_population
from .zest_cron import cron_update_emi
from .propelld_cron import change_status_adhoc , change_status
# from .sf_datalog_cleanup_cron import sf_data_log_cleanup_method

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bits.local_settings')

app = Celery('bits')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    # sender.add_periodic_task(
    #     crontab(hour=6,minute = 0,),
    #     sf_data_log_cleanup.s(),
    # )
    sender.add_periodic_task(
        crontab(hour=8,minute=0),
        specific_table_population.s(),
    )

    sender.add_periodic_task(
        crontab(hour='0,12',minute=10,),
        #crontab(hour=19,minute = 42,),
        db_backup_task.s(),
    )

    sender.add_periodic_task(
        crontab(hour=10,minute=16,day_of_week='mon,fri'),
        #crontab(),
        send_bits_mail_task.s(),
    )

    sender.add_periodic_task(
	crontab(hour=10,minute=15,day_of_week='sat'),
	#crontab(),
	send_app_fee_mails_task.s(),
    )

    sender.add_periodic_task(
        crontab(hour=10,minute=15,day_of_week='sat'),
        #crontab(),
        debug_task1.s(),

    )

    sender.add_periodic_task(
        # crontab(hour=0,minute=40),
        crontab(hour='0,12',minute=30,),
        s3_backup_task.s(),
    )


    sender.add_periodic_task(
        crontab(hour='*/1',minute=0),
        cron_update_emi.s(),
    )


    sender.add_periodic_task(
        crontab(hour='0,12',minute=35,),
        change_status_adhoc.s(),
    )

    sender.add_periodic_task(
        crontab(hour='0,12',minute=20,),
        change_status.s(),
    )

@app.task
def db_backup_task():
    print "db backup"
    #db_bkup()

@app.task
def send_bits_mail_task():
    print "send mail"
    #send_mails()

@app.task
def send_app_fee_mails_task():
    print "###### send_app_fee_mails ######"
    #send_app_fee_mails()

@app.task
def s3_backup_task():
    print "###### s3_backup_task ######"
    main_bucket = r'bits-application-files'
    backup_bucket = r'ac-backup-bucket'
    region = r'ap-south-1'
    s3_bucket_backup(main_bucket, backup_bucket, region)

@app.task
def emi_status_update_task():
    print "emi updation"
    cron_update_emi()

@app.task
def debug_task1():
    print "test beat"
    celery_beat_test()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task
def change_status_update_task():
    print "Propelld Adhoc status updation"
    change_status_adhoc()

@app.task
def change_status_update():
    print "Propelld  status updation"
    change_status()

@app.task
def specific_table_population():
    print "Populating Table"
    specific_summary_table_population()

# @app.task
# def sf_data_log_cleanup():
#     print "SF data log  status updation"
#     sf_data_log_cleanup_method()