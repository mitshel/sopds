import os

from django.db.models import Q
from django.utils.translation import ugettext as _

from opds_catalog.models import Book, Catalog, Author, Genre, Series, bseries, bauthor, bgenre, bookshelf, Counter, LangCodes

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
unknown_genre=_('Unknown genre')


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

def zipisscanned(zipname):
    row_count = Book.objects.filter(path=zipname).update(avail=2)
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
    

def inpx_skip(arcpath,arcsize):
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

def findcat(cat_name):
    (head,tail)=os.path.split(cat_name)
    try:
        catalog = Catalog.objects.get(cat_name=tail, path=cat_name)
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
    new_cat = Catalog.objects.create(parent=parent, cat_name=tail, path=cat_name, cat_type=archive, cat_size=size)

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
    book = Book.objects.create(filename=name,path=path,catalog=cat,filesize=size,format=exten.lower()[:8],
                title=title[:256],search_title=title.upper()[:256],annotation=annotation[:10000],docdate=docdate[:32],lang=lang[:16],
                cat_type=archive,avail=2, lang_code=getlangcode(title))
    return book

#def findauthor(first_name,last_name):
#    try:
#        author = Author.objects.filter(last_name=last_name, first_name=first_name)[:1]
#    except Author.DoesNotExist:
#        author = None
#
#    return author

#def addauthor(first_name, last_name):
#    author, created = Author.objects.get_or_create(last_name=last_name, first_name=first_name, lang_code=getlangcode(last_name))
#    return author

def findauthor(full_name):
    try:
        author = Author.objects.filter(full_name=full_name[:128])[:1]
    except Author.DoesNotExist:
        author = None

    return author

def addauthor(full_name):
    author, created = Author.objects.get_or_create(full_name=full_name[:128], defaults={'search_full_name':full_name.upper()[:128], 'lang_code':getlangcode(full_name)})
    return author

def addbauthor(book, author):
    ba = bauthor(book=book, author=author)
    ba.save()

def addgenre(genre):
    genre, created = Genre.objects.get_or_create(genre=genre[:32], defaults={'section':unknown_genre, 'subsection':genre[:100]})
    return genre

def addbgenre(book, genre):
    bg = bgenre(book=book, genre=genre)
    bg.save()

def addseries(ser):
    series, created = Series.objects.get_or_create(ser=ser[:80], defaults={'search_ser':ser.upper()[:80], 'lang_code':getlangcode(ser)})
    return series

def addbseries(book, ser, ser_no):
    bs = bseries(book=book, ser=ser, ser_no=ser_no)
    bs.save()
    
def commit():
    #self.cnx.commit()
    pass