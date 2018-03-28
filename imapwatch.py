#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import smtplib, imaplib, urllib, threading, email, os, sys, yaml
from email.header import Header, decode_header
from email.MIMEText import MIMEText
from email.Utils import parseaddr

config = yaml.load(open('./imapwatch.yml','r'))
mailboxes = config['imap']['mailboxes'] 
threads = []

def idle(connection):
    tag = connection._new_tag()
    connection.send("%s IDLE\r\n" % tag)
    response = connection.readline()
    connection.loop = True
    if response == '+ idling\r\n':
        while connection.loop:
            resp = connection.readline()
            uid, message = resp[2:-2].split(' ',1)
            yield uid, message
    else:
        raise Exception("IDLE not handled? : %s" % response)

def done(connection):
    connection.send("DONE\r\n")
    connection.loop = False

def watch(mailbox):
    m = imaplib.IMAP4_SSL(config['imap']['server'])
    m.login(config['imap']['username'], config['imap']['password'])
    m.select(mailbox)
    for uid, msg in m.idle():
        if config['imap']['monitor'] in msg:
            #print mailbox + " " + uid
            print fetch(uid, mailbox)
    return

def fetch(num, mailbox):
    m = imaplib.IMAP4_SSL(config['imap']['server'])
    m.login(config['imap']['username'], config['imap']['password'])
    m.select(mailbox)
    data = m.fetch(num, '(RFC822)')
    message = email.message_from_string(data[1][0][1])
    header_msgid = decode_header(message.get('Message-Id'))[0][0]
    header_from = decode_header(message.get('From'))[0][0]
    header_subject = decode_header(message.get('Subject'))[0][0]
    msg_body = body(message)

    output  = "Message-Id: " + header_msgid + "\n"
    output += "From: " + header_from + "\n"
    output += "Subject: " + header_subject + "\n\n"

    send(header_subject, header_from, header_msgid, msg_body)

    m.close()
    m.logout()
    return output

import email

def body(msg):
    """ Decode email body.
    Detect character set if the header is not set.
    We try to get text/plain, but if there is not one then fallback to text/html.
    :param message_body: Raw 7-bit message body input e.g. from imaplib. Double encoded in quoted-printable and latin-1
    :return: Message body as unicode string
    """

    text = ""
    if msg.is_multipart():
        html = None
        for part in msg.walk():
            #print "%s, %s" % (part.get_content_type(), part.get_content_charset())
	
            if part.get_content_charset() is None:
                # We cannot know the character set, so return decoded "something"
                text = part.get_payload(decode=True)
                continue

            charset = part.get_content_charset()

            if part.get_content_type() == 'text/plain':
                text = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

            if part.get_content_type() == 'text/html':
                html = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

        if text is not None:
            return text.strip()
        else:
            return html.strip()
    else:
        text = unicode(msg.get_payload(decode=True), msg.get_content_charset(), 'ignore').encode('utf8', 'replace')
        return text.strip()


def send(header_subject, header_from, header_msgid, body):
    send_from = config['smtp']['from']
    send_to = config['smtp']['to']

    sender_name, sender_address = parseaddr(header_from)
    if sender_name == "":
        sender_name = sender_address
    sender_name = str(Header(unicode(sender_name),  'ISO-8859-1'))
   
   
    #msg = MIMEText(header_from+": \""+header_subject+"\"\n"+"message:"+urrllib.urlencode(msgid)+"\n\n"+body)
    body = u'\u2709\ufe0f'+" "+sender_name+": \""+header_subject+"\"\n"+"message:"+urllib.quote_plus(header_msgid)
    msg = MIMEText(body.encode('UTF-8'),'plain','UTF-8')
    msg['To'] = send_to
    msg['From'] = str(Header(unicode(header_from), 'ISO-8859-1'))
    msg['Subject'] = str(Header(unicode(header_subject), 'ISO-8859-1'))
    s = smtplib.SMTP_SSL(config['smtp']['server'])
    s.ehlo()
    s.login(config['smtp']['user'],config['smtp']['password'])
    s.sendmail(send_from, send_to, msg.as_string())
    s.quit()
 
imaplib.IMAP4.idle = idle
imaplib.IMAP4.done = done

for mailbox in mailboxes:
    t = threading.Thread(name=mailbox, target=watch, args=(mailbox,))
    threads.append(t)
    t.start()
