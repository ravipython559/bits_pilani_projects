from django.core.urlresolvers import reverse_lazy

ZEST_GRANT_TYPE = 'client_credentials'
ZEST_SCOPE = 'merchant_api_sensitive'
ZEST_CLIENT_ID = r'7d9ba82e-4c4f-48c2-b1e1-ea0e1036000b'
ZEST_CLIENT_SECRET = r'YPVwwm]=)RST]@C}HfEQ'
ZEST_URL = 'https://app.zestmoney.in'
ZEST_AUTH_URL = 'https://authentication.zestmoney.in'
ZEST_MERCHANT_NAME = 'MerchantName'
ZEST_TO_MERCHANT = r'etgME)zg'
ZEST_PORTAL_LINK = r'https://app.zestmoney.in/authentication?isSignup=false'

BITS_DOMAIN = r'https://wilpadmissions.bits-pilani.ac.in'

get_url = lambda domain, url: '{0}{1}'.format(domain, url)
bits_url = lambda url: '{}{}'.format(BITS_DOMAIN, url)
try:
	from bits.local_settings import (ZEST_GRANT_TYPE, 
		ZEST_CLIENT_ID, ZEST_CLIENT_SECRET, 
		ZEST_SCOPE, ZEST_URL, ZEST_AUTH_URL, ZEST_MERCHANT_NAME, 
		ZEST_TO_MERCHANT, ZEST_PORTAL_LINK, BITS_DOMAIN)
except:
	print("No local zest settings found.")

ORDER_ID_FORMAT = '{year}ZEST{seq}'
CALLBACK_KEY_FORMAT = '{o_id}|{sec_key}|{status}'
PLAN_URL = get_url(ZEST_URL, '/Pricing/v2/quote/availableemiplans')
LOAN_CREATION_URL = get_url(ZEST_URL, '/ApplicationFlow/LoanApplications')
ORDER_STATUS_URL = get_url(ZEST_URL, '/ApplicationFlow/LoanApplications/orders/{orderId}')
LOAN_DELETE_URL = get_url(ZEST_URL, '/ApplicationFlow/LoanApplications/orders/{orderId}/cancellation')
DELIVERY_REPORT_URL = get_url(ZEST_URL, '/Loan/DeliveryReport/{orderId}')
AUTH_URL = get_url(ZEST_AUTH_URL, '/connect/token')


get_return_url = lambda :bits_url(reverse_lazy('bits_rest:zest-return-view'))
get_success_url = lambda :bits_url(reverse_lazy('bits_rest:zest-success-view'))
get_callback_url = lambda :bits_url(reverse_lazy('bits_rest:applicantData'))

