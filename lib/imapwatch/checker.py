#/usr/bin/env python3
import datetime
import imaplib
import socket
import ssl
import threading
import time
import imapclient
import imapclient.exceptions
import email
from email.header import decode_header
from urllib.parse import quote_plus
from .sender import Sender, SenderThread

class Checker:
    def __init__(self, logger, stop_event, server_address: str, username, password, mailbox, check_for, action, sender, use_ssl=True, timeout=10):
        self.server, self.ssl_context, = None, None
        self.logger = logger
        self.stop_event = stop_event
        self.server_address = server_address
        self.username = username
        self.password = password
        self.timeout = timeout
        self.mailbox = mailbox
        self.check_for = check_for
        self.action = action
        self.sender = sender
        if use_ssl:
            self.ssl_context = ssl.create_default_context()
        self.last_sync = datetime.datetime.now()

    def connect(self):
        self.server = imapclient.IMAPClient(self.server_address, ssl_context=self.ssl_context, use_uid=False)
        self.server.login(self.username, self.password)
        self.server.select_folder(self.mailbox)
        self.logger.info(f"Connected to mailbox {self.mailbox}")

    def timestamps_difference(self, timestamp):
        delta = timestamp - self.last_sync
        return delta.days * 24*60 + (delta.seconds + delta.microseconds / 10e6) / 60

    def check_messages(self, responses):
        messages = []
        if 'flagged' in self.check_for:
            messages += [ r[0] for r in responses if len(r) > 2 and b'FLAGS' in r[2] and len(r[2]) > 1 and b'\\Flagged' in r[2][1] ]
        if 'new' in self.check_for:
            messages += [ r[0] for r in responses if len(r) > 1 and b'EXISTS' in r[1] ]
        return messages 

    def decode_header(self, header):
        h = email.header.decode_header(header.decode())
        self.logger.debug(f"h: {h}")
        #elements = [ i[0].decode(i[1]) if i[1] else i[0] for i in h ]
        elements = []
        for i in h:
            if i[1]:
                elements.append(i[0].decode(i[1]))
            else:
                try:
                    elements.append(i[0].decode())
                except AttributeError:
                    elements.append(i[0])
        # TODO should we join with a space or no space?
        return ''.join(elements)

    def fetch_messages(self, messages):
        items = []
        for fetch_id, data in self.server.fetch(messages, ['ENVELOPE']).items():
            envelope = data[b'ENVELOPE']
            message_id = envelope.message_id.decode()
            subject = self.decode_header(envelope.subject).strip()
            if envelope.from_[0].name:
                from_ = self.decode_header(envelope.from_[0].name).strip()
            else:
                from_ = (envelope.from_[0].mailbox + b'@' +  envelope.from_[0].host).decode()
            items.append({ 
                'from_': from_,
                'subject': subject,
                'message_id': message_id
            })
            self.logger.info(f'Flagged item: {from_} / {subject}')

        return items

    def dispatch(self, items):
        if self.action['action'] == 'things':
            body = '\n'.join([ f'\u2709\ufe0f {i["from_"]}: "{i["subject"]}"\nmessage:{quote_plus(i["message_id"])}' for i in items ])
            subject = items[0]['subject']
       
        # TODO: create this action
        elif self.action['action'] == 'resend':
            body = "Test resend"
            subject = items[0]['subject']
        
        SenderThread('Sender', self.logger, self.sender, self.action['email'], subject, body).start()
    
    def idle_loop(self):
        self.server.idle()
        while not self.stop_event.is_set():
            try:
                current_sync = datetime.datetime.now()
                # timeout defines how long we should wait until we get a response
                # if we wait a bit longer we can get all the response to an IDLE call
                # (not just the first one)
                #
                # also: when stopping a thread, it waits until this loop has finished.
                # we can set this smaller to quit quicker, but not too small (as we won't have
                # enought time to catch multiple messages
                responses = self.server.idle_check(timeout=3)
                if isinstance(responses, list) and len(responses) > 0:
                    messages = self.check_messages(responses)
                    if messages:
                        self.server.idle_done()
                        items = self.fetch_messages(messages)
                        self.dispatch(items)
                        self.server.noop()
                        self.server.idle()
                        # if we restart idle() we can also restart the timer (we need to only
                        # check for non-activity, so we're good now for another {timeout} minutes
                        self.last_sync = current_sync
                if self.timestamps_difference(current_sync) > self.timeout:  # renew idle command every 10 minutes
                    self.logger.debug(f"Refresing IDLE timeout")
                    self.server.idle_done()
                    self.server.noop()
                    self.server.idle()
                    self.last_sync = current_sync
            except (imapclient.exceptions.IMAPClientError, imapclient.exceptions.IMAPClientAbortError,
                    imaplib.IMAP4.error, imaplib.IMAP4.abort, socket.error, socket.timeout, ssl.SSLError,
                    ssl.SSLEOFError) as exception:
                self.logger.critical(f"Checker: Got exception @ {self.mailbox}: {exception}")
                self.logger.inf(f"Reconnecting...")
                self.connect()
                self.idle_loop()
        
        self.server.idle_done()
        # TODO how should we close the server connection?
        self.server.logout()

    def stop(self):
        self.stop_event.set()

class CheckerThread(threading.Thread):
    def __init__(self, logger, checker: Checker):
        self.logger = logger
        self.checker = checker
        threading.Thread.__init__(self, name=checker.mailbox)

    def run(self):
        self.checker.connect()
        self.checker.idle_loop()

    def stop(self):
        self.checker.stop()
