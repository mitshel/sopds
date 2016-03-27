import os

from django.test import TestCase

from opds_catalog import opdsdb
from opds_catalog.sopdscan import opdsScanner
from opds_catalog import settings

class scanTestCase(TestCase):
    scanner = None
    def setUp(self):
        opdsdb.clear_all()
        test_module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        settings.ROOT_LIB = os.path.join(test_module_path, 'data')
        self.scanner = opdsScanner()


    def test_processfile(self):
        pass


