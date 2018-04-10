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

## Configuration (example)

Example configuration in [YAML syntax](http://pyyaml.org/wiki/PyYAMLDocumentation) (also included as `imapwatch_example.yml`). Actions are examples and you could/should build your own (`things` is included as an example and exists in the current code). Check [imapwatch/checker.py](blob/master/imapwatch/checker.py) for the relevant code (see the `dispatch` function). 

You can (for now) use multiple accounts, multiple actions and a single SMTP server. Take good care
of writing good YAML syntax (check for when to use `-` as delineator for blocks) and use `['']` with
the `check_for` item.

To use this configuration file, rename to `imapwatch.yml` (or specify a different file using the
`-c` / `--configfile` parameter).

```
accounts:
  - account: 'provider'
    server: 'imap.provider.com'
    username: 'john@provider.com'
    password: 'mysecretpass'
    use_ssl: True
    timeout: 15
    mailboxes:
      - mailbox: 'INBOX'
        check_for: ['flagged']
        action: 'things'
      - mailbox: '+Later'
        check_for: ['flagged']
        action: 'things'
      - mailbox: '+News'
        check_for: ['flagged']
        action: 'things'
      - mailbox: '+TODO'
        check_for: ['new']
        action: 'things'

actions:
  - action: 'things'
    email: 'add-to-things-xxxxxxx@things.email'

smtp:
  server: 'smtp.provider.com'
  username: 'john@provider.com'
  password: 'mysecretpass'
  from: 'john@provider.com'
```

## Want to help?

Feel free to file an issue or create a pull request!
