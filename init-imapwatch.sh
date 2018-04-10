#! /bin/sh
PATH=/bin:/usr/bin:/sbin:/usr/sbin
DAEMON=$HOME/imapwatch/imapwatch.py
DAEMONOPTS="-d"
PIDFILE=/tmp/imapwatchd.pid

test -x $DAEMON || exit 0

set -e

. /lib/lsb/init-functions

case "$1" in
  start)
     log_daemon_msg "Starting imapwatchd"
     start_daemon -p $PIDFILE $DAEMON
     log_end_msg $?
   ;;
  stop)
     log_daemon_msg "Stopping imapwatchd"
     killproc -p $PIDFILE $DAEMON
     #PID=`cat $PIDFILE`
     #kill -9 $PID       
     log_end_msg $?
   ;;
  force-reload|restart)
     $0 stop
     $0 start
   ;;
  status)
     status_of_proc -p $PIDFILE $DAEMON imapwatch.py && exit 0 || exit $?
   ;;
 *)
   echo "Usage: imapwatchd.sh {start|stop|restart|force-reload|status}"
   exit 1
  ;;
esac

exit 0
