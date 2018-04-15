import smtplib
import threading
import logging
from email.mime.text import MIMEText
from email.header import Header

class Sender:
    def __init__(self, logger, server, username, password, from_):
        self.logger = logger
        self.server = server
        self.username = username
        self.password = password
        self.from_ = from_
        threading.Thread.__init__(self)

    def send(self, to, subject, message):
        self.logger.debug(f'Sending message now: {self.from_} => {to}: {subject}')
        # construct to, from, subject
        msg = MIMEText(message,'plain','utf-8')
        msg['From'] = Header(self.from_,'utf-8')
        msg['To'] = Header(to,'utf-8')
        msg['Subject'] = Header(subject,'utf-8')

        s = smtplib.SMTP_SSL(self.server)
        s.ehlo()
        s.login(self.username,self.password)
        s.sendmail(self.from_, to, msg.as_string())
        s.quit()

class SenderThread(threading.Thread):
    def __init__(self, name, logger, sender: Sender, to, subject, body):
        self.logger = logger
        self.sender = sender
        self.to = to
        self.subject = subject
        self.body = body
        threading.Thread.__init__(self, name=name)

    def run(self):
        self.sender.send(self.to, self.subject, self.body)

    def stop(self):
        self.sender.stop()
