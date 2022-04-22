#! /bin/bash

PROJ ='bits'
exec celery -A $PROJ worker -l info
