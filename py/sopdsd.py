#!/usr/bin/env python3

import logging
import sys, os, time, atexit
from signal import SIGTERM
from multiprocessing import Process

import sopdscfg
import sopdserve
import sopdsweb
from sopdscan import opdsScanner

#*******************************************
#
#*******************************************
class Daemon:
    def __init__(self, cfg):
        self.cfg = cfg
        self.name = ""
        self.pid = 0
        self.pidfile = ''
        self.stdin  = '/dev/null'
        self.stdout = '/dev/null'
        self.stderr = '/dev/null'
        self.enabled = False

        self.logger = logging.getLogger('')
        self.logger.setLevel(self.cfg.LOGLEVEL)
        formatter=logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        self.fh = logging.FileHandler(self.cfg.SCAND_LOGFILE)
        self.fh.setLevel(self.cfg.LOGLEVEL)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.fh)



    #***************************************
    # Get the pid from pidfile.
    #***************************************
    def getPid(self):
        try:
            pf = open(self.pidfile,'r')
            scan_pid = int(pf.read().strip())
            pf.close()
        except IOError:
            scan_pid = None

        return scan_pid


    #***************************************
    #
    #***************************************
    def removePidFile(self):
        try:
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
        except IOError as e:
            message = str(e) + "\nCan not remove pid file {}".format(self.pidfile)
            sys.stderr.write(message)


    #***************************************
    #
    #***************************************
    def isRunning(self):
        pid = self.getPid();
        if pid:
            try:
                procfile = open("/proc/{}/status".format(pid), 'r')
                procfile.close()
                return True
            except IOError:
                return False

        return False


    #***************************************
    #
    #***************************************
    def start(self):
        if self.isRunning():
            message = "Pidfile {} for {} daemon already exist. Daemon already running?\n".format(self.name, self.pidfile)
            sys.stderr.write(message)
            return;

        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent.
                return
        except OSError as e:
            message = "Fork #2 (scand) failed: {}\n".format(e)
            sys.stderr.write(message)
            sys.exit(1)

        print('{} Daemon going to background, PID: {}'.format(self.name, os.getpid(), end="\r"))

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
        atexit.register(self.removePidFile)
        self._run()


    #***************************************
    #
    #***************************************
    def stop(self):
        """
        Stop the daemon.
        """
        pid = self.getPid()

        if self.enabled and not pid:
            message = "%s daemon not running?\n" % self.name
            sys.stderr.write(message)
            return

        print("Stop %s daemon [%s]" % (self.name, pid))
        try:
            os.kill(pid, SIGTERM)
            time.sleep(1)
        except OSError as e:
            print(str(e))

        self.removePidFile()


    #***************************************
    #
    #***************************************
    def status(self):
        """
        Get status of daemon.
        """

        pid = self.getPid()

        if not pid:
            message = "There is not PID file {}. {} Daemon already running?\n".format(self.pidfile, self.name)
            sys.stdout.write(message)
            return

        if self.isRunning():
            message = "There is a {} process with the PID {}\n".format(self.name, pid)
            sys.stdout.write(message)
        else:
            message = "There is not a {} process with the PID {}\n".format(self.name, pid)
            sys.stdout.write(message)




#*******************************************
#
#*******************************************
class DaemonTool:
    def __init__(self, cfg):
        self.cfg = cfg
        self.daemons = []

        self.daemons.append(ScanDaemon(cfg))
        self.daemons.append(HttpDaemon(cfg))
        self.daemons.append(WebDaemon(cfg))

        hasEnabled = False
        for daemon in self.daemons:
            hasEnabled = hasEnabled or daemon.enabled

        if not hasEnabled:
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


    #***************************************
    #
    #***************************************
    def start(self):
        """
        Deamonize, do double-fork magic.
        """
        self.logger.info('sopdsDaemon start()...')

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

        # Do next forks
        for daemon in self.daemons:
            if daemon.enabled:
                pid = daemon.start()


    #***************************************
    #
    #***************************************
    def stop(self):
        self.logger.info('sopdsDaemon stop()...')

        for daemon in self.daemons:
            if daemon.isRunning:
                daemon.stop();


    #***************************************
    #
    #***************************************
    def status(self):
        self.logger.info('sopdsDaemon status()...')
        for daemon in self.daemons:
            daemon.status()


    #***************************************
    #
    #***************************************
    def restart(self):
        self.stop()
        self.start()



#*******************************************
#
#*******************************************
class ScanDaemon(Daemon):

    #***************************************
    #
    #***************************************
    def __init__(self, cfg):
        Daemon.__init__(self, cfg)
        self.name    = "SOPDS SCAN"
        self.pidfile = self.cfg.PID_FILE
        self.stdout  = self.cfg.SCAND_LOGFILE
        self.stderr  = self.cfg.SCAND_LOGFILE
        self.enabled = self.cfg.SCAN_DAEMON
        self.start_scan=False
        self.scanner=opdsScanner(self.cfg, self.logger)


    #***************************************
    #
    #***************************************
    def _run(self):
        self.logger.info('sopdsDaemon entering in main loop...')

        while True:
            t=time.localtime()
            if (((self.cfg.DAY_OF_WEEK==0) or (self.cfg.DAY_OF_WEEK==t.tm_wday+1)) and (t.tm_hour*60+t.tm_min in self.cfg.SCAN_TIMES)) or (self.cfg.SCAN_ON_START and not self.start_scan):
                  self.scanner.scan_all()
            self.start_scan=True
            time.sleep(30)


#*******************************************
#
#*******************************************
class HttpDaemon(Daemon):

    #***************************************
    #
    #***************************************
    def __init__(self, cfg):
        Daemon.__init__(self, cfg)
        self.name    = "SOPDS HTTP"
        self.pidfile = self.cfg.HTTPD_PID_FILE
        self.stdout  = self.cfg.HTTPD_LOGFILE
        self.stderr  = self.cfg.HTTPD_LOGFILE
        self.enabled = self.cfg.HTTP_DAEMON


    #***************************************
    #
    #***************************************
    def _run(self):
        sopdserve.start_server(self.cfg)



#*******************************************
#
#*******************************************
class WebDaemon(Daemon):

    #***************************************
    #
    #***************************************
    def __init__(self, cfg):
        Daemon.__init__(self, cfg)
        self.name    = "SOPDS WEB"
        self.pidfile = self.cfg.WEB_PID_FILE
        self.stdout  = self.cfg.WEB_LOGFILE
        self.stderr  = self.cfg.WEB_LOGFILE
        self.enabled = self.cfg.WEB_DAEMON


    #***************************************
    #
    #***************************************
    def _run(self):
        sopdsweb.start_server(self.cfg)

#*******************************************
#
#*******************************************
if __name__ == "__main__":
    cfg=sopdscfg.cfgreader()

    daemonTool = DaemonTool(cfg)

    if len(sys.argv) == 2:

        if 'start' == sys.argv[1]:
            daemonTool.start()

        elif 'stop' == sys.argv[1]:
            daemonTool.stop()

        elif 'restart' == sys.argv[1]:
            daemonTool.restart()

        elif 'status' == sys.argv[1]:
            daemonTool.status()

        else:
            print ("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print ('show cmd deamon usage')
        print ("Usage: {} start|stop|restart|status".format(sys.argv[0]))
        sys.exit(2)
