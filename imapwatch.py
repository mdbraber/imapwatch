#!/usr/bin/env python3.6
import signal
import os
from argparse import ArgumentParser
from daemon.pidfile import TimeoutPIDLockFile
from lockfile import AlreadyLocked, LockTimeout
from imapwatch.imapwatch import IMAPWatch, IMAPWatchDaemon

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', metavar='ARG',
                        type=int, choices=range(0, 51),
                        action='store', dest='verbose',
                        default=None,
                        help='Adds a console logger for the level specified in the range 1..50')
    parser.add_argument('--pidfile',
                        action='store', dest='pidfile',
                        default='/tmp/imapwatch.pid',
                        help='PID file')
    args = parser.parse_args()

    pidfile = TimeoutPIDLockFile('/tmp/imapwatch.pid',timeout=1)
    try:
        # we first try to acquire the pidfile lock so we can break on the command line if
        # this won't work. It's not atomic, but good enough for us...
        pidfile.acquire()
    except (AlreadyLocked, LockTimeout) as e:
        try:
            pid = pidfile.read_pid()
            os.kill(pid, 0)
            raise SystemExit(f'Another imapwatch is already running with pid: {pid}')
        except OSError:  #No process with locked PID
            pidfile.break_lock()

    imapwatch = IMAPWatch(args.verbose)
    signal.signal(signal.SIGTERM, imapwatch.stop)
    signal.signal(signal.SIGINT, imapwatch.stop)
    imapwatch.start()
    signal.pause()
