import os
import signal
import sys
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from opds_catalog.models import Counter
from opds_catalog.sopdscan import opdsScanner
from opds_catalog.settings import SCANNER_LOG, SCAN_SHED_DAY, SCAN_SHED_DOW, SCAN_SHED_HOUR, SCAN_SHED_MIN, LOGLEVEL

class Command(BaseCommand):
    help = 'Scan Books Collection.'

    def add_arguments(self, parser):
        parser.add_argument('command', help='Use [ scan | start | stop | restart ]')
        parser.add_argument('--verbose',action='store_true', dest='verbose', default=False, help='Set verbosity level for books collection scan.')
        parser.add_argument('--daemon',action='store_true', dest='daemonize', default=False, help='Daemonize server')
        
    def handle(self, *args, **options): 
        self.pidfile = os.path.join(settings.BASE_DIR, "sopds-scanner.pid")
        action = options['command']            
        self.logger = logging.getLogger('')
        self.logger.setLevel(logging.DEBUG)
        formatter=logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')

        if LOGLEVEL!=logging.NOTSET:
            # Создаем обработчик для записи логов в файл
            fh = logging.FileHandler(SCANNER_LOG)
            fh.setLevel(LOGLEVEL)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

        if options['verbose']:
            # Создадим обработчик для вывода логов на экран с максимальным уровнем вывода
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            
        if (options["daemonize"] and (action in ["start", "scan"])):
            if sys.platform == "win32":
                self.stdout.write("On Windows platform Daemonize not working.")
            else:         
                daemonize()            

        if action=='scan':
            self.stdout.write('Startup once book-scan.')
            self.scan()   
            self.stdout.write('Complete book-scan.')        
        elif action == "start":
            self.start()
        elif action == "stop":
            pid = open(self.pidfile, "r").read()
            self.stop(pid)
        elif action == "restart":
            pid = open(self.pidfile, "r").read()
            self.restart(pid)            

    def scan(self):
        scanner=opdsScanner(self.logger)
        with transaction.atomic():
            scanner.scan_all()
        Counter.objects.update_known_counters()  
            
    def start(self):
        writepid(self.pidfile)
        self.stdout.write('Startup scheduled book-scan (min=%s, hour=%s, day_of_week=%s, day=%s).'%(SCAN_SHED_MIN,SCAN_SHED_HOUR,SCAN_SHED_DOW,SCAN_SHED_DAY))
        sched = BlockingScheduler()
        sched.add_job(self.scan, 'cron', day=SCAN_SHED_DAY, day_of_week=SCAN_SHED_DOW, hour=SCAN_SHED_HOUR, minute=SCAN_SHED_MIN)
        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C'
        self.stdout.write("Quit the server with %s.\n"%quit_command)  
        try:
            sched.start()
        except (KeyboardInterrupt, SystemExit):
            pass            
    
    def stop(self, pid):
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError as e:
            self.stdout.write("Error stopping sopds_scanner: %s"%str(e))
    
    def restart(self, pid):
        self.stop(pid)
        self.start()

def writepid(pid_file):
    """
    Write the process ID to disk.
    """
    fp = open(pid_file, "w")
    fp.write(str(os.getpid()))
    fp.close()
    
def daemonize():
    """
    Detach from the terminal and continue as a daemon.
    """
    # swiped from twisted/scripts/twistd.py
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent
    os.setsid()
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent again.
    os.umask(0)

    std_in = open("/dev/null", 'r')
    std_out = open(SCANNER_LOG, 'a+')
    os.dup2(std_in.fileno(), sys.stdin.fileno())
    os.dup2(std_out.fileno(), sys.stdout.fileno())
    os.dup2(std_out.fileno(), sys.stderr.fileno())    
    
#    null = os.open("/dev/null", os.O_RDWR)
#    for i in range(3):
#        try:
#            os.dup2(null, i)
#        except OSError as e:
#            if e.errno != errno.EBADF:
#                raise
    os.close(std_in.fileno())
    os.close(std_out.fileno())


    

        
 

