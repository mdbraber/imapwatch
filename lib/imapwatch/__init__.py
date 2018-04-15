__all__ = ["checker", "sender", "filelikelogger","loggingdaemoncontext"]

import time
import logging
import yaml
import threading
import daemon
import sys
import os
import signal
from logging.handlers import RotatingFileHandler
from daemon.pidfile import TimeoutPIDLockFile
from lockfile import AlreadyLocked, LockTimeout, NotLocked
from .sender import Sender
from .checker import Checker, CheckerThread
from .loggingdaemoncontext import LoggingDaemonContext


class IMAPWatch:

    def __init__(self, basedir = None, configfile = 'imapwatch.yml', pidfile = '/tmp/imapwatch.pid', logfile = 'log/imapwatch.log', daemon = False, verbose = None, force = False):
        
        if basedir:
            # basedir must be a full, absolute path
            __location__ = os.path.realpath(os.path.join(basedir))
        else:
            # assume the configfile and log are in the parent-parent directory of the directory of this file
            __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(os.path.realpath(__file__)), os.pardir, os.pardir))
        
        configfile = os.path.join(__location__, configfile)
        self.config = yaml.load(open(configfile,'r'))
        if not self.config:
            raise SystemExit("No config file found. Exiting.")

        self.pidfile = TimeoutPIDLockFile(pidfile,timeout=1)
        self.logfile = os.path.join(__location__, logfile)
        self.daemon = daemon
        self.verbose = verbose
        self.force = force

        self.stop_event = threading.Event()
        self.threads = []

    def start(self):

        self.setup_logging()

        context = LoggingDaemonContext()
        context.loggers_preserve = [ self.logger ]
        context.stdout_logger = self.stdout_logger
        context.stderr_logger = self.stderr_logger
        context.pidfile = self.pidfile 
        context.signal_map = {
            signal.SIGTERM: self.stop,
            signal.SIGINT: self.stop,
        }

        if self.daemon:
            context.detach_process = True
        else:
            context.detach_process = False
            # TODO should this not be below the else statement?
            context.stdout = sys.stdout
            context.stdin = sys.stdin

        # TODO first acquire and then release so we can go back to the command line
        # then do the same in the DaemonContext
        try:
            with context as c:
                self.logger.info('---------------')
                self.logger.info(f'Starting daemon with pid {self.pidfile.read_pid()}')
                sender = Sender(self.logger, self.config['smtp']['server'], self.config['smtp']['username'], self.config['smtp']['password'], self.config['smtp']['from'])

                self.logger.info("Setting up mailboxes")
                for account in self.config['accounts']:
                    mailboxes = account['mailboxes']
                    for mailbox in mailboxes:
                        action = [ a for a in self.config['actions'] if a['action'] == mailbox['action'] ][0]  
                        checker = Checker(self.logger, self.stop_event, account['server'], account['username'], account['password'], mailbox['mailbox'], mailbox['check_for'], action, sender, bool(account['use_ssl']), int(account['timeout']))
                        checker_thread = CheckerThread(self.logger, checker)
                        self.threads.append(checker_thread)
                        checker_thread.start()
                
                # we have to do this, otherwise we lose the context and lockfile
                # (after all the threads have been created and detached)
                while not self.stop_event.is_set():
                    time.sleep(1)
        except FileExistsError:
            self.logger.debug('Removed stale lock file')
            self.pidfile.break_lock()
        except AlreadyLocked:
            if not self.force:
                raise SystemExit('Another imapwatch process already running')
            pass
        except LockTimeout:
            raise SystemExit('LockTimeout')
        except NotLocked:
            raise SystemExit('NotLocked')
            pass
                
    def setup_logging(self):

        # configure logging
        logFormatter = logging.Formatter('%(asctime)s %(name)-10.10s [%(process)-5d] [%(levelname)-8.8s] [%(threadName)-11.11s] %(message)s')
        self.logger = logging.getLogger('imapwatch')
        # this shouldn't be necessary? level should be NOTSET standard
        # https://docs.python.org/3/library/logging.html
        self.logger.setLevel(logging.DEBUG)

        # create the filehandler 
        self.fileHandler = RotatingFileHandler(
            self.logfile,
            mode='a',
            maxBytes=1048576,
            backupCount=9,
            encoding='UTF-8',
            # if we don't set delay to False, the stream is not opened until we start writing
            # this prevents getLogFileHandler() to find the right handle to preserve
            delay=False
            )
        self.fileHandler.formatter = logFormatter
        self.logger.addHandler(self.fileHandler)
        
        # get the (already existing) imapclient logger 
        self.imapclient_logger = logging.getLogger('imapclient')
        self.imapclient_logger.addHandler(self.fileHandler)

        self.stdout_logger = logging.getLogger('stdout')
        self.stdout_logger.setLevel(logging.DEBUG)
        self.stdout_logger.addHandler(self.fileHandler)
        
        self.stderr_logger = logging.getLogger('stderr')
        self.stderr_logger.setLevel(logging.DEBUG)
        self.stderr_logger.addHandler(self.fileHandler)
       
        consoleHandler = logging.StreamHandler()
        consoleHandler.formatter = logFormatter

        if not self.daemon:
            # Add optional ConsoleHandler
            consoleHandler.setLevel('DEBUG')
            self.logger.setLevel(self.verbose)
            
            self.logger.addHandler(consoleHandler)
            self.stdout_logger.addHandler(consoleHandler)
            self.stderr_logger.addHandler(consoleHandler)
            
            # TODO add custom level for imapclient logging on the console
            # or in the configfile?
            self.imapclient_logger.addHandler(consoleHandler)
 
    def stop(self, signum, frame):
        self.logger.debug('Stopping')
        self.stop_event.set()
        # TODO should we use threading.enumerate() to stop threads?
        # https://docs.python.org/3/library/threading.html
        for t in self.threads:
            #self.logger.debug(f'Calling stop() for thread {t.name}')
            t.stop()
            #self.logger.debug(f'Finished stop() for thread {t.name}')
            #self.logger.debug(f'Calling join() for thread {t.name}')
            t.join()
            #self.logger.debug(f'Finshed join() for thread {t.name}') 
        self.logger.info('Stopped')
