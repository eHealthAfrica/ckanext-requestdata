import logging
import smtplib
import cgi
from socket import error as socket_error
from time import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from smtplib import SMTPRecipientsRefused
# from pylons import config
from email.header import Header
from email import Utils
import ckan
from ckan.common import config
from ckan.common import _
import paste.deploy.converters


log = logging.getLogger(__name__)


def send_email(content, to, subject, file=None):
    '''Sends email
       :param content: The body content for the mail.
       :type string:
       :param to: To whom will be mail sent
       :type string:
       :param subject: The subject of mail.
       :type string:


       :rtype: string

       '''
    mail_from = config.get('smtp.mail_from')
    msg = MIMEText(content.encode('utf-8'), 'plain', 'utf-8')
    subject = Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = _("%s <%s>") % ('Data Requests', mail_from)
    if isinstance(to, basestring):
        to = [to]
    msg['To'] = ','.join(to)
    msg['Date'] = Utils.formatdate(time())
    msg['X-Mailer'] = "CKAN %s" % ckan.__version__
    msg = MIMEMultipart()


    content = """\
        <html>
          <head></head>
          <body>
            <span>""" + content + """</span>
          </body>
        </html>
    """

    msg.attach(MIMEText(content, 'html', _charset='utf-8'))

    if isinstance(file, cgi.FieldStorage):
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(file.file.read())
        Encoders.encode_base64(part)

        extension = file.filename.split('.')[-1]

        header_value = 'attachment; filename=attachment.{0}'.format(extension)

        part.add_header('Content-Disposition', header_value)

        msg.attach(part)
    # Send the email using Python's smtplib.
    smtp_connection = smtplib.SMTP()

    smtp_server = config.get('smtp.server', 'localhost')
    smtp_starttls = paste.deploy.converters.asbool(
        config.get('smtp.starttls'))
    smtp_user = config.get('smtp.user')
    smtp_password = config.get('smtp.password')
    try:
        smtp_connection.connect(smtp_server)
    except socket.error, e:
        log.exception(e)
        raise MailerException('SMTP server could not be connected to: "%s" %s'
                              % (smtp_server, e))

    try:
        # Identify ourselves and prompt the server for supported features.
        smtp_connection.ehlo()

        # If 'smtp.starttls' is on in CKAN config, try to put the SMTP
        # connection into TLS mode.
        if smtp_starttls:
            if smtp_connection.has_extn('STARTTLS'):
                smtp_connection.starttls()
                # Re-identify ourselves over TLS connection.
                smtp_connection.ehlo()
            else:
                raise MailerException("SMTP server does not support STARTTLS")

        # If 'smtp.user' is in CKAN config, try to login to SMTP server.
        if smtp_user:
            assert smtp_password, ("If smtp.user is configured then "
                                   "smtp.password must be configured as well.")
            smtp_connection.login(smtp_user, smtp_password)

        smtp_connection.sendmail(mail_from, to, msg.as_string())
        log.info("Sent email to {0}".format(to))
        response_dict = {
            'success': True,
            'message': 'Email message was successfully sent.'
        }
        return response_dict
    except SMTPRecipientsRefused:
        error = {
            'success': False,
            'error': {
                'fields': {
                    'recepient': 'Invalid email recepient, maintainer not '
                    'found'
                }
            }
        }
        return error
    except smtplib.SMTPException, e:
        msg = '%r' % e
        log.exception(msg)
        raise MailerException(msg)
    except socket_error:
        log.critical('Could not connect to email server. Have you configured '
                     'the SMTP settings?')
        error_dict = {
            'success': False,
            'message': 'An error occured while sending the email. Try again.'
        }
        return error_dict
    finally:
        smtp_connection.quit()
        
