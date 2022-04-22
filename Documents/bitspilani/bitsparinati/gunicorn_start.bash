#! /bin/bash

NAME="bits"
DJANGODIR=/home/ubuntu/code/bitsparinati
SOCKFILE=/run/gunicorn/socket
PIDFILE=/run/gunicorn/pid
USER=ubuntu
GROUP=ubuntu
NUM_WORKERS=3
DJANGO_SETTINGS_MODULE=bits.settings
DJANGO_WSGI_MODULE=bits.wsgi
KEYFILE=/home/ubuntu/code/bitsparinati/ssl/bits-pilani.key
CERTIFICATE=/home/ubuntu/code/bitsparinati/ssl/bits-pilani.pem
FORWARD_IP="35.154.166.13,127.0.0.1"
echo "Starting $NAME as `whoami`"

cd $DJANGODIR
source /home/ubuntu/code/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR



exec gunicorn ${DJANGO_WSGI_MODULE}:application \
	--name $NAME \
        --workers $NUM_WORKERS \
        --pid $PIDFILE \
        --user=$USER --group=$GROUP \
        --bind=unix:$SOCKFILE \
#        --keyfile $KEYFILE \
#        --certfile $CERTIFICATE \
        --forwarded-allow-ips=$FORWARD_IP \
        --log-level=debug \
        --access-logfile /home/ubuntu/code/gunicorn-logs/bits-debug.txt \
        --error-logfile /home/ubuntu/code/gunicorn-logs/bits-error.txt \
        --log-file=-
        --check-config
