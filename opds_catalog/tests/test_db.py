from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from opds_catalog.models import Book, Catalog, Author, Genre, Series, bookshelf, Counter, bauthor, bgenre, bseries
from opds_catalog import models

class DBStructTestCase(TestCase):
    def setUp(self):
        book = Book.objects.create(filename="testbook.fb2", path=".", filesize=500, format="fb2", cat_type=0, registerdate=timezone.now(),
                            docdate="01.01.2016", favorite=0, lang="ru", title="Книга", annotation="Аннотация", cover="", cover_type="",
                            doublicat=0, avail=2,
                            catalog=Catalog.objects.create(parent=None, cat_name=".", path=".", cat_type=0)
        )
        author = Author.objects.create(first_name="Дмитрий", last_name="Шелепнев")
        genre = Genre.objects.create(genre="fantastic0", section="fantastic1", subsection="fantastic2")
        series = Series.objects.create(ser="mywork")
        ba = bauthor.objects.create(book=book, author=author)
        bg = bgenre.objects.create(book=book, genre=genre)
        bs = bseries.objects.create(book=book, ser=series, ser_no=1)
#        bshelf = bookshelf.objects.create(user=AnonymousUser, book=book, readtime=timezone.now())
        Counter.objects.update_known_counters()

    def test_Book(self):
        """ Тестирование соответствия структуры модели Book и работоспособности БД """
        book = Book.objects.get(title="Книга")
        self.assertEqual(book.filename, "testbook.fb2")
        self.assertEqual(book.path, ".")
        self.assertEqual(book.filesize, 500)
        self.assertEqual(book.format, "fb2")
        self.assertEqual(book.cat_type, 0)
#        self.assertEqual(book.registerdate, "testbook.fb2")
        self.assertEqual(book.docdate, "01.01.2016")
        self.assertEqual(book.favorite, 0)
        self.assertEqual(book.lang, "ru")
        self.assertEqual(book.title, "Книга")
        self.assertEqual(book.annotation, "Аннотация")
        self.assertEqual(book.cover, "")
        self.assertEqual(book.cover_type, "")
        self.assertEqual(book.doublicat, 0)
        self.assertEqual(book.avail, 2)
        self.assertEqual(book.catalog.path, ".")
        self.assertEqual(book.catalog.cat_name, ".")
        self.assertEqual(book.catalog.cat_type, 0)

    def test_Author(self):
        """ Тестирование соответствия структуры моделей Author и bauthor и работоспособности БД """
        book = Book.objects.get(title="Книга")
        self.assertEqual(book.authors.count(), 1)
        self.assertEqual(book.authors.get(last_name="Шелепнев").first_name, "Дмитрий")


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
        self.assertEqual(bseries.objects.get(ser=ser).ser_no, 1)

    def test_Counter(self):
        """ Тестирование соответствия структуры модели Counter, менеджера CounterManager и работоспособности БД """
        self.assertEqual(Counter.objects.get_counter(models.counter_allbooks), 1)
        self.assertEqual(Counter.objects.get_counter(models.counter_allauthors), 1)
        self.assertEqual(Counter.objects.get_counter(models.counter_allcatalogs), 1)
        self.assertEqual(Counter.objects.get_counter(models.counter_allgenres), 1)
        self.assertEqual(Counter.objects.get_counter(models.counter_allseries), 1)
