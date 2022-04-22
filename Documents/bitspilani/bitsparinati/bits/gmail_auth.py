from pydrive.auth import GoogleAuth
from apiclient.discovery import build

class MailAuth(GoogleAuth):
	def __init__(self,settings_file='gmail_settings.yaml',http_timeout=None):
		return super(MailAuth,self).__init__(settings_file=settings_file,http_timeout=http_timeout)

	def Authorize(self):
		super(MailAuth,self).Authorize()
		self.service = build('gmail', 'v1', http=self.http)