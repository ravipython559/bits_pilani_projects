import base64
from apiclient import errors
from email.MIMEText import MIMEText

from email.MIMEMultipart import MIMEMultipart

def send_message(service, user_id, message):
  try:
    
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print 'Message Id: %s' % message['id']
    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error


def create_message(sender, to, cc, subject, message_text):

    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(to)
    msg['Cc'] = ','.join(cc)
    msg.attach(MIMEText(message_text, 'plain'))
    raw = base64.urlsafe_b64encode(msg.as_string())
    raw = raw.decode()
    return {'raw': raw}



  #message = MIMEText(message_text)
  #message['to'] = to
  #message['from'] = sender
  #message['subject'] = subject
  #message['cc'] = cc
  #return {'raw': base64.urlsafe_b64encode(message.as_string())}
