#!/usr/bin/env python3.6
import signal
import os
import time
from argparse import ArgumentParser
from imapwatch import IMAPWatch
from daemon.pidfile import TimeoutPIDLockFile

if __name__ == "__main__":

    def start(args):
        imapwatch = IMAPWatch(args.basedir, args.configfile, args.pidfile, args.logfile, args.daemon, args.loglevel, args.force)
        imapwatch.start()
        
    def stop(args):
        try:
            pidfile = TimeoutPIDLockFile(args.pidfile,timeout=1)
            pid = pidfile.read_pid()
            if not pid:
                raise SystemExit("No running imapwatch process found")
            if args.force:
                os.kill(pid, signal.SIGKILL)
                print(f"Killed imapwatch process with pid {pid} with force")
            else:
                print(f"Stopping imapwatch process with pid {pid}: ", end='', flush=True)
                os.kill(pid, signal.SIGTERM)
                while pidfile.is_locked():
                    time.sleep(1)
                    print('.',end='',flush=True)
                print('done!')
        except OSError as e:
            pidfile.break_lock()
            raise SystemExit(f'Cleaning up stale lockfile')

    def restart(args):
        stop(args)
        start(args)

    parser = ArgumentParser(prog='imapwatch')

    parser.add_argument('-b','--base-dir',
                        action='store', dest='basedir',
                        help='Path to basedir - default: \'\'')
    parser.add_argument('-c','--configfile',
                        action='store', dest='configfile',
                        default='imapwatch.yml',
                        help='Path to logfile - default: imapwatch.yml')
    parser.add_argument('-d','--daemon',
                        action='store_true', dest='daemon',
                        help='Run as daemon')
    parser.add_argument('-f','--force',
                        action='store_true', dest='force',
                        help='Force action (start or stop)')
    parser.add_argument('-l','--logfile',
                        action='store', dest='logfile',
                        default='log/imapwatch.log',
                        help='Path to logfile - default: log/imapwatch.log')
    parser.add_argument('-p','--pidfile',
                        action='store', dest='pidfile',
                        default='/tmp/imapwatch.pid',
                        help='Path to PID file, needs full path! - default: /tmp/imapwatch.pid')
    parser.add_argument('-v', '--verbose',
                        action='store', dest='loglevel',
                        choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        default='INFO',
                        help='Loglevel for the console logger - default: INFO')

    sp = parser.add_subparsers(help='Actions for %(prog)s - default: "start"')
    sp_start = sp.add_parser(
        'start',
        help='Starts %(prog)s')
    sp_stop = sp.add_parser(
        'stop',
        description = "Stops %(prog)s if it is currently running",
        help='Stops %(prog)s')
    sp_restart = sp.add_parser(
        'restart',
        description = "Checks if %(prog) is running and tries to restart it",
        help='Restarts %(prog)s')

    sp_stop.set_defaults(func=stop)
    sp_start.set_defaults(func=start)
    sp_restart.set_defaults(func=restart)
    
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        start(args)
