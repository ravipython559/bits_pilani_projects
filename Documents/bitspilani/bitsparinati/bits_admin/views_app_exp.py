from django.shortcuts import render, redirect
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from django_mysql.models import GroupConcat
from djqscsv import render_to_csv_response
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import Max, Value,Count,F,Q,CharField,Case,When,Sum,DateTimeField
from django.db.models.functions import Concat
from datetime import datetime as dt
from datetime import date, timedelta
from .models import *
from registrations.models import *
from .forms import *
from .task import *
from .bits_decorator import *
from django.views.decorators.cache import never_cache
from django.conf import settings
from import_export.tmp_storages import  MediaStorage as MS
from django.http import JsonResponse,HttpResponse, HttpResponseRedirect
from django.views.decorators.http import  require_GET
from celery.result import AsyncResult
from django.core.serializers.json import DjangoJSONEncoder
from table.views import FeedDataView
from .tables import *
from django.contrib.auth.decorators import login_required
import json
import datetime
import logging
import tablib
import operator
from django.utils import timezone
from bits_admin.dynamic_views import *
from bits_admin.tables_ajax import *
from bits_admin.csv_views import *
logger = logging.getLogger("main")

@method_decorator([staff_member_required,],name='dispatch')
class AEView(BaseAEView):
	token = ApplcantExceptionTable().token

@method_decorator([staff_member_required,],name='dispatch')
class ApplicationExceptionView(BaseApplicationExceptionView) :
	template_name = 'bits_admin/application_exception_table.html'