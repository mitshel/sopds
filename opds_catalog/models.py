from django.db import models
from django import utils
from django.contrib.auth.models import User


class Book(models.Model):
    filename = models.CharField(max_length=256)
    path = models.CharField(max_length=1024)
    filesize = models.IntegerField(null=False, default=0)
    format = models.CharField(max_length=8)
    cat_id = models.ForeignKey('Catalog')
    cat_type = models.IntegerField(null=False, default=0)
    registerdate = models.DateTimeField(null=False, default=utils.timezone.now)
    docdate = models.CharField(max_length=20)
    favorite = models.IntegerField(null=False, default=0)
    lang = models.CharField(max_length=16)
    title = models.CharField(max_length=256)
    annotation = models.CharField(max_length=10000)
    cover = models.CharField(max_length=32)
    cover_type = models.CharField(max_length=32)
    doublicat = models.IntegerField(null=False, default=0)
    avail = models.IntegerField(null=False, default=0)
    author = models.ManyToManyField('Author')
    genre = models.ManyToManyField('Genre')
    series = models.ManyToManyField('Series', through='bseries')

class Catalog(models.Model):
    parent = models.ForeignKey('self', null=True)
    cat_name = models.CharField(max_length=64)
    path = models.CharField(max_length=1024)
    cat_type = models.IntegerField(null=False, default=0)

class Author(models.Model):
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)

class Genre(models.Model):
    genre = models.CharField(max_length=32)
    section = models.CharField(max_length=64)
    subsection = models.CharField(max_length=100)

class Series(models.Model):
    ser = models.CharField(max_length=64)

class bseries(models.Model):
    book = models.ForeignKey(Book)
    series = models.ForeignKey(Series)
    ser_no = models.IntegerField(null=False, default=0)

class bookshelf(models.Model):
    user = models.ForeignKey(User)
    book = models.ForeignKey(Book)
    readtime = models.DateTimeField(null=False, default=utils.timezone.now)
