#!/usr/bin/env python3

import logging
import sys, os, time, atexit
from signal import SIGTERM

import sopdscfg
from sopdscan import opdsScanner
 
class Daemon(object):
    """
    Subclass Daemon class and override the run() method.
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
 
    def daemonize(self):
        """
        Deamonize, do double-fork magic.
        """
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent.
                sys.exit(0)
        except OSError as e:
            message = "Fork #1 failed: {}\n".format(e)
            sys.stderr.write(message)
            sys.exit(1)
 
        # Decouple from parent environment.
        os.chdir("/")
        os.setsid()
        os.umask(0)
 
        # Do second fork.
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent.
                sys.exit(0)
        except OSError as e:
            message = "Fork #2 failed: {}\n".format(e)
            sys.stderr.write(message)
            sys.exit(1)
 
        print('daemon going to background, PID: {}'.format(os.getpid(),end="\r"))
 
        # Redirect standard file descriptors.
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
 
        # Write pidfile.
        pid = str(os.getpid())
        open(self.pidfile,'w+').write("{}\n".format(pid))
 
        # Register a function to clean up.
        atexit.register(self.delpid)
 
    def delpid(self):
        os.remove(self.pidfile)
 
    def start(self):
        """
        Start daemon.
        """
        # Check pidfile to see if the daemon already runs.
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
 
        if pid:
            message = "Pidfile {} already exist. Daemon already running?\n".format(self.pidfile)
            sys.stderr.write(message)
            sys.exit(1)
 
        # Start daemon.
        self.daemonize()
        self.run()
 
    def status(self):
        """
        Get status of daemon.
        """
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            message = "There is not PID file. Daemon already running?\n"
            sys.stderr.write(message)
            sys.exit(1)
 
        try:
            procfile = open("/proc/{}/status".format(pid), 'r')
            procfile.close()
            message = "There is a process with the PID {}\n".format(pid)
            sys.stdout.write(message)
        except IOError:
            message = "There is not a process with the PID {}\n".format(self.pidfile)
            sys.stdout.write(message)
 
    def stop(self):
        """
        Stop the daemon.
        """
        # Get the pid from pidfile.
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError as e:
            message = str(e) + "\nDaemon not running?\n"
            sys.stderr.write(message)
            sys.exit(1)
 
        # Try killing daemon process.
        try:
            os.kill(pid, SIGTERM)
            time.sleep(1)
        except OSError as e:
            print(str(e))
            sys.exit(1)
 
        try:
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
        except IOError as e:
            message = str(e) + "\nCan not remove pid file {}".format(self.pidfile)
            sys.stderr.write(message)
            sys.exit(1)
 
    def restart(self):
        """
        Restart daemon.
        """
        self.stop()
        time.sleep(1)
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been daemonized by start() or restart().
        """
 
class opdsDaemon(Daemon):
    def __init__(self):
        self.start_scan=False
        self.cfg=sopdscfg.cfgreader()

        self.logger = logging.getLogger('')
        self.logger.setLevel(self.cfg.LOGLEVEL)
        formatter=logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        self.fh = logging.FileHandler(self.cfg.LOGFILE)
        self.fh.setLevel(self.cfg.LOGLEVEL)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.fh)
        self.logger.info('sopdsDaemon initializing...')

        self.scanner=opdsScanner(self.cfg, self.logger)

        Daemon.__init__(self, self.cfg.PID_FILE, self.cfg.LOGFILE,self.cfg.LOGFILE,self.cfg.LOGFILE)

    def start(self):
        self.logger.info('sopdsDaemon starting...')
        Daemon.start(self)

    def delpid(self):
        self.logger.info('sopdsDaemon exitting (delpid function)...')
        Daemon.delpid(self)

    def status(self):
        self.logger.info('sopdsDaemon status checking...')
        Daemon.status(self)

    def stop(self):
        self.logger.info('sopdsDaemon stopping...')
        Daemon.stop(self)

    def restart(self):
        self.logger.info('sopdsDaemon restarting...')
        Daemon.restart(self)

    def run(self):
        self.cfg.parse()
        self.fh.setLevel(self.cfg.LOGLEVEL)
        self.logger.info('sopdsDaemon entering in main loop...')
        
        while True:
            t=time.localtime()
            if (((self.cfg.DAY_OF_WEEK==0) or (self.cfg.DAY_OF_WEEK==t.tm_wday+1)) and (t.tm_hour*60+t.tm_min in self.cfg.SCAN_TIMES)) or (self.cfg.SCAN_ON_START and not self.start_scan):
                  self.scanner.log_options()
                  self.scanner.scan_all()
                  self.scanner.log_stats()
            self.start_scan=True
            time.sleep(30)

 
if __name__ == "__main__":

    daemon = opdsDaemon()
    if len(sys.argv) == 2:
#        print('{} {}'.format(sys.argv[0],sys.argv[1]))
 
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'status' == sys.argv[1]:
            daemon.status()
        else:
            print ("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print ('show cmd deamon usage')
        print ("Usage: {} start|stop|restart|status".format(sys.argv[0]))
        sys.exit(2)

