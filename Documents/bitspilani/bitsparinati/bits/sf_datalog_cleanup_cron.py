# from datetime import date, timedelta
# from registrations.models import SaleForce, SaleForceLeadDataLog, SaleForceQualificationDataLog, SaleForceWorkExperienceDataLog, SaleForceDocumentDataLog
# from django.db.models.functions import *
# from django.db.models import *


# def sf_data_log_cleanup_method():
# 	startdate = date.today()
# 	enddate = startdate + timedelta(days=-120)

# 	print("inside the function ",enddate)
# 	LDL = SaleForceLeadDataLog.objects.filter(created_on__lte=enddate)
# 	QDL = SaleForceQualificationDataLog.objects.filter(created_on__lte=enddate)
# 	EDL = SaleForceWorkExperienceDataLog.objects.filter(created_on__lte=enddate)
# 	DDL = SaleForceDocumentDataLog.objects.filter(created_on__lte=enddate)
# 	w=LDL.delete()
# 	x=QDL.delete()
# 	y=EDL.delete()
# 	z=DDL.delete()
# 	print("SaleForceLeadDataLog",w)
# 	print("SaleForceQualificationDataLog",x)
# 	print("SaleForceWorkExperienceDataLog",y)
# 	print("SaleForceDocumentDataLog",z)
