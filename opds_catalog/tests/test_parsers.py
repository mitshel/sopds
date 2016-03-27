import os

from django.test import TestCase

from opds_catalog.fb2parse import fb2parser

class scanTestCase(TestCase):
    test_module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_ROOTLIB = os.path.join(test_module_path, 'tests/data')
    test_fb2 = "262001.fb2"
    test_bad_fb2 = "badfile.fb2"

    def setUp(self):
        pass

    def test_fb2parse_valid(self):
        """ Тестирование класса fb2parser валидного fb2 """
        parser = fb2parser()
        parser.reset()
        f = open(os.path.join(self.test_ROOTLIB, self.test_fb2), 'rb')
        parser.parse(f)
        self.assertEquals(parser.book_title.getvalue()[0], "The Sanctuary Sparrow")
        self.assertEquals(parser.author_first.getvalue()[0], "Ellis")
        self.assertEquals(parser.author_last.getvalue()[0], "Peters")
        self.assertEquals(parser.genre.getvalue()[0], "antique")
        self.assertEquals(parser.lang.getvalue()[0], "en")
        self.assertEquals(parser.docdate.getvalue()[0], "30.1.2011")
        self.assertEquals(parser.parse_error, 0)

    def test_fb2parse_novalid(self):
        """ Тестирование класса fb2parser валидного fb2 """
        parser = fb2parser()
        parser.reset()
        f = open(os.path.join(self.test_ROOTLIB, self.test_bad_fb2), 'rb')
        parser.parse(f)
        self.assertNotEquals(parser.parse_error, 0)

