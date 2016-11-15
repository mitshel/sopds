from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _

counter_allbooks = 'allbooks'
counter_allcatalogs = 'allcatalogs'
counter_allauthors = 'allauthors'
counter_allgenres = 'allgenres'
counter_allseries = 'allseries'

LangCodes = {1:'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯабвгдеёжзийклмнопрстуфхцчшщьыъэюя',
             2:'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
             3:'0123456789'}
lang_menu = {1:_('Cyrillic'), 2:_('Latin'), 3:_('Digits'), 9:_('Other symbols'), 0:_('Show all')}

class Book(models.Model):
    filename = models.CharField(db_index=True, max_length=256)
    path = models.CharField(db_index=True, max_length=1000)
    filesize = models.IntegerField(null=False, default=0, db_index=True)
    format = models.CharField(max_length=8, db_index=True)
    catalog = models.ForeignKey('Catalog',db_index=True)
    cat_type = models.IntegerField(null=False, default=0)
    registerdate = models.DateTimeField(db_index=True, null=False, default=timezone.now)
    docdate = models.CharField(max_length=32)
    #favorite = models.IntegerField(null=False, default=0)
    lang = models.CharField(max_length=16)
    title = models.CharField(max_length=256, db_index=True)
    search_title = models.CharField(max_length=256, default=None, db_index=True)
    annotation = models.CharField(max_length=10000)
    lang_code = models.IntegerField(db_index=True, null=False, default=9)
    avail = models.IntegerField(null=False, default=0, db_index=True)
    authors = models.ManyToManyField('Author', through='bauthor')
    genres = models.ManyToManyField('Genre', through='bgenre')
    series = models.ManyToManyField('Series', through='bseries')

#    class Meta:
#        index_together = [
#            ["title", "format", "filesize"]
#        ]

class Catalog(models.Model):
    parent = models.ForeignKey('self', null=True, db_index=True)
    cat_name = models.CharField(db_index=True, max_length=128)
    path = models.CharField(db_index=True, max_length=1000)
    cat_type = models.IntegerField(null=False, default=0)
    cat_size = models.BigIntegerField(null=True, default=0)

class Author(models.Model):
    full_name = models.CharField(db_index=True, max_length=128, default=None)
    search_full_name = models.CharField(db_index=True, max_length=128, default=None)
    lang_code = models.IntegerField(db_index=True, null=False, default=9)


class bauthor(models.Model):
    book = models.ForeignKey('Book', db_index=True)
    author = models.ForeignKey('Author', db_index=True)
#    class Meta:
#        index_together = [
#            ["book", "author"],
#        ]

class Genre(models.Model):
    genre = models.CharField(db_index=True, max_length=32)
    section = models.CharField(db_index=True, max_length=64)
    subsection = models.CharField(db_index=True, max_length=100)

class bgenre(models.Model):
    book = models.ForeignKey('Book', db_index=True)
    genre = models.ForeignKey('Genre', db_index=True)
#    class Meta:
#        index_together = [
#            ["book", "genre"],
#        ]

class Series(models.Model):
    ser = models.CharField(db_index=True, max_length=80)
    search_ser = models.CharField(db_index=True, max_length=80, default=None)
    lang_code = models.IntegerField(db_index=True, null=False, default=9)

class bseries(models.Model):
    book = models.ForeignKey('Book', db_index=True)
    ser = models.ForeignKey('Series', db_index=True)
    ser_no = models.IntegerField(null=False, default=0)
#    class Meta:
#        index_together = [
#            ["book", "ser"],
#        ]

class bookshelf(models.Model):
    user = models.ForeignKey(User, db_index=True)
    book = models.ForeignKey(Book, db_index=True)
    readtime = models.DateTimeField(null=False, default=timezone.now)


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

class Counter(models.Model):
    name = models.CharField(primary_key=True, null=False, blank=False, max_length=16)
    value = models.IntegerField(null=False, default=0)
    update_time = models.DateTimeField(null=False, default=timezone.now)
    obj = models.Manager()
    objects = CounterManager()



