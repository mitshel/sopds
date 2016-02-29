from django.core.management.base import BaseCommand, CommandError
#from photogal.models import Setting, PhotoAlbums, PhotoImages, addimage
from django.utils import timezone
import os

class Command(BaseCommand):
    help = 'Scan Books Collection.'

    def add_arguments(self, parser):
        parser.add_argument('--verbose',action='store_true', dest='verbose', default=False, help='Set verbosity level for books collection scan.')

    def handle(self, *args, **options):
        self.stdout.write('Startup book-scan function.')
        self.scan(options['verbose'])

    def scan(self,verbose=False):
        pass

