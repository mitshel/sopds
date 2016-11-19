from django.test import TestCase
from opds_catalog.models import Catalog, bseries

from opds_catalog import opdsdb

class opdsdbTestCase(TestCase):

    def setUp(self):
        opdsdb.clear_all()
        opdsdb.addcattree("root/child/subchild",opdsdb.CAT_NORMAL)
        book = opdsdb.addbook("testbook.fb2", "root/child",opdsdb.findcat("root/child"),".fb2","Test Book", "Annotation", "01.01.2016", "ru", 500, 0)
        opdsdb.addbauthor(book, opdsdb.addauthor("Test Author"))
        opdsdb.addbgenre(book, opdsdb.addgenre("fantastic"))
        opdsdb.addbseries(book, opdsdb.addseries("mywork"), 1)


    def test_cat_fn(self):
        """ Тестирование функций addcattree, findcat """
        self.assertEqual(Catalog.objects.filter(parent=None).count(), 1)
        self.assertEqual(Catalog.objects.all().count(), 4)

        cat = Catalog.objects.get(parent=None)
        self.assertEqual(cat.cat_name,".")
        cat = Catalog.objects.get(parent=cat)
        self.assertEqual(cat.cat_name, "root")
        cat = Catalog.objects.get(parent=cat)
        self.assertEqual(cat.cat_name, "child")
        cat = Catalog.objects.get(parent=cat)
        self.assertEqual(cat.cat_name, "subchild")

        cat = opdsdb.findcat("root/child")
        self.assertEqual(cat.cat_name, "child")
        self.assertEqual(cat.path, "root/child")
        self.assertEqual(cat.parent.cat_name, "root")
        self.assertEqual(cat.parent.parent.cat_name, ".")
        self.assertIsNone(cat.parent.parent.parent)

    def test_book_fn(self):
        """ Тестирование функций addbook, findbook """
        book = opdsdb.findbook("testbook.fb2","root/child")
        self.assertIsNotNone(book)
        self.assertEqual(book.filename,"testbook.fb2")
        self.assertEqual(book.path, "root/child")
        self.assertEqual(book.catalog.cat_name, "child")
        self.assertEqual(book.catalog.cat_type, 0)
        self.assertEqual(book.format, ".fb2")
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.annotation, "Annotation")
        self.assertEqual(book.docdate, "01.01.2016")
        self.assertEqual(book.lang, "ru")
        self.assertEqual(book.filesize, 500)
        self.assertEqual(book.cat_type, 0)

    def test_author_fn(self):
        """ Тестирование функций addauthor, addbauthor """
        book = opdsdb.findbook("testbook.fb2", "root/child")
        self.assertEqual(book.authors.count(), 1)
        self.assertEqual(book.authors.get(full_name="Test Author").search_full_name, "TEST AUTHOR")

    def test_genre_fn(self):
        """ Тестирование функций addgenre, addbgenre """
        book = opdsdb.findbook("testbook.fb2", "root/child")
        self.assertEqual(book.genres.count(), 1)
        self.assertEqual(book.genres.get(genre="fantastic").section, opdsdb.unknown_genre)
        self.assertEqual(book.genres.get(genre="fantastic").subsection, "fantastic")

    def test_series_fn(self):
        """ Тестирование функций addseries, addbseries """
        book = opdsdb.findbook("testbook.fb2", "root/child")
        self.assertEqual(book.series.count(), 1)
        ser = book.series.all()[0]
        self.assertEqual(ser.ser, "mywork")
        self.assertEqual(bseries.objects.get(ser=ser).ser_no, 1)
