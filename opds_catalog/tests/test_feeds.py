# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.utils.translation import ugettext as _


class feedsTestCase(TestCase):
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
        response = c.get('/opds/search/Драк/')
        self.assertEquals(response.status_code, 200)
        response = c.get(reverse('opds:searchtypes', kwargs={'searchterms':'Драк'}))
        self.assertEquals(response.status_code, 200)
        self.assertIn(_("Search by titles"), response.content.decode())
        
    def test_SearchBooks(self):
        c = Client()        
        response = c.get('/opds/search/books/Драк/')
        self.assertEquals(response.status_code, 200)
        response = c.get(reverse('opds:searchbooks', kwargs={'searchtype':'books','searchterms':'рак'}))
        self.assertEquals(response.status_code, 200)        
        self.assertIn("Драконьи Услуги", response.content.decode())
        self.assertIn("Куприянов Денис", response.content.decode())
        response = c.get(reverse('opds:searchbooks', kwargs={'searchtype':'sbooks','searchterms':'Драк'}))
        self.assertEquals(response.status_code, 200)        
        self.assertIn("Драконьи Услуги", response.content.decode())
        self.assertIn("Куприянов Денис", response.content.decode())   
        response = c.get(reverse('opds:searchbooks', kwargs={'searchtype':'abooks','searchterms':'1034'}))
        self.assertEquals(response.status_code, 200)        
        self.assertIn("Драконьи Услуги", response.content.decode())
        self.assertIn("Куприянов Денис", response.content.decode())  
        self.assertIn("All books by Куприянов Денис", response.content.decode())  
        self.assertIn("prose_contemporary", response.content.decode())    
        self.assertIn("<category term", response.content.decode()) 
    
    def test_SearchAuthors(self):
        c = Client()                
        response = c.get('/opds/search/authors/Логинов/')
        self.assertEquals(response.status_code, 200)
        response = c.get(reverse('opds:searchauthors', kwargs={'searchtype':'authors','searchterms':'гинов'}))
        self.assertEquals(response.status_code, 200)        
        self.assertIn("Логинов Святослав", response.content.decode())     
        response = c.get(reverse('opds:searchauthors', kwargs={'searchtype':'sauthors','searchterms':'Лог'}))
        self.assertEquals(response.status_code, 200)        
        self.assertIn("Логинов Святослав", response.content.decode())         

    def test_SearchGenres(self):        
        #response = c.get('/opds/search/genres/antiq/')
        #self.assertEquals(response.status_code, 200)
        #self.assertIn("The Sanctuary Sparrow", response.content.decode())
        #self.assertIn("Peters Ellis", response.content.decode())  
        pass  

    def test_LangFeed(self):
        c = Client()
        response = c.get('/opds/books/')
        self.assertEquals(response.status_code, 200)
        response = c.get(reverse('opds:lang_books'));
        self.assertEquals(response.status_code, 200)
        self.assertIn(_("Cyrillic"), response.content.decode())
        self.assertIn(_("Latin"), response.content.decode())
        self.assertIn(_("Digits"), response.content.decode())
        self.assertIn(_("Other symbols"), response.content.decode())  
        self.assertIn(_("Show all"), response.content.decode())           
     
    def test_BooksFeed(self):
        c = Client()
        response = c.get('/opds/books/0/')
        self.assertEquals(response.status_code, 200)
        response = c.get(reverse('opds:char_books', kwargs={'lang_code':0}));
        self.assertEquals(response.status_code, 200)
#        self.assertIn(_("Cyrillic"), response.content.decode()) 

    def test_AuthorsFeed(self):
        c = Client()
        response = c.get('/opds/authors/0/')
        self.assertEquals(response.status_code, 200)
        response = c.get(reverse('opds:char_authors', kwargs={'lang_code':0}));
        self.assertEquals(response.status_code, 200)
#        self.assertIn(_("Cyrillic"), response.content.decode())      