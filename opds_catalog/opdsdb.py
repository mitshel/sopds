import os

from django.db.models import Q

from opds_catalog.models import Book, Catalog, Author, Genre, Series, bseries


# Книги где avail=0 уже известно что удалены
# Книги где avail=2 это только что прверенные существующие книги
# Устанавливаем avail=1 для книг которые не удалены. Во время проверки если они не удалены им присвоится значение 2
# Книги с avail=0 проверятся не будут и будут убраны из всех выдач и всех обработок.
#
# три позиции (0,1,2) сделаны для того чтобы сделать возможным корректную работу cgi-скрипта во время сканирования библиотеки
#
def avail_check_prepare(self):
    Book.objects.filter(~Q(avail=0)).update(avail=1)

def books_del_logical(self):
    row_count = Book.objects.filter(avail=1).update(avail=0)
    return row_count

def books_del_phisical(self):
    row_count = Book.objects.filter(avail__lte=1).delete()
    # TODO: Разобратся нужно ли удалять записи в таблицах связи ManyToMany или они сами удалятся?
    # sql='delete from '+TBL_BAUTHORS+' where book_id in (select book_id from '+TBL_BOOKS+' where avail<=1)'
    # sql='delete from '+TBL_BGENRES+' where book_id in (select book_id from '+TBL_BOOKS+' where avail<=1)'
    return row_count

def zipisscanned(self,zipname,setavail=0):
    try:
        catalog = Book.objects.filter(path=zipname)[:1]
    except Book.DoesNotExist:
        catalog = None

    if catalog!=None and setavail:
        Book.objects.filter(catalog=catalog).update(avail=2)

    return catalog

def findcat(self, cat_name):
    (head,tail)=os.path.split(cat_name)
    try:
        catalog = Catalog.objects.filter(cat_name=tail, path=cat_name)[:1]
    except Catalog.DoesNotExist:
        catalog = None

    return catalog

def addcattree(self, cat_name, archive=0):
    catalog = self.findcat(cat_name)
    if catalog!=None:
       return catalog
    if catalog.cat_name=="":
       return None
    (head,tail)=os.path.split(cat_name)
    parent=self.addcattree(head)
    new_cat = Catalog(parent=parent, cat_name=tail, path=cat_name, cat_type=archive)
    new_cat.save()

    return new_cat

def findbook(self, name, path, setavail=0):
    # Здесь специально не делается проверка avail, т.к. если удаление было логическим, а книга была восстановлена в своем старом месте
    # то произойдет восстановление записи об этой книги а не добавится новая
    try:
       book = Book.objects.filter(filename=name, path=path)[:1]
    except Book.DoesNotExist:
       book = None

    if book!=None and setavail:
          book.update(avail=2)

    return book