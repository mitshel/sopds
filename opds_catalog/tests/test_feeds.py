# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.utils.translation import ugettext as _


class ModelsTestCase(TestCase):
    fixtures = ['testdb.json']
    
    def setUp(self):
        pass            
  
    def test_MainFeed(self):
        c = Client()
        response = c.get('/opds/')
        self.assertEquals(response.status_code, 200)
        response = c.get(reverse('opds:main'));
        self.assertEquals(response.status_code, 200)
        self.assertIn(_('By catalogs'), response.content.decode())
        self.assertIn(_("Catalogs: %(catalogs)s, books: %(books)s.")%{"catalogs":2, "books":4}, response.content.decode())
        self.assertIn(_("Authors: %(authors)s.")%{"authors":4}, response.content.decode())
        self.assertIn(_("Genres: %(genres)s.")%{"genres":4}, response.content.decode())
            
    def test_CatalogsFeed(self):
        c = Client()
        response = c.get('/opds/catalogs/')
        self.assertEquals(response.status_code, 200)
        response = c.get(reverse('opds:catalogs'));
        self.assertEquals(response.status_code, 200)  
        self.assertIn('books.zip', response.content.decode())
        self.assertIn('The Sanctuary Sparrow', response.content.decode())           
        
       
    def test_CatalogsFeedTree(self):
        c = Client()
        response = c.get('/opds/catalogs/12/')
        self.assertEquals(response.status_code, 200)
        response = c.get( reverse('opds:cat_tree',args=['12']) )
        self.assertEquals(response.status_code, 200) 
        self.assertIn('Драконьи Услуги', response.content.decode())     
        self.assertIn('Китайски сладкиш с късметче', response.content.decode())  
        self.assertIn('Любовь в жизни Обломова', response.content.decode())  
        
    def test_OpenSearch(self):
        c = Client()
        response = c.get('/opds/search/')
        self.assertEquals(response.status_code, 200)
        self.assertIn('www.sopds.ru', response.content.decode())
        
    def test_SearchTypes(self):
        c = Client()
        response = c.get('/opds/search/')
        self.assertEquals(response.status_code, 200)
        self.assertIn('www.sopds.ru', response.content.decode())
        
          