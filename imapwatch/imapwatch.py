#!/usr/bin/env python3.6
import time
import logging
import yaml
import threading
import daemon
import sys
import os
import signal
from logging.handlers import RotatingFileHandler
from .sender import Sender
from .checker import Checker, CheckerThread
from .loggingdaemoncontext import LoggingDaemonContext

class IMAPWatch:
    def __init__(self, verbose = None):
        self.verbose = verbose
        self.stop_event = threading.Event()
        self.threads = []

        self.config = yaml.load(open('./imapwatch.yml','r'))
        if not self.config:
            raise SystemExit("No config file found. Exiting.")

        self.setupLogging()

    def start(self):
        # read configuration

        sender = Sender(self.logger, self.config['smtp']['server'], self.config['smtp']['username'], self.config['smtp']['password'], self.config['smtp']['from'])

        self.logger.debug("Setting up accounts")
        for account in self.config['accounts']:
            mailboxes = account['mailboxes']
            for mailbox in mailboxes:
                action = [ a for a in self.config['actions'] if a['action'] == mailbox['action'] ][0]  
                checker = Checker(self.logger, self.stop_event, account['server'], account['username'], account['password'], mailbox['mailbox'], mailbox['check_for'], action, sender, bool(account['use_ssl']), int(account['timeout']))
                CheckerThread(self.logger, checker).start()
                self.threads.append(checker)
      
        while True:
            time.sleep(1)

    def setupLogging(self):

        # configure logging
        logFormatter = logging.Formatter('%(name)-10.10s %(asctime)s [%(process)d %(threadName)-11.11s] [%(levelname)-8.8s] %(message)s')
        self.logger = logging.getLogger('imapwatch')
        # this shouldn't be necessary? level should be NOTSET standard
        # https://docs.python.org/3/library/logging.html
        self.logger.setLevel(logging.DEBUG)

        # create the filehandler 
        self.fileHandler = RotatingFileHandler(
            './log/imapwatch.log',
            mode='a',
            maxBytes=1048576,
            backupCount=9,
            encoding='UTF-8',
            # if we don't set delay to False, the stream is not opened until we start writing
            # this prevents getLogFileHandler() to find the right handle to preserve
            delay=False
            )
        self.fileHandler.name = "File Logger"
        self.fileHandler.formatter = logFormatter
        self.logger.addHandler(self.fileHandler)
        
        # get the (already existing) imapclient logger 
        self.imapclient_logger = logging.getLogger('imapclient')
        self.imapclient_logger.addHandler(self.fileHandler)

        # Add optional ConsoleHandler
        if self.verbose:
            consoleHandler = logging.StreamHandler()
            consoleHandler.name = "Console Logger"
            consoleHandler.formatter = logFormatter

            self.logger.setLevel(self.verbose)
            self.logger.addHandler(consoleHandler)
            
            # TODO: add custom level for imapclient logging on the console
            self.imapclient_logger.addHandler(consoleHandler)

    def getLogFileHandles(self, l):
        handles = []
        for handler in l.handlers:
            if isinstance(handler, (logging.FileHandler, RotatingFileHandler)):
                handles.append(handler.stream.fileno())
        if l.parent:
            handles += self.getLogFileHandles(l.parent)
        return handles

    def stop(self, signum, frame):
        self.logger.debug('Stopping')
        self.stop_event.set()
        map(self.stop, self.threads)
        map(threading.Thread.join, self.threads)
        raise SystemExit("Exited")

class IMAPWatchDaemon(IMAPWatch):
    def __init__(self, pidfile):
        self.pidfile = pidfile
        super().__init__()

    def start(self):
        self.logger.debug('Starting daemon')

        stdout_logger = logging.getLogger('stdout')
        stdout_logger.setLevel(logging.DEBUG)
        stdout_logger.addHandler(self.fileHandler)
        stderr_logger = logging.getLogger('stderr')
        stderr_logger.setLevel(logging.DEBUG)
        stderr_logger.addHandler(self.fileHandler)

        context = LoggingDaemonContext()
        context.detach_process = True
        context.pidfile = self.pidfile
        context.loggers_preserve = [ self.logger ]
        context.stdout_logger = stdout_logger
        context.stderr_logger = stderr_logger
        context.signal_map = {
            signal.SIGTERM: self.stop,
            signal.SIGINT: self.stop,
        }

        with context:
            self.logger.debug("In daemon context")
            print("Print on stdout")
            super().start()
            signal.pause()
