# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.utils.translation import ugettext as _


class DownloadsTestCase(TestCase):
    fixtures = ['testdb.json']
    
    def setUp(self):
        pass            
  
    def test_download_book(self):
        pass
    
    def test_download_zip(self):
        pass    
    
    def test_download_cover(self):
        pass    