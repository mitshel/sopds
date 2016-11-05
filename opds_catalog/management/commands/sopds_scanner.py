import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from opds_catalog.models import Counter
from opds_catalog.sopdscan import opdsScanner
from opds_catalog import settings

class Command(BaseCommand):
    help = 'Scan Books Collection.'

    def add_arguments(self, parser):
        parser.add_argument('--verbose',action='store_true', dest='verbose', default=False, help='Set verbosity level for books collection scan.')
        parser.add_argument('--scan',action='store_true', dest='scan', default=False, help='Scan book collection.')

    def handle(self, *args, **options):             
        logger = logging.getLogger('')
        logger.setLevel(logging.DEBUG)
        formatter=logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')

        if settings.LOGLEVEL!=logging.NOTSET:
            # Создаем обработчик для записи логов в файл
            fh = logging.FileHandler(settings.LOGFILE)
            fh.setLevel(settings.LOGLEVEL)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        if options['verbose']:
            # Создадим обработчик для вывода логов на экран с максимальным уровнем вывода
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        if options['scan']:
            self.stdout.write('Startup book-scan function.')
            self.scan(logger, options['verbose'])

    def scan(self, logger, verbose=False):
        scanner=opdsScanner(logger)
        with transaction.atomic():
            scanner.scan_all()
        Counter.objects.update_known_counters()    

        
 

