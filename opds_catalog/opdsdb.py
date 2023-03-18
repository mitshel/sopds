# -*- coding: utf-8 -*-

import os
import re

from django.db.models import Q
from django.utils.translation import gettext as _ , gettext_noop as _noop
from django.db import transaction, connection

from opds_catalog.models import Book, Catalog, Author, Genre, Series, bseries, bauthor, bgenre, bookshelf, Counter, LangCodes
from opds_catalog.models import SIZE_BOOK_FILENAME, SIZE_BOOK_PATH, SIZE_BOOK_FORMAT, SIZE_BOOK_DOCDATE, SIZE_BOOK_LANG, SIZE_BOOK_TITLE, SIZE_BOOK_ANNOTATION
from opds_catalog.models import SIZE_CAT_CATNAME, SIZE_CAT_PATH, SIZE_AUTHOR_NAME, SIZE_GENRE, SIZE_GENRE_SECTION, SIZE_GENRE_SUBSECTION, SIZE_SERIES


##########################################################################
# типы каталогов (cat_type)
#
CAT_NORMAL=0
CAT_ZIP=1
CAT_INPX=2
CAT_INP=3

##########################################################################
# Как будем искать дубликаты
#
CMP_NONE=0
CMP_NORMAL=1
CMP_STRONG=2
CMP_CLEAR=3
CMP_TITLE_FTYPE_FSIZE=2
CMP_TITLE_AUTHORS=1

##########################################################################
# разные константы
#
unknown_genre_en =_noop('Unknown genre') 
unknown_genre=_(unknown_genre_en)

##########################################################################
# объект который мы будем использовать для перекодироки 4х байтного UTF в 3х байтный
# пока только для аннотации, т.к. там уже "словлена" ошибка при записи в 3х байтный utf8 MYSQL
#
utfhigh = re.compile(u'[\U00010000-\U0010ffff]')

def pg_optimize(verbose=False):
    """ TODO: Table optimizations for Postgre """
    if connection.vendor != 'postgresql':
        if verbose:
            print('No PostgreSql connection backend detected...')
    else:
        print('Start PostgreSql tables optimization...')
        cursor = connection.cursor()
        cursor.execute('alter table opds_catalog_book SET ( fillfactor = 50)')
        cursor.execute('VACUUM FULL opds_catalog_book')
        print('PostgreSql tables internal structure optimized...')

def clear_all(verbose=False):
    cursor = connection.cursor()
    cursor.execute('delete from opds_catalog_bseries')
    cursor.execute('delete from opds_catalog_bauthor')
    cursor.execute('delete from opds_catalog_bgenre')
    cursor.execute('delete from opds_catalog_bookshelf')
    cursor.execute('delete from opds_catalog_book')
    cursor.execute('delete from opds_catalog_catalog')
    cursor.execute('delete from opds_catalog_author')
    cursor.execute('delete from opds_catalog_genre')
    cursor.execute('delete from opds_catalog_series')
    cursor.execute('delete from opds_catalog_counter')
    
def clear_genres(verbose=False):
    cursor = connection.cursor()
    cursor.execute('delete from opds_catalog_genre')

# Книги где avail=0 уже известно что удалены
# Книги где avail=2 это только что прверенные существующие книги
# Устанавливаем avail=1 для книг которые не удалены. Во время проверки
# если они не удалены им присвоится значение 2
# Книги с avail=0 проверятся не будут и будут убраны из всех выдач и всех обработок.
#
# три позиции (0,1,2) сделаны для того чтобы сделать возможным корректную работу
# cgi-скрипта во время сканирования библиотеки
#

def p(s,size):
    new = utfhigh.sub(u'',s[:size])
    return new
    
def getlangcode(s):
    langcode = 9
    if len(s)==0:
        return langcode 
    for k in LangCodes.keys():
        if s[0] in LangCodes[k]:
            langcode = k
    
    return langcode
    
