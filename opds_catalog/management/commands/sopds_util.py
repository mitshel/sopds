from django.core.management.base import BaseCommand
from django.core.management import call_command
from opds_catalog import opdsdb
from opds_catalog.models import Counter

class Command(BaseCommand):
    help = 'Utils for SOPDS.'
        
    def add_arguments(self, parser):
        parser.add_argument('--clear',action='store_true', dest='clear', default=False, help='Clear opds database.')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clear book database.')
            self.clear()

    def clear(self):
        opdsdb.clear_all()
        call_command('loaddata', 'genre.json', app_label='opds_catalog') 
        Counter.objects.update_known_counters()

