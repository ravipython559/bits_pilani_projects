from django.core.mail.backends.smtp import EmailBackend

class BitsEmailBackend(EmailBackend):
	def send_messages_bits(self, email_messages):
		"""
		Sends one or more EmailMessage objects and returns the number of email
		messages sent.
		"""
		if not email_messages:
			return
		with self._lock:
			new_conn_created = self.open()
			if not self.connection:
				# We failed silently on open().
				# Trying to send would be pointless.
				return
			emails_list = []
			for message in email_messages:
				sent = self._send(message)
				if sent:
					emails_list += message.to
			if new_conn_created:
				self.close()
		return emails_list
