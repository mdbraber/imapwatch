# imapwatch

Daemon (as robust as possible) that can watch for changes (e.g. new or flagged mesages) in IMAP folders using the IDLE command ([RFC 2177](https://tools.ietf.org/html/rfc2177)). Possible to execute a command upon changes, e.g. sending a specific message to your todo-list e-mail address (or basically anything you can build in Python). I'm using it to watch for flagged e-mails and automatically create an item in my Things 3 inbox.

## Usage

```
mdbraber@spiff:~/imapwatch/$ ./imapwatch.py -h
usage: imapwatch [-h] [-b BASEDIR] [-c CONFIGFILE] [-d] [-f] [-l LOGFILE]
                 [-p PIDFILE] [-v {CRITICAL,ERROR,WARNING,INFO,DEBUG}]
                 {start,stop,restart} ...

positional arguments:
  {start,stop,restart}  Actions for imapwatch - default: "start"
    start               Starts imapwatch
    stop                Stops imapwatch
    restart             Restarts imapwatch

optional arguments:
  -h, --help            show this help message and exit
  -b BASEDIR, --base-dir BASEDIR
                        Path to basedir - default: ''
  -c CONFIGFILE, --configfile CONFIGFILE
                        Path to logfile - default: imapwatch.yml
  -d, --daemon          Run as daemon
  -f, --force           Force action (start or stop)
  -l LOGFILE, --logfile LOGFILE
                        Path to logfile - default: log/imapwatch.log
  -p PIDFILE, --pidfile PIDFILE
                        Path to PID file, needs full path! - default:
                        /tmp/imapwatch.pid
  -v {CRITICAL,ERROR,WARNING,INFO,DEBUG}, --loglevel {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Loglevel for the console logger - default: INFO
```

## Want to help?

Feel free to file an issue or create a pull request!
