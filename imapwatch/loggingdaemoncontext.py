import os
import daemon
import sys
from .filelikelogger import FileLikeLogger
     
class LoggingDaemonContext(daemon.DaemonContext):

    def __init__(
        self,
        chroot_directory=None,
        working_directory='/',
        umask=0,
        uid=None,
        gid=None,
        prevent_core=True,
        detach_process=None,
        files_preserve=[],   # changed default
        loggers_preserve=[], # new
        pidfile=None,
        stdout_logger = None,  # new
        stderr_logger = None,  # new
        #stdin,   omitted!
        stdin = None,
        #stdout,  omitted!
        stdout = None,
        #sterr,   omitted!
        stderr = None,
        signal_map=None,
        ):

        self.stdout_logger = stdout_logger
        self.stderr_logger = stderr_logger
        self.loggers_preserve = loggers_preserve

        devnull_in = open(os.devnull, 'r+')
        devnull_out = open(os.devnull, 'w+')
        files_preserve.extend([devnull_in, devnull_out])

        super().__init__(
            chroot_directory = chroot_directory,
            working_directory = working_directory,
            umask = umask,
            uid = uid,
            gid = gid,
            prevent_core = prevent_core,
            detach_process = detach_process,
            files_preserve = files_preserve, 
            pidfile = pidfile,
            #stdin = devnull_in,
            #stdout = devnull_out,
            #stderr = devnull_out,
            stdin = sys.stdin,
            stdout = sys.stdout,
            stderr = sys.stderr,
            signal_map = signal_map) 

    def _openFilesFromLoggers(self, loggers):
        "returns the open files used by file-based handlers of the specified loggers"
        openFiles = []
        for logger in loggers:
            for handler in logger.handlers:
                if hasattr(handler, 'stream') and hasattr(handler.stream, 'fileno'):
                    if handler.stream.fileno() not in openFiles:
                        openFiles.append(handler.stream.fileno())
                if hasattr(handler, 'socket') and hasattr(handler.socket, 'fileno'):
                    if handler.socket.fileno() not in openFiles:
                        openFiles.append(handler.socket.fileno())
        return openFiles

    def _addLoggerFiles(self):
        "adds all files related to loggers_preserve to files_preserve"
        for logger in [self.stdout_logger, self.stderr_logger]:
            if logger:
                self.loggers_preserve.append(logger)
        loggerFiles = self._openFilesFromLoggers(self.loggers_preserve)
        self.files_preserve.extend(loggerFiles)

    def open(self): 
        self._addLoggerFiles() 
        super().open()
        #if self.stdout_logger:
        #    fileLikeObj = FileLikeLogger(self.stdout_logger)
        #    sys.stdout = fileLikeObj
        #if self.stderr_logger:
        #    fileLikeObj = FileLikeLogger(self.stderr_logger)
        #    sys.stderr = fileLikeObj