def avail_check_prepare():
    Book.objects.filter(~Q(avail=0)).update(avail=1)

def books_del_logical():
    row_count = Book.objects.filter(avail=1).update(avail=0)
    return row_count

def books_del_phisical():
    row_count = Book.objects.filter(avail__lte=1).delete()
    # TODO: Разобратся нужно ли удалять записи в таблицах связи ManyToMany или они сами удалятся?
    # sql='delete from '+TBL_BAUTHORS+' where book_id in (select book_id from '+TBL_BOOKS+' where avail<=1)'
    # sql='delete from '+TBL_BGENRES+' where book_id in (select book_id from '+TBL_BOOKS+' where avail<=1)'
    return row_count

def arc_skip(arcpath,arcsize):
    """
       Выясняем изменялся ли архив (ZIP или INP-файл)
       если нет, то пытаемся пропустить сканирование, устанавливая для всех книг из
       архива avail=2
       Если не одной такой книги не нашлось, то считаем что пропуск сканирования не удался
       и возвращаем 0
       Если книги из искомого каталога имелись и для них установлен avail=2, то пропуск возможен 
       и возвращаем 1 (или row_count)      
    """
    catalog = findcat(arcpath)
    
    # Если такого каталога еще нет в БД, то значит считаем что ZIP изменен и пропуск невозможен
    if catalog == None:
        return 0
    
    # Если каталог в БД найден и его размер совпадает с текущим, то считаем что файл архива не менялся
    # Поэтому делаем update всех книг из этого архива, однако если ни одного изменения не произошло, то
    # таких книг нет, поэтому видимо нужно пересканировать архив
    if arcsize == catalog.cat_size:
        row_count = Book.objects.filter(path=arcpath).update(avail=2)
        return row_count 
    
    # Здесь мы оказываемся если размеры архива в БД и в наличии разные, поэтому считаем что изменения в архиве есть 
    # и пропуск сканирования невозможен    
    return 0
    

def inp_skip(arcpath,arcsize):
    """
       Выясняем изменялся ли INPX-файл)
       если нет, то пытаемся пропустить сканирование, устанавливая для всех книг из
       INPX avail=2
       Если не одной такой книги не нашлось, то считаем что пропуск сканирования не удался
       и возвращаем 0
       Если книги из искомого INPX имелись и для них установлен avail=2, то пропуск возможен 
       и возвращаем 1 (или row_count)      
    """
    catalog = findcat(arcpath)

    # Если такого INPX еще нет в БД, то значит считаем что INPX изменен и пропуск невозможен
    if catalog == None:
        return 0

    # Если INPX в БД найден и его размер совпадает с текущим, то считаем что файл INPX не менялся
    # Поэтому делаем update всех книг из этого INPX, однако если ни одного изменения не произошло, то
    # таких книг нет, поэтому видимо нужно пересканировать архив
    if arcsize == catalog.cat_size:
        row_count = Book.objects.filter(catalog__parent=catalog).update(avail=2)
        return row_count     
    
    # Здесь мы оказываемся если размеры INPX в БД и в наличии разные, поэтому считаем что изменения в архиве есть 
    # и пропуск сканирования невозможен        
    return 0


def inpx_skip(arcpath, arcsize):
    """
       Выясняем изменялся ли INPX-файл)
       если нет, то пытаемся пропустить сканирование, устанавливая для всех книг из
       INPX avail=2
       Если не одной такой книги не нашлось, то считаем что пропуск сканирования не удался
       и возвращаем 0
       Если книги из искомого INPX имелись и для них установлен avail=2, то пропуск возможен
       и возвращаем 1 (или row_count)
    """
    catalog = findcat(arcpath)

    # Если такого INPX еще нет в БД, то значит считаем что INPX изменен и пропуск невозможен
    if catalog == None:
        return 0

    # Если INPX в БД найден и его размер совпадает с текущим, то считаем что файл INPX не менялся
    # Поэтому делаем update всех книг из этого INPX, однако если ни одного изменения не произошло, то
    # таких книг нет, поэтому видимо нужно пересканировать архив
    if arcsize == catalog.cat_size:
        row_count = Book.objects.filter(catalog__parent__parent=catalog).update(avail=2)
        return row_count

        # Здесь мы оказываемся если размеры INPX в БД и в наличии разные, поэтому считаем что изменения в архиве есть
    # и пропуск сканирования невозможен
    return 0

