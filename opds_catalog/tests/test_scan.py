import os

from django.test import TestCase

from opds_catalog import opdsdb
from opds_catalog.sopdscan import opdsScanner
from opds_catalog import settings
from opds_catalog.models import Book, Catalog, Author, Genre, Series

class scanTestCase(TestCase):
    test_module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_ROOTLIB = os.path.join(test_module_path, 'tests/data')
    test_fb2 = "262001.fb2"
    test_zip = "books.zip"

    def setUp(self):
        settings.ROOT_LIB = self.test_ROOTLIB

    def test_processfile(self):
        """ Тестирование процедуры processfile (извлекает метаданные из книги и помещает в БД) """
        opdsdb.clear_all()
        scanner = opdsScanner()
        scanner.processfile(self.test_fb2, self.test_ROOTLIB, os.path.join(self.test_ROOTLIB,self.test_fb2), None,0,495373)
        book = Book.objects.get(filename=self.test_fb2)
        self.assertIsNotNone(book)
        self.assertEqual(scanner.books_added,1)
        self.assertEqual(book.filename, self.test_fb2)
        self.assertEqual(book.path, ".")
        self.assertEqual(book.format, "fb2")
        self.assertEqual(book.cat_type, 0)
        #self.assertGreaterEqual(book.registerdate, )
        self.assertEqual(book.docdate, "30.1.2011")
        self.assertEqual(book.favorite, 0)
        self.assertEqual(book.lang, "en")
        self.assertEqual(book.title, "The Sanctuary Sparrow")
        self.assertEqual(book.annotation, "")
        self.assertEqual(book.cover, "")
        self.assertEqual(book.cover_type, "")
        self.assertEqual(book.doublicat, 0)
        self.assertEqual(book.avail, 2)
        self.assertEqual(book.catalog.path, ".")
        self.assertEqual(book.catalog.cat_name, ".")
        self.assertEqual(book.catalog.cat_type, 0)
        self.assertEqual(book.filesize, 495373)

        self.assertEqual(book.authors.count(), 1)
        self.assertEqual(book.authors.get(last_name="Peters").first_name, "Ellis")

        self.assertEqual(book.genres.count(), 1)
        self.assertEqual(book.genres.get(genre="antique").section, opdsdb.unknown_genre)
        self.assertEqual(book.genres.get(genre="antique").subsection, "antique")

    def test_processzip(self):
        """ Тестирование процедуры processzip (извлекает метаданные из книг, помещенных в архив и помещает их БД) """
        opdsdb.clear_all()
        scanner = opdsScanner()
        scanner.processzip(self.test_zip, self.test_ROOTLIB, os.path.join(self.test_ROOTLIB,self.test_zip) )
        self.assertEquals(scanner.books_added, 3)
        self.assertEquals(Book.objects.all().count(), 3)
        self.assertEquals(Catalog.objects.all().count(), 2)

        book = Book.objects.get(filename="539603.fb2")
        self.assertEqual(book.filesize, 15194)
        self.assertEqual(book.path, self.test_zip)
        self.assertEqual(book.cat_type, 1)
        self.assertEqual(book.catalog.path, self.test_zip)
        self.assertEqual(book.catalog.cat_name, self.test_zip)
        self.assertEqual(book.catalog.cat_type, 1)
        self.assertEqual(book.docdate, "130552595662030000")
        self.assertEqual(book.title, "Любовь в жизни Обломова")
        self.assertEqual(book.doublicat, 0)
        self.assertEqual(book.avail, 2)
        self.assertEqual(book.authors.count(), 1)
        self.assertEqual(book.authors.get(last_name="Логинов").first_name, "Святослав")
        self.assertEqual(book.genres.count(), 1)
        self.assertEqual(book.genres.get(genre="nonf_criticism").section, opdsdb.unknown_genre)
        self.assertEqual(book.genres.get(genre="nonf_criticism").subsection, "nonf_criticism")

        book = Book.objects.get(filename="539485.fb2")
        self.assertEqual(book.filesize, 12293)
        self.assertEqual(book.path, self.test_zip)
        self.assertEqual(book.cat_type, 1)
        self.assertEqual(book.title, "Китайски сладкиш с късметче")
        self.assertEqual(book.authors.get(last_name="Фрич").first_name, "Чарлз")

        book = Book.objects.get(filename="539273.fb2")
        self.assertEqual(book.filesize, 21722)
        self.assertEqual(book.path, self.test_zip)
        self.assertEqual(book.cat_type, 1)
        self.assertEqual(book.title, "Драконьи Услуги")
        self.assertEqual(book.authors.get(last_name="Куприянов").first_name, "Денис")

    def test_scanall(self):
        """ Тестирование процедуры scanall (извлекает метаданные из книг и помещает в БД) """
        opdsdb.clear_all()
        scanner = opdsScanner()
        scanner.scan_all()
        self.assertEquals(scanner.books_added, 4)
        self.assertEquals(scanner.bad_books, 1)
        self.assertEquals(Book.objects.all().count(), 4)
        self.assertEquals(Author.objects.all().count(), 4)
        self.assertEquals(Genre.objects.all().count(), 4)
        self.assertEquals(Series.objects.all().count(), 0)
        self.assertEquals(Catalog.objects.all().count(), 2)
