from django.core.urlresolvers import reverse_lazy
from bits.zest_settings import * 

ZEST_CLIENT_ID = r'460a4c5c-1bed-4818-8a44-95eed85309c7'
ZEST_CLIENT_SECRET = r'A7FE3z#Iv-8+53bkf(Ru'

try:
	from bits.local_settings import ZEST_CLIENT_ID, ZEST_CLIENT_SECRET
except:
	print("No zest settings found.")

home_url = lambda url: '{}{}'.format(BITS_DOMAIN, url)
ORDER_ID_FORMAT = 'ADHOC{seq}'

get_return_url = lambda :home_url(reverse_lazy('adhoc:zest-return-view'))
get_success_url = lambda :home_url(reverse_lazy('adhoc:zest-success-view'))
get_callback_url = lambda :home_url(reverse_lazy('adhoc:applicantData'))