def findcat(cat_name):
    (head,tail)=os.path.split(cat_name)
    try:
        catalog = Catalog.objects.get(cat_name=tail[:SIZE_CAT_CATNAME], path=cat_name[:SIZE_CAT_PATH])
    except Catalog.DoesNotExist:
        catalog = None

    return catalog

def addcattree(cat_name, archive=0, size = 0):
    catalog = findcat(cat_name)
    if catalog:
        return catalog
    if cat_name in ("","."):
        return Catalog.objects.get_or_create(parent=None, cat_name=".", path=".", cat_type=0)[0]
    (head,tail)=os.path.split(cat_name)
    parent=addcattree(head)
    new_cat = Catalog.objects.create(parent=parent, cat_name=tail[:SIZE_CAT_CATNAME], path=cat_name[:SIZE_CAT_PATH], cat_type=archive, cat_size=size)

    return new_cat

def findbook(name, path, setavail=0):
    # Здесь специально не делается проверка avail, т.к. если удаление было логическим,
    # а книга была восстановлена в своем старом месте
    # то произойдет восстановление записи об этой книги а не добавится новая
    try:
        book = Book.objects.get(filename=name[:SIZE_BOOK_FILENAME], path=path[:SIZE_BOOK_PATH])
    except Book.DoesNotExist:
        book = None

    if book and setavail:
        book.avail=2
        book.save()

    return book

def addbook(name, path, cat, exten, title, annotation, docdate, lang, size=0, archive=0):
    book = Book.objects.create(filename=name[:SIZE_BOOK_FILENAME],path=path[:SIZE_BOOK_PATH],catalog=cat,filesize=size,format=exten.lower()[:SIZE_BOOK_FORMAT],
                title=title[:SIZE_BOOK_TITLE],search_title=title.upper()[:SIZE_BOOK_TITLE],annotation=p(annotation,SIZE_BOOK_ANNOTATION),
                docdate=docdate[:SIZE_BOOK_DOCDATE],lang=lang[:SIZE_BOOK_LANG],cat_type=archive,avail=2, lang_code=getlangcode(title))
    return book

def findauthor(full_name):
    try:
        author = Author.objects.filter(full_name=full_name[:SIZE_AUTHOR_NAME])[:1]
    except Author.DoesNotExist:
        author = None

    return author

def addauthor(full_name):
    author, created = Author.objects.get_or_create(full_name=full_name[:SIZE_AUTHOR_NAME], defaults={'search_full_name':full_name.upper()[:SIZE_AUTHOR_NAME], 
                                                                                                     'lang_code':getlangcode(full_name)})
    return author

def addbauthor(book, author):
    ba = bauthor(book=book, author=author)
    ba.save()

def addgenre(genre):
    genre, created = Genre.objects.get_or_create(genre=genre[:SIZE_GENRE], defaults={'section':unknown_genre, 'subsection':genre[:SIZE_GENRE_SUBSECTION]})
    return genre

def addbgenre(book, genre):
    bg = bgenre(book=book, genre=genre)
    bg.save()

def addseries(ser):
    series, created = Series.objects.get_or_create(ser=ser[:SIZE_SERIES], defaults={'search_ser':ser.upper()[:SIZE_SERIES], 'lang_code':getlangcode(ser)})
    return series

def addbseries(book, ser, ser_no):
    bs = bseries(book=book, ser=ser, ser_no=ser_no)
    bs.save()
    
def set_autocommit(autocommit):
    transaction.set_autocommit(autocommit)
    
def commit():
    transaction.commit()