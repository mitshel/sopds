from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

counter_allbooks = 'allbooks'
counter_allcatalogs = 'allcatalogs'
counter_allauthors = 'allauthors'
counter_allgenres = 'allgenres'
counter_allseries = 'allseries'

LangCodes = {1:'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ',
             2:'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
             3:'0123456789'}

class Book(models.Model):
    filename = models.CharField(db_index=True, max_length=256)
    path = models.CharField(db_index=True, max_length=1024)
    filesize = models.IntegerField(null=False, default=0)
    format = models.CharField(max_length=8)
    catalog = models.ForeignKey('Catalog',db_index=True)
    cat_type = models.IntegerField(null=False, default=0)
    registerdate = models.DateTimeField(db_index=True, null=False, default=timezone.now)
    docdate = models.CharField(max_length=20)
    #favorite = models.IntegerField(null=False, default=0)
    lang = models.CharField(max_length=16)
    title = models.CharField(max_length=256)
    annotation = models.CharField(max_length=10000)
    #cover = models.CharField(max_length=32)
    #cover_type = models.CharField(max_length=32)
    #doublicat = models.IntegerField(null=False, default=0)
    lang_code = models.IntegerField(db_index=True, null=False, default=9)
    avail = models.IntegerField(null=False, default=0)
    authors = models.ManyToManyField('Author', through='bauthor')
    genres = models.ManyToManyField('Genre', through='bgenre')
    series = models.ManyToManyField('Series', through='bseries')

    class Meta:
        index_together = [
            ["title", "format", "filesize"],
            ["avail"],
        ]

class Catalog(models.Model):
    parent = models.ForeignKey('self', null=True)
    cat_name = models.CharField(max_length=64)
    path = models.CharField(max_length=1024)
    cat_type = models.IntegerField(null=False, default=0)

    class Meta:
        index_together = [
            ["cat_name", "path"],
        ]

class Author(models.Model):
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    lang_code = models.IntegerField(db_index=True, null=False, default=9)

    class Meta:
        index_together = [
            ["last_name", "first_name"],
        ]

class bauthor(models.Model):
    book = models.ForeignKey('Book')
    author = models.ForeignKey('Author')
    class Meta:
        index_together = [
            ["book", "author"],
        ]

class Genre(models.Model):
    genre = models.CharField(db_index=True, max_length=32)
    section = models.CharField(max_length=64)
    subsection = models.CharField(max_length=100)

class bgenre(models.Model):
    book = models.ForeignKey('Book')
    genre = models.ForeignKey('Genre')

    class Meta:
        index_together = [
            ["book", "genre"],
        ]

class Series(models.Model):
    ser = models.CharField(db_index=True, max_length=64)
    lang_code = models.IntegerField(db_index=True, null=False, default=9)

class bseries(models.Model):
    book = models.ForeignKey('Book')
    ser = models.ForeignKey('Series')
    ser_no = models.IntegerField(null=False, default=0)

    class Meta:
        index_together = [
            ["book", "ser"],
        ]

class bookshelf(models.Model):
    user = models.ForeignKey(User)
    book = models.ForeignKey(Book)
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



