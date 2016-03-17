from django.db import models, connection
from django import utils
from django.contrib.auth.models import User


class Book(models.Model):
    filename = models.CharField(db_index=True, max_length=256)
    path = models.CharField(db_index=True, max_length=1024)
    filesize = models.IntegerField(null=False, default=0)
    format = models.CharField(max_length=8)
    catalog = models.ForeignKey('Catalog',db_index=True)
    cat_type = models.IntegerField(null=False, default=0)
    registerdate = models.DateTimeField(db_index=True, null=False, default=utils.timezone.now)
    docdate = models.CharField(max_length=20)
    favorite = models.IntegerField(null=False, default=0)
    lang = models.CharField(max_length=16)
    title = models.CharField(max_length=256)
    annotation = models.CharField(max_length=10000)
    cover = models.CharField(max_length=32)
    cover_type = models.CharField(max_length=32)
    doublicat = models.IntegerField(null=False, default=0)
    avail = models.IntegerField(null=False, default=0)
    authors = models.ManyToManyField('Author', through='bauthor')
    genres = models.ManyToManyField('Genre', through='bgenre')
    series = models.ManyToManyField('Series', through='bseries')

    class Meta:
        index_together = [
            ["title", "format", "filesize"],
            ["avail", "doublicat"],
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

    class Meta:
        index_together = [
            ["last_name", "first_name"],
        ]

class bauthor(models.Model):
    book = models.ForeignKey(Book)
    author = models.ForeignKey(Author)
    class Meta:
        index_together = [
            ["book", "author"],
        ]

class Genre(models.Model):
    genre = models.CharField(db_index=True, max_length=32)
    section = models.CharField(max_length=64)
    subsection = models.CharField(max_length=100)

class bgenre(models.Model):
    book = models.ForeignKey(Book)
    genre = models.ForeignKey(Genre)

    class Meta:
        index_together = [
            ["book", "genre"],
        ]

class Series(models.Model):
    ser = models.CharField(db_index=True, max_length=64)

class bseries(models.Model):
    book = models.ForeignKey(Book)
    ser = models.ForeignKey(Series)
    ser_no = models.IntegerField(null=False, default=0)

    class Meta:
        index_together = [
            ["book", "ser"],
        ]

class bookshelf(models.Model):
    user = models.ForeignKey(User)
    book = models.ForeignKey(Book)
    readtime = models.DateTimeField(null=False, default=utils.timezone.now)

class Catalog_Book_Serialiser(models.Model):
    pass
#    query = 'select 1 as t,cat_id,cat_name,path,now(),cat_name as title,'' as docdate,'' as annotation,'cat' as format, 0 as filesize, '' as cover, '' as cover_type from "+TBL_CATALOGS+" where parent_id="+str(cat_id)+" union all "
#    "select 2,book_id,filename,path,registerdate,title,annotation,docdate,format,filesize,cover,cover_type from "+TBL_BOOKS+" where cat_id="+str(cat_id)+" and avail!=0 order by 1,6 "+limitstr)

