#!/usr/bin/env python3.6
import signal
import os
from argparse import ArgumentParser
from daemon.pidfile import TimeoutPIDLockFile
from lockfile import AlreadyLocked, LockTimeout
from imapwatch.imapwatch import IMAPWatch, IMAPWatchDaemon

if __name__ == "__main__":
    def start(args):
        pidfile = TimeoutPIDLockFile(args.pidfile,timeout=1)
        try:
            # we first try to acquire the pidfile lock so we can break on the command line if
            # this won't work. It's not atomic, but good enough for us...
            pidfile.acquire()
            # if we're in daemon mode we need to break the lock so DaemonContext can use it's own lock
            pidfile.break_lock()
        except (AlreadyLocked, LockTimeout) as e:
            try:
                pid = pidfile.read_pid()
                os.kill(pid, 0)
                raise SystemExit(f'Another imapwatch is already running with pid: {pid}')
            except OSError:  #No process with locked PID
                pidfile.break_lock()

        imapwatch = IMAPWatchDaemon(pidfile)
        imapwatch.start()

    def stop(args):
        pidfile = TimeoutPIDLockFile(args.pidfile,timeout=1)
        try:
            pid = pidfile.read_pid()
            if not pid:
                raise SystemExit("No running imapwatch process found")
            if args.force:
                os.kill(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGTERM)
        except Exception as e:
            print(f'Error: {e}')

    def restart(args):
        stop(args)
        start(args)

    parser = ArgumentParser(prog='imapwatchd')
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Terminates the process forcefully'
    )
    parser.add_argument('-p',
                        action='store', dest='pidfile',
                        default='/tmp/imapwatch.pid',
                        help='PID file')
    sp = parser.add_subparsers()
    sp_start = sp.add_parser(
        'start',
        help='Starts %(prog)s'
    )

    sp_stop = sp.add_parser(
        'stop',
        description = "Stops %(prog)s if it is currently running",
        help='Stops %(prog)s'
    )
    sp_restart = sp.add_parser(
        'restart',
        description = "Checks if %(prog) is running and tries to restart it",
        help='Restarts %(prog)s'
    )

    sp_stop.set_defaults(func=stop)
    sp_start.set_defaults(func=start)
    sp_restart.set_defaults(func=restart)
    
    args = parser.parse_args()

    args.func(args)
