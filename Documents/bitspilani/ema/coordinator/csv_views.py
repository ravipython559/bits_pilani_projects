from csv_export.views import CSVExportView
from master.models import StudentRegistration
from .permissions import *
from master.csv_views import BaseStudentRegExportCSV

class StudentRegExportCSV(EMAUserPermissionMixin,BaseStudentRegExportCSV):
	pass