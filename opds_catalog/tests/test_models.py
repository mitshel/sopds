from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings as main_settings

from opds_catalog.models import Book, Catalog, Author, Genre, Series, bookshelf, Counter, bauthor, bgenre, bseries
from opds_catalog import models
from opds_catalog import opdsdb

class modelsTestCase(TestCase):
    testdatetime = datetime(2016, 1, 1, 0, 0)
    if main_settings.USE_TZ:
        testdatetime = testdatetime.replace(tzinfo=timezone.get_current_timezone())

    def setUp(self):
        opdsdb.clear_all()
        book = Book.objects.create(filename="testbook.fb2", path=".", filesize=500, format="fb2", cat_type=0, 
                            registerdate=self.testdatetime,docdate="01.01.2016", lang="ru", title="Книга", search_title="КНИГА", 
                            annotation="Аннотация", avail=2,catalog=Catalog.objects.create(parent=None, cat_name=".", path=".", cat_type=0)
        )
        author = Author.objects.create(full_name="Шелепнев Дмитрий", search_full_name="ШЕЛЕПНЕВ ДМИТРИЙ")
        genre = Genre.objects.create(genre="fantastic0", section="fantastic1", subsection="fantastic2")
        series = Series.objects.create(ser="mywork", search_ser="MYWORK")
        bauthor.objects.create(book=book, author=author)
        bgenre.objects.create(book=book, genre=genre)
        bseries.objects.create(book=book, ser=series, ser_no=1)
        user = User.objects.create_user("testuser","testuser@sopds.ru", "testpassword", first_name="Test", last_name="User")
        bookshelf.objects.create(user=user, book=book, readtime=self.testdatetime)
        Counter.objects.update_known_counters()


    def test_Book(self):
        """ Тестирование соответствия структуры модели Book и работоспособности БД """
        book = Book.objects.get(title="Книга")
        self.assertEqual(book.filename, "testbook.fb2")
        self.assertEqual(book.path, ".")
        self.assertEqual(book.filesize, 500)
        self.assertEqual(book.format, "fb2")
        self.assertEqual(book.cat_type, 0)
        self.assertEqual(book.registerdate, self.testdatetime)
        self.assertEqual(book.docdate, "01.01.2016")
        self.assertEqual(book.lang, "ru")
        self.assertEqual(book.title, "Книга")
        self.assertEqual(book.search_title, "КНИГА")
        self.assertEqual(book.annotation, "Аннотация")
        self.assertEqual(book.avail, 2)
        self.assertEqual(book.catalog.path, ".")
        self.assertEqual(book.catalog.cat_name, ".")
        self.assertEqual(book.catalog.cat_type, 0)

    def test_Author(self):
        """ Тестирование соответствия структуры моделей Author и bauthor и работоспособности БД """
        book = Book.objects.get(title="Книга")
        self.assertEqual(book.authors.count(), 1)
        self.assertEqual(book.authors.get(full_name="Шелепнев Дмитрий").search_full_name, "ШЕЛЕПНЕВ ДМИТРИЙ")

    def test_Genre(self):
        """ Тестирование соответствия структуры моделей Genre и bgenre и работоспособности БД """
        book = Book.objects.get(title="Книга")
        self.assertEqual(book.genres.count(), 1)
        self.assertEqual(book.genres.get(genre="fantastic0").section, "fantastic1")
        self.assertEqual(book.genres.get(genre="fantastic0").subsection, "fantastic2")

    def test_Series(self):
        """ Тестирование соответствия структуры моделей Series и bseries и работоспособности БД """
        book = Book.objects.get(title="Книга")
        self.assertEqual(book.series.count(), 1)
        ser = book.series.all()[0]
        self.assertEqual(ser.ser,"mywork")
        self.assertEqual(ser.search_ser,"MYWORK")
        self.assertEqual(bseries.objects.get(ser=ser).ser_no, 1)

    def test_bookshelf(self):
        """ Тестирование соответствия структуры модели bookshelf и работоспособности БД """
        user = User.objects.get(username="testuser")
        self.assertEqual(bookshelf.objects.all().count(), 1)
        self.assertEqual(bookshelf.objects.filter(user=user).count(), 1)
        self.assertEqual(bookshelf.objects.get(user=user).book.title, "Книга")

    def test_Counter(self):
        """ Тестирование соответствия структуры модели Counter, менеджера CounterManager и работоспособности БД """
        self.assertEqual(Counter.objects.get_counter(models.counter_allbooks), 1)
        self.assertEqual(Counter.objects.get_counter(models.counter_allauthors), 1)
        self.assertEqual(Counter.objects.get_counter(models.counter_allcatalogs), 1)
        self.assertEqual(Counter.objects.get_counter(models.counter_allgenres), 1)
        self.assertEqual(Counter.objects.get_counter(models.counter_allseries), 1)
