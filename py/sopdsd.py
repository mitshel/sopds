#!/usr/bin/env python3

import logging
import sys, os, time, atexit
from signal import SIGTERM
from multiprocessing import Process

import sopdscfg
import sopdserve
from sopdscan import opdsScanner

typeSCAND = 0
typeHTTPD = 1
 
class Daemon(object):
    """
    Subclass Daemon class and override the run() method.
    """
    def __init__(self, scan_pidfile, http_pidfile, stdin='/dev/null', scan_stdout='/dev/null', http_stdout='/dev/null', scan_stderr='/dev/null', http_stderr='/dev/null', enable_scand=True, enable_httpd=True):
        self.stdin = stdin
        self.scan_stdout = scan_stdout
        self.scan_stderr = scan_stderr
        self.http_stdout = http_stdout
        self.http_stderr = http_stderr
        self.scan_pidfile  = scan_pidfile
        self.http_pidfile  = http_pidfile
        self.enable_httpd = enable_httpd
        self.enable_scand = enable_scand
        self.daemon_type = 0
 
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
 
        # Do second fork (SCAN DAEMON)
        if self.enable_scand:
           try:
               pid = os.fork()
               if pid > 0:
                   # Exit from second parent.
                   sys.exit(0)
           except OSError as e:
               message = "Fork #2 (scand) failed: {}\n".format(e)
               sys.stderr.write(message)
               sys.exit(1)

        # Do third fork (HTTPD DAEMON)
        if self.enable_httpd:
           try: 
               pid = os.fork()
               if pid>0 and not self.enable_scand:
                   # Exit from second parent.
                   sys.exit(0)
           except OSError as e:
               message = "Fork #3 (httpd) failed: {}. Exitting\n".format(e)
               sys.stderr.write(message)
               sys.exit(1)

 
        if (pid>0 and self.enable_httpd) or (self.enable_httpd and not self.enable_scand):
           print('SOPDS HTTP Daemon going to background, PID: {}'.format(os.getpid(),end="\r"))
           self.daemon_type=typeHTTPD
           self.pidfile=self.http_pidfile
           self.stdout=self.http_stdout
           self.stderr=self.http_stderr
        else:
           print('SOPDS SCAN Daemon going to background, PID: {}'.format(os.getpid(),end="\r"))
           self.daemon_type=typeSCAND
           self.pidfile=self.scan_pidfile
           self.stdout=self.scan_stdout
           self.stderr=self.scan_stderr
 
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
        scan_pid=None
        http_pid=None
 
        if self.enable_scand:
           try:
               pf = open(self.scan_pidfile,'r')
               scan_pid = int(pf.read().strip())
               pf.close()
           except IOError:
               scan_pid = None

           if scan_pid:
               message = "Pidfile {} for SOPDS SCAN daemon already exist. Daemon already running?\n".format(self.scan_pidfile)
               sys.stderr.write(message)


        if self.enable_httpd:
           try:
               pf = open(self.http_pidfile,'r')
               http_pid = int(pf.read().strip())
               pf.close()
           except IOError:
               http_pid = None
 
           if http_pid:
               message = "Pidfile {} for SOPDS HTTP daemon already exist. Daemon already running?\n".format(self.http_pidfile)
               sys.stderr.write(message)

        if (scan_pid and self.enable_scand) or (http_pid and self.enable_httpd):
             sys.exit(1)
 
        # Start daemon.
        self.daemonize()
        self.run()
 
    def status(self):
        """
        Get status of daemon.
        """
        scan_pid = None
        http_pid = None

        if self.enable_scand:
           try:
               pf = open(self.scan_pidfile,'r')
               scan_pid = int(pf.read().strip())
               pf.close()
           except IOError:
               message = "There is not PID file {}. SOPDS SCAN Daemon already running?\n".format(self.scan_pidfile)
               sys.stderr.write(message)
               scan_pid = None

        if self.enable_httpd:
           try:
               pf = open(self.http_pidfile,'r')
               http_pid = int(pf.read().strip())
               pf.close()
           except IOError:
               message = "There is not PID file {}. SOPDS HTTP Daemon already running?\n".format(self.http_pidfile)
               sys.stderr.write(message)
               http_pid=None

        if not ((scan_pid or not self.enable_scand) and (http_pid or not self.enable_httpd)):
            sys.exit(1)
 
        if self.enable_scand:
           try:
               procfile = open("/proc/{}/status".format(scan_pid), 'r')
               procfile.close()
               message = "There is a SOPDS SCAN process with the PID {}\n".format(scan_pid)
               sys.stdout.write(message)
           except IOError:
               message = "There is not a SOPDS SCAN process with the PID {}\n".format(self.scan_pid)
               sys.stdout.write(message)

        if self.enable_httpd:
           try:
               procfile = open("/proc/{}/status".format(http_pid), 'r')
               procfile.close()
               message = "There is a SOPDS HTTP process with the PID {}\n".format(http_pid)
               sys.stdout.write(message)
           except IOError:
               message = "There is not a SOPDS HTTP process with the PID {}\n".format(self.http_pid)
               sys.stdout.write(message)

 
    def stop(self):
        """
        Stop the daemon.
        """
        # Get the pid from pidfile.
        scan_pid=None
        http_pid=None
 
        if self.enable_scand:
           try:
               pf = open(self.scan_pidfile,'r')
               scan_pid = int(pf.read().strip())
               pf.close()
           except IOError as e:
               message = str(e) + "\n SOPDS SCAN Daemon not running?\n"
               sys.stderr.write(message)
               scan_pid = None

           if scan_pid:
              try:
                  os.kill(scan_pid, SIGTERM)
                  time.sleep(1)
              except OSError as e:
                  print(str(e))

           try:
               if os.path.exists(self.scan_pidfile):
                   os.remove(self.scan_pidfile)
           except IOError as e:
               message = str(e) + "\nCan not remove pid file {}".format(self.scan_pidfile)
               sys.stderr.write(message)

        if self.enable_httpd:
           try:
               pf = open(self.http_pidfile,'r')
               http_pid = int(pf.read().strip())
               pf.close()
           except IOError as e:
               message = str(e) + "\n SOPDS HTTP Daemon not running?\n"
               sys.stderr.write(message)
               http_pid = None

           if http_pid:
              try:
                  os.kill(http_pid, SIGTERM)
                  time.sleep(1)
              except OSError as e:
                  print(str(e))

           try:
               if os.path.exists(self.http_pidfile):
                   os.remove(self.http_pidfile)
           except IOError as e:
               message = str(e) + "\nCan not remove pid file {}".format(self.scan_pidfile)
               sys.stderr.write(message)
 
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
        if not (self.cfg.SCAN_DAEMON or self.cfg.HTTP_DAEMON):
           print('Check configuration file. No daemons enabled.')
           sys.exit(0)

        self.logger = logging.getLogger('')
        self.logger.setLevel(self.cfg.LOGLEVEL)
        formatter=logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        self.fh = logging.FileHandler(self.cfg.SCAND_LOGFILE)
        self.fh.setLevel(self.cfg.LOGLEVEL)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.fh)
        self.logger.info('sopdsDaemon __init__()...')

        self.scanner=opdsScanner(self.cfg, self.logger)

        Daemon.__init__(self, self.cfg.PID_FILE, self.cfg.HTTPD_PID_FILE, '/dev/null', self.cfg.SCAND_LOGFILE,self.cfg.HTTPD_LOGFILE,self.cfg.SCAND_LOGFILE,self.cfg.HTTPD_LOGFILE, self.cfg.SCAN_DAEMON, self.cfg.HTTP_DAEMON)

    def start(self):
        self.logger.info('sopdsDaemon start()...')
        Daemon.start(self)

    def delpid(self):
        self.logger.info('sopdsDaemon delpid()...')
        Daemon.delpid(self)

    def status(self):
        self.logger.info('sopdsDaemon status()...')
        Daemon.status(self)

    def stop(self):
        self.logger.info('sopdsDaemon stop()...')
        Daemon.stop(self)

    def restart(self):
        self.logger.info('sopdsDaemon restart()...')
        Daemon.restart(self)

    def run_scanner(self):
        self.cfg.parse()
        self.fh.setLevel(self.cfg.LOGLEVEL)
        self.logger.info('sopdsDaemon entering in main loop...')

        while True:
            t=time.localtime()
            if (((self.cfg.DAY_OF_WEEK==0) or (self.cfg.DAY_OF_WEEK==t.tm_wday+1)) and (t.tm_hour*60+t.tm_min in self.cfg.SCAN_TIMES)) or (self.cfg.SCAN_ON_START and not self.start_scan):
                  self.scanner.scan_all()
            self.start_scan=True
            time.sleep(30)

    def run_server(self):
        sopdserve.start_server(self.cfg)

    def run(self):
        if self.daemon_type == typeSCAND:
           self.run_scanner()
        else:
           self.run_server()
 
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

