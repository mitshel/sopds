import os

from django.db.models import Q

from opds_catalog.models import Book, Catalog, Author, Genre, Series, bseries, bauthor, bgenre, bookshelf, Counter

##########################################################################
# типы каталогов (cat_type)
#
CAT_NORMAL=0
CAT_ZIP=1
CAT_GZ=2

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
unknown_genre='Неизвестный жанр'


def clear_all():
    Book.objects.all().delete()
    Catalog.objects.all().delete()
    Author.objects.all().delete()
    Genre.objects.all().delete()
    Series.objects.all().delete()
    bseries.objects.all().delete()
    bauthor.objects.all().delete()
    bseries.objects.all().delete()
    bookshelf.objects.all().delete()
    Counter.objects.all().delete()

# Книги где avail=0 уже известно что удалены
# Книги где avail=2 это только что прверенные существующие книги
# Устанавливаем avail=1 для книг которые не удалены. Во время проверки
# если они не удалены им присвоится значение 2
# Книги с avail=0 проверятся не будут и будут убраны из всех выдач и всех обработок.
#
# три позиции (0,1,2) сделаны для того чтобы сделать возможным корректную работу
# cgi-скрипта во время сканирования библиотеки
#
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

def zipisscanned(zipname,setavail=0):
    row_count = Book.objects.filter(path=zipname).update(avail=2)
    return row_count

def findcat(cat_name):
    (head,tail)=os.path.split(cat_name)
    try:
        catalog = Catalog.objects.get(cat_name=tail, path=cat_name)
    except Catalog.DoesNotExist:
        catalog = None

    return catalog

def addcattree(cat_name, archive=0):
    catalog = findcat(cat_name)
    if catalog:
        return catalog
    if cat_name=="":
        return Catalog.objects.get_or_create(cat_name=".", path=".", cat_type=archive)[0]
    (head,tail)=os.path.split(cat_name)
    parent=addcattree(head)
    new_cat = Catalog.objects.create(parent=parent, cat_name=tail, path=cat_name, cat_type=archive)

    return new_cat

def findbook(name, path, setavail=0):
    # Здесь специально не делается проверка avail, т.к. если удаление было логическим,
    # а книга была восстановлена в своем старом месте
    # то произойдет восстановление записи об этой книги а не добавится новая
    try:
       book = Book.objects.get(filename=name, path=path)
    except Book.DoesNotExist:
       book = None

    if book and setavail:
       book.avail=2
       book.save()

    return book

def addbook(name, path, cat, exten, title, annotation, docdate, lang, size=0, archive=0):
    format=exten[1:]
    format=format.lower()
    book = Book.objects.create(filename=name,path=path,catalog=cat,filesize=size,format=format,
                title=title,annotation=annotation,docdate=docdate,lang=lang,
                cat_type=archive,doublicat=0,avail=2)
    return book

def findauthor(first_name,last_name):
    try:
        author = Author.objects.filter(last_name=last_name, first_name=first_name)[:1]
    except Author.DoesNotExist:
        author = None

    return author

def addauthor(first_name, last_name):
    author, created = Author.objects.get_or_create(last_name=last_name, first_name=first_name)
    return author

def addbauthor(book, author):
    ba = bauthor(book=book, author=author)
    ba.save()
    #book.authors.add(author)

def addgenre(genre):
    genre, created = Genre.objects.get_or_create(genre=genre, defaults={'section':unknown_genre, 'subsection':genre})
    return genre

def addbgenre(book, genre):
    bg = bgenre(book=book, genre=genre)
    bg.save()
    #book.genres.add(genre)

def addseries(ser):
    series, created = Series.objects.get_or_create(ser=ser)
    return series

def addbseries(book, ser, ser_no):
    bs = bseries(book=book, ser=ser, ser_no=ser_no)
    bs.save()