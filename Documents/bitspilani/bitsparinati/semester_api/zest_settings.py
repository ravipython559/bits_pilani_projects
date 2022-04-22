from django.core.urlresolvers import reverse_lazy

ZEST_GRANT_TYPE = 'client_credentials'
ZEST_SCOPE = 'merchant_api_sensitive'
ZEST_CLIENT_ID = r'1595eba7-a942-4135-b752-5f7babab18dd'
ZEST_CLIENT_SECRET = r'U}+22Y673+oxQwZKc=ib'
HCL_ZEST_CLIENT_ID = r'1e7c132e-a8f5-4753-9116-a8781094f525'
HCL_ZEST_CLIENT_SECRET = r'kFdVwaBh9}i8d]irbAuR'
ZEST_URL = 'https://app.zestmoney.in'
ZEST_AUTH_URL = 'https://authentication.zestmoney.in'
ZEST_MERCHANT_NAME = 'MerchantName'
# ZEST_TO_MERCHANT = r'4rI0FU=r'
ZEST_TO_MERCHANT = r'etgME)zg'
ZEST_PORTAL_LINK = r'https://app.zestmoney.in/authentication?isSignup=false'
REG_RETURN_URL = 'http://wilpdar.bits-pilani.ac.in/registration/erp/reg_card.asp'
REG_SUCCESS_URL = 'http://wilpdar-aws.bits-pilani.ac.in/zest/doneurl.asp'
BITS_DOMAIN = r'https://wilpadmissions.bits-pilani.ac.in'

try:
	from semester_api.local_settings import (ZEST_GRANT_TYPE, 
		ZEST_CLIENT_ID, ZEST_CLIENT_SECRET, 
		ZEST_SCOPE, ZEST_URL, ZEST_AUTH_URL, ZEST_MERCHANT_NAME, 
		ZEST_TO_MERCHANT, ZEST_PORTAL_LINK, BITS_DOMAIN, REG_SUCCESS_URL,
		REG_RETURN_URL, HCL_ZEST_CLIENT_ID, HCL_ZEST_CLIENT_SECRET)
except:
	print("No local settings found. for semester api avoid for production purpose")

get_url = lambda domain, url: '{0}{1}'.format(domain, url)
home_url = lambda url: '{}{}'.format(BITS_DOMAIN, url)

ORDER_ID_FORMAT = 'ZEST{seq}'
CALLBACK_KEY_FORMAT = '{o_id}|{sec_key}|{status}'
PLAN_URL = get_url(ZEST_URL, '/Pricing/v2/quote/availableemiplans')
LOAN_CREATION_URL = get_url(ZEST_URL, '/ApplicationFlow/LoanApplications')
ORDER_STATUS_URL = get_url(ZEST_URL, '/ApplicationFlow/LoanApplications/orders/{orderId}')
DELIVERY_REPORT_URL = get_url(ZEST_URL, '/Loan/DeliveryReport/{orderId}')
AUTH_URL = get_url(ZEST_AUTH_URL, '/connect/token')
LOAN_DELETE_URL = get_url(ZEST_URL, '/ApplicationFlow/LoanApplications/orders/{orderId}/cancellation')

get_return_url = lambda :home_url(reverse_lazy('semester_api:zest-return-view'))
get_success_url = lambda :home_url(reverse_lazy('semester_api:zest-success-view'))
get_callback_url = lambda :home_url(reverse_lazy('semester_api:applicantData'))

