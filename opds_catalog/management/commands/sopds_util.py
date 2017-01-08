from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.conf import settings as main_settings

from opds_catalog import opdsdb
from opds_catalog import models
from opds_catalog.models import Counter

from constance import config

class Command(BaseCommand):
    help = 'Utils for SOPDS.'
    verbose = False
        
    def add_arguments(self, parser):
        parser.add_argument('command', action="store", nargs='*', help='Use [ clear | info | save_mygenres | load_mygenres | setconf | getconf ]') 
        parser.add_argument('--verbose',action='store_true', dest='verbose', default=False, help='Set verbosity level for books collection scan.')  
        parser.add_argument('--nogenres',action='store_true', dest='nogenres', default=False, help='Not install genres fom fixtures.')              

    def handle(self, *args, **options):
        action = options['command'][0] 
        
        self.verbose = options['verbose']
        self.nogenres = options['nogenres']
               
        if action=='clear':
            self.stdout.write('Clear book database.')
            self.clear()        
        elif action == "info":
            self.info()
        elif action == "save_mygenres":
            self.save_mygenres()
        elif action == "load_mygenres":
            self.load_mygenres()
        elif action == "setconf":
            self.confparam = options['command'][1] if len(options['command'])>1 else None
            self.confvalue = options['command'][2] if len(options['command'])>2 else None
            self.setconf(self.confparam, self.confvalue)         
        elif action == "getconf":
            self.confparam = options['command'][1] if len(options['command'])>1 else None
            self.getconf(self.confparam)   

    def clear(self):
        with transaction.atomic():
            opdsdb.clear_all(self.verbose)
        if not self.nogenres:
            call_command('loaddata', 'genre.json', app_label='opds_catalog') 
        Counter.objects.update_known_counters()
        
    def info(self):
        Counter.objects.update_known_counters()
        self.stdout.write('Books count    = %s'%Counter.objects.get_counter(models.counter_allbooks))
        self.stdout.write('Catalogs count = %s'%Counter.objects.get_counter(models.counter_allcatalogs))
        self.stdout.write('Authors count  = %s'%Counter.objects.get_counter(models.counter_allauthors))
        self.stdout.write('Genres count   = %s'%Counter.objects.get_counter(models.counter_allgenres))
        self.stdout.write('Series count   = %s'%Counter.objects.get_counter(models.counter_allseries))  
        
    def save_mygenres(self):     
        call_command('dumpdata', 'opds_catalog.genre','--output','opds_catalog/fixtures/mygenres.json', app_label='opds_catalog')  
        self.stdout.write('Genre dump saved in opds_catalog/fixtures/mygenres.json')
        
    def load_mygenres(self):  
        opdsdb.clear_genres(self.verbose)   
        call_command('loaddata', 'mygenres.json', app_label='opds_catalog')  
        Counter.objects.update_known_counters()
        self.stdout.write('Genres load from opds_catalog/fixtures/mygenres.json')
        
    def setconf(self, confparam, confvalue):  
        if confparam and confvalue:
            call_command('constance', 'set',confparam, confvalue, app_label='opds_catalog')
            self.stdout.write('Config parameter %s set to %s'%(confparam, confvalue))
            
            
    def getconf(self, confparam):  
        if confparam:
            call_command('constance', 'get', confparam, app_label='opds_catalog')
        else:
            call_command('constance', 'list', app_label='opds_catalog')

            

