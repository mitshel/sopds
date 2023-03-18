from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _lazy

counter_allbooks = 'allbooks'
counter_allcatalogs = 'allcatalogs'
counter_allauthors = 'allauthors'
counter_allgenres = 'allgenres'
counter_allseries = 'allseries'

SIZE_BOOK_FILENAME   = 512
SIZE_BOOK_PATH       = 512
SIZE_BOOK_FORMAT     = 8
SIZE_BOOK_DOCDATE    = 32
SIZE_BOOK_LANG       = 16
SIZE_BOOK_TITLE      = 512
SIZE_BOOK_ANNOTATION = 10000

SIZE_CAT_CATNAME     = 190
SIZE_CAT_PATH        = SIZE_BOOK_PATH

SIZE_AUTHOR_NAME     = 128

SIZE_GENRE           = 32
SIZE_GENRE_SECTION   = 64
SIZE_GENRE_SUBSECTION = 100

SIZE_SERIES          = 150


LangCodes = {1:'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯабвгдеёжзийклмнопрстуфхцчшщьыъэюя',
             2:'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
             3:'0123456789'}
lang_menu = {1:_lazy('Cyrillic'), 2:_lazy('Latin'), 3:_lazy('Digits'), 9:_lazy('Other symbols'), 0:_lazy('Show all')}

class Book(models.Model):
    filename = models.CharField(max_length=SIZE_BOOK_FILENAME,db_index=True)
    path = models.CharField(max_length=SIZE_BOOK_PATH,db_index=True)
    filesize = models.IntegerField(null=False, default=0)
    format = models.CharField(max_length=SIZE_BOOK_FORMAT)
    catalog = models.ForeignKey('Catalog',db_index=True, on_delete=models.CASCADE)
    cat_type = models.IntegerField(null=False, default=0)
    registerdate = models.DateTimeField(null=False, default=timezone.now)
    docdate = models.CharField(max_length=SIZE_BOOK_DOCDATE,db_index=True)
    #favorite = models.IntegerField(null=False, default=0)
    lang = models.CharField(max_length=SIZE_BOOK_LANG)
    title = models.CharField(max_length=SIZE_BOOK_TITLE, db_index=True)
    search_title = models.CharField(max_length=SIZE_BOOK_TITLE, default=None, db_index=True)
    annotation = models.CharField(max_length=SIZE_BOOK_ANNOTATION)
    lang_code = models.IntegerField(null=False, default=9, db_index=True)
    avail = models.IntegerField(null=False, default=0, db_index=True)
    authors = models.ManyToManyField('Author', through='bauthor')
    genres = models.ManyToManyField('Genre', through='bgenre')
    series = models.ManyToManyField('Series', through='bseries')  

class Catalog(models.Model):
    parent = models.ForeignKey('self', null=True, db_index=True, on_delete=models.CASCADE)
    cat_name = models.CharField(max_length=SIZE_CAT_CATNAME, db_index=True)
    path = models.CharField(max_length=SIZE_CAT_PATH, db_index=True)
    cat_type = models.IntegerField(null=False, default=0)
    cat_size = models.BigIntegerField(null=True, default=0)

class Author(models.Model):
    full_name = models.CharField(max_length=SIZE_AUTHOR_NAME, default=None, db_index=True)
    search_full_name = models.CharField(max_length=SIZE_AUTHOR_NAME, default=None, db_index=True)
    lang_code = models.IntegerField(null=False, default=9, db_index=True)


class bauthor(models.Model):
    book = models.ForeignKey('Book', db_index=True, on_delete=models.CASCADE)
    author = models.ForeignKey('Author', db_index=True, on_delete=models.CASCADE)
#    class Meta:
#        index_together = [
#            ["book", "author"],
#        ]

class Genre(models.Model):
    genre = models.CharField(max_length=SIZE_GENRE, db_index=True)
    section = models.CharField(max_length=SIZE_GENRE_SECTION, db_index=True)
    subsection = models.CharField(max_length=SIZE_GENRE_SUBSECTION, db_index=True)

class bgenre(models.Model):
    book = models.ForeignKey('Book', db_index=True, on_delete=models.CASCADE)
    genre = models.ForeignKey('Genre', db_index=True, on_delete=models.CASCADE)

class Series(models.Model):
    ser = models.CharField(max_length=SIZE_SERIES, db_index=True)
    search_ser = models.CharField(max_length=SIZE_SERIES, default=None, db_index=True)
    lang_code = models.IntegerField(null=False, default=9,db_index=True)

class bseries(models.Model):
    book = models.ForeignKey('Book', db_index=True, on_delete=models.CASCADE)
    ser = models.ForeignKey('Series', db_index=True, on_delete=models.CASCADE)
    ser_no = models.IntegerField(null=False, default=0)
#    class Meta:
#        index_together = [
#            ["book", "ser"],
#        ]

class bookshelf(models.Model):
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, db_index=True, on_delete=models.CASCADE)
    readtime = models.DateTimeField(null=False, default=timezone.now, db_index=True)


class CounterManager(models.Manager):
    def update(self, counter_name, counter_value):
        self.update_or_create(name=counter_name, defaults = {"value":counter_value, "update_time":timezone.now()})

    def update_known_counters(self):
        self.update(counter_allbooks, Book.objects.all().count())
        self.update(counter_allcatalogs, Catalog.objects.all().count())
        self.update(counter_allauthors, Author.objects.all().count())
        self.update(counter_allgenres, Genre.objects.all().count())
        self.update(counter_allseries, Series.objects.all().count())

    def get_counter(self, counter_name):
        try:
            counter = self.get(name=counter_name).value
        except ObjectDoesNotExist:
            counter = 0
            
        return counter

    def get_lastscan(self):
        try:
            lastscan = self.get(name='allbooks').update_time
        except ObjectDoesNotExist:
            lastscan = None

        return lastscan

class Counter(models.Model):
    name = models.CharField(primary_key=True, null=False, blank=False, max_length=16)
    value = models.IntegerField(null=False, default=0)
    update_time = models.DateTimeField(null=False, default=timezone.now)
    obj = models.Manager()
    objects = CounterManager()
    

