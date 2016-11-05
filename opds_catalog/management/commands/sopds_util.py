from django.core.management.base import BaseCommand
from django.core.management import call_command
from opds_catalog import opdsdb

class Command(BaseCommand):
    help = 'Utils for SOPDS.'

    def add_arguments(self, parser):
        parser.add_argument('--clear',action='store_true', dest='clear', default=False, help='Clear opds database.')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clear book database.')

    def clear(self,verbose=False):
        opdsdb.clear_all()
        call_command('loaddata', 'genre.json', app_label='opds_catalog') 

