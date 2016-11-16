from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction

from opds_catalog import opdsdb
from opds_catalog import models
from opds_catalog.models import Counter

class Command(BaseCommand):
    help = 'Utils for SOPDS.'
    verbose = False
        
    def add_arguments(self, parser):
        parser.add_argument('command', help='Use [ clear | info ]')
        parser.add_argument('--verbose',action='store_true', dest='verbose', default=False, help='Set verbosity level for books collection scan.')        

    def handle(self, *args, **options):
        action = options['command'] 
        
        self.verbose = options['verbose']
               
        if action=='clear':
            self.stdout.write('Clear book database.')
            self.clear()        
        elif action == "info":
            self.info()

    def clear(self):
        with transaction.atomic():
            opdsdb.clear_all(self.verbose)
        call_command('loaddata', 'genre.json', app_label='opds_catalog') 
        Counter.objects.update_known_counters()
        
    def info(self):
        Counter.objects.update_known_counters()
        self.stdout.write('Books count    = %s'%Counter.objects.get_counter(models.counter_allbooks))
        self.stdout.write('Catalogs count = %s'%Counter.objects.get_counter(models.counter_allcatalogs))
        self.stdout.write('Authors count  = %s'%Counter.objects.get_counter(models.counter_allauthors))
        self.stdout.write('Genres count   = %s'%Counter.objects.get_counter(models.counter_allgenres))
        self.stdout.write('Series count   = %s'%Counter.objects.get_counter(models.counter_allseries))        
        

