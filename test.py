import time
import sys
import daemon
from daemon.pidfile import TimeoutPIDLockFile

pidfile = TimeoutPIDLockFile('/tmp/imapwatch.pid',timeout=1)
context = daemon.DaemonContext(pidfile = pidfile, detach_process = False, stdout=sys.stdout, stderr=sys.stderr)


with context as c:
    while True:
        print('Test')
        print(f'c.pidfile: {c.pidfile}')
        print(f'c.pidfile.read_pid(): {c.pidfile.read_pid()}')
