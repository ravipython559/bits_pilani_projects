import datetime
from registrations.models import *
from django.db.models import Max
from django.conf import settings



'''
 data=[]



 tmp = {
	'date': datetime.datetime.strptime('12/03/2016 14:29:47',
	 '%m/%d/%Y %H:%M:%S'),
	'payment_id':'C1381T4a1b26cdccea46d2b63bb57c3d60b2b8',
	'payment_amount': '55750',
	'payment_bank':'1060',
	'fee_type':'1',
	'transaction_id':'275667366',
	'student_application_id':'AHT741381',
 } 





 data.append(tmp)
'''

def vish(x):
	dt = x['date']
	s=StudentCandidateApplication.objects.get(
		student_application_id=x['student_application_id'])
	v=ApplicationPayment(application=s,
	payment_id=x['payment_id'],
	payment_amount=x['payment_amount'],payment_date=dt,
	payment_bank=x['payment_bank'],
	transaction_id=x['transaction_id'],
	fee_type=x['fee_type'])
	print 'application_status',s.application_status
	s.application_status = settings.APP_STATUS[11][0]
	v.save()
	s.save()

	pfa = PROGRAM_FEES_ADMISSION.objects.get(program=s.program,
									fee_type = '1',
									latest_fee_amount_flag=True)
	cs = CandidateSelection.objects.get(application = s,
									application__admit_year=pfa.admit_year,
									application__program = pfa.program)
	max_id = CandidateSelection.objects.filter(application__admit_year=pfa.admit_year,
									application__program = pfa.program).exclude(
									student_id__isnull =True).aggregate(Max('student_id'))


	print 'student_application_id',x['student_application_id']
	print 'payment_id',x['payment_id']
	print 'payment_amount',x['payment_amount']
	print 'payment_bank',x['payment_bank']
	print 'transaction_id',x['transaction_id']
	print 'fee_type',x['fee_type']
	print 'max_id',max_id

	if not max_id['student_id__max']:
		student_id = '{0}{1}{2:03d}'.format(pfa.admit_year,
			pfa.program.program_code,1)
	else:
		student_id = '{0}{1}{2:03d}'.format(pfa.admit_year,
			pfa.program.program_code,
			int(max_id['student_id__max'][-3:])+1)

	if cs.student_id :student_id = cs.student_id
	cs.student_id = student_id
	cs.save()
        print 'student_id',cs.student_id



def func1(data):
	for x in data:
		s=StudentCandidateApplication.objects.get(student_application_id=x['student_application_id'])
		print s.student_application_id, s.application_status
	


def app_fee(x):
	dt = x['date']
	s=StudentCandidateApplication.objects.get(
		student_application_id=x['student_application_id'])
	v=ApplicationPayment(application=s,
	payment_id=x['payment_id'],
	payment_amount=x['payment_amount'],payment_date=dt,
	payment_bank=x['payment_bank'],
	transaction_id=x['transaction_id'],
	fee_type=x['fee_type'])
	print 'application_status',s.application_status
	print 'full_name', s.full_name
	s.application_status = settings.APP_STATUS[13][0]
	v.save()
	s.save()


