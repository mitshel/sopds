#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import sopdscfg
import sopdsdb
import cgi
import codecs
import os
import io
import locale
import time
import sopdsparse
import base64
import subprocess
import zipf
from urllib import parse

#######################################################################
#
# Парсим конфигурационный файл
#
cfg=sopdscfg.cfgreader()
zipf.ZIP_CODEPAGE=cfg.ZIP_CODEPAGE

######################################################################
#
# Парсим данные response (выясняем имя пользователя если была Аутентификация)
#
user = None
if 'REMOTE_USER' in os.environ:
   user = os.environ['REMOTE_USER']

#######################################################################
#
# Вспомогательные функции
#
def translit(s):
   """Russian translit: converts 'привет'->'privet'"""
   assert s is not str, "Error: argument MUST be string"

   table1 = str.maketrans("абвгдеёзийклмнопрстуфхъыьэАБВГДЕЁЗИЙКЛМНОПРСТУФХЪЫЬЭ",  "abvgdeezijklmnoprstufh'y'eABVGDEEZIJKLMNOPRSTUFH'Y'E")
   table2 = {'ж':'zh','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ю':'ju','я':'ja',  'Ж':'Zh','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Sch','Ю':'Ju','Я':'Ja'}
   for k in table2.keys():
       s = s.replace(k,table2[k])
   return s.translate(table1)

def websym(s,attr=False):
    """Replace special web-symbols"""
    result = s
    if attr:
        table = {'"':'\''}
    else:
        table = {'&':'&amp;','<':'&lt;'}
    for k in table.keys():
        result = result.replace(k,table[k])
    return result;

def enc_print(string='', encoding='utf8'):
    sys.stdout.buffer.write(string.encode(encoding) + b'\n')

def header(charset='utf-8'):
   enc_print('Content-Type: text/xml; charset='+charset)
   enc_print()
   enc_print('<?xml version="1.0" encoding="'+charset+'"?>')
   enc_print('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">')
   enc_print('<id>'+cfg.SITE_ID+'</id>')
   enc_print('<title>'+cfg.SITE_TITLE+'</title>')
   enc_print('<subtitle>Simple OPDS Catalog by www.sopds.ru</subtitle>')
   enc_print('<updated>'+time.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
   enc_print('<icon>'+cfg.SITE_ICON+'</icon>')
   enc_print('<author><name>'+cfg.SITE_AUTOR+'</name><uri>'+cfg.SITE_URL+'</uri><email>'+cfg.SITE_EMAIL+'</email></author>')
   enc_print('<link type="application/atom+xml" rel="start" href="'+cfg.CGI_PATH+'?id=00"/>')

def header_search(sstr='',charset='utf-8'):
   enc_print('Content-Type: text/xml; charset='+charset)
   enc_print()
   enc_print('<?xml version="1.0" encoding="'+charset+'"?>')
   enc_print('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">')
   enc_print('<id>tag::search::'+sstr+'</id>')
   enc_print('<title>Поиск</title>')
   enc_print('<updated>'+time.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
   enc_print('<icon>'+cfg.SITE_ICON+'</icon>')
   enc_print('<link type="application/atom+xml" rel="start" href="'+cfg.CGI_PATH+'?id=00"/>')

def header_authors(title,charset='utf-8'):
   enc_print('Content-Type: text/xml; charset='+charset)
   enc_print()
   enc_print('<?xml version="1.0" encoding="'+charset+'"?>')
   enc_print('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">')
   enc_print('<id>tag::authors submenu::</id>')
   enc_print('<title>%s</title>'%title)
   enc_print('<updated>'+time.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
   enc_print('<icon>'+cfg.SITE_ICON+'</icon>')
   enc_print('<link type="application/atom+xml" rel="start" href="'+cfg.CGI_PATH+'?id=00"/>')

def footer():
   enc_print('</feed>')

def main_menu():
   if cfg.ALPHA: am='30'
   else: am=''
   dbinfo=opdsdb.getdbinfo(cfg.DUBLICATES_SHOW,cfg.BOOK_SHELF,user)
   enc_print('<link href="'+cfg.SEARCHXML_PATH+'" rel="search" type="application/opensearchdescription+xml" />')
   enc_print('<link href="'+cfg.CGI_PATH+'?searchTerm={searchTerms}" rel="search" type="application/atom+xml" />')
   enc_print('<entry>')
   enc_print('<title>По каталогам</title>')
   enc_print('<content type="text">Каталогов: %s, книг: %s.</content>'%(dbinfo[2][1],dbinfo[0][1]))
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id=01"/>')
   enc_print('<id>id:01</id></entry>')
   enc_print('<entry>')
   enc_print('<title>По авторам</title>')
   enc_print('<content type="text">Авторов: %s.</content>'%dbinfo[1][1])
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+am+'02"/>')
   enc_print('<id>id:02</id></entry>')
   enc_print('<entry>')
   enc_print('<title>По наименованию</title>')
   enc_print('<content type="text">Книг: %s.</content>'%dbinfo[0][1])
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+am+'03"/>')
   enc_print('<id>id:03</id></entry>')
   enc_print('<entry>')
   enc_print('<title>По Жанрам</title>')
   enc_print('<content type="text">Жанров: %s.</content>'%dbinfo[3][1])
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id=04"/>')
   enc_print('<id>id:04</id></entry>')
   enc_print('<entry>')
   enc_print('<title>По Сериям</title>')
   enc_print('<content type="text">Серий: %s.</content>'%dbinfo[4][1])
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+am+'06"/>')
   enc_print('<id>id:06</id></entry>')
   if cfg.NEW_PERIOD!=0:
      enc_print('<entry>')
      enc_print('<title>Новинки за %s суток</title>'%cfg.NEW_PERIOD)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id=05"/>')
      enc_print('<id>id:05</id></entry>')
   if cfg.BOOK_SHELF and user!=None:
      enc_print('<entry>')
      enc_print('<title>Книжная полка для %s</title>'%user)
      enc_print('<content type="text">Книг: %s.</content>'%dbinfo[5][1])
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id=08"/>')
      enc_print('<id>id:08</id></entry>')

def new_menu():
   if cfg.ALPHA: am='30'
   else: am=''
   newinfo=opdsdb.getnewinfo(cfg.DUBLICATES_SHOW,cfg.NEW_PERIOD)
   enc_print('<entry>')
   enc_print('<title>Все новинки за %s суток</title>'%cfg.NEW_PERIOD)
   enc_print('<content type="text">Новых книг: %s.</content>'%newinfo[0][1])
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+am+'03&amp;news=1"/>')
   enc_print('<id>id:03:news</id></entry>')
   enc_print('<entry>')
   enc_print('<title>Новинки по авторам</title>')
#   enc_print('<content type="text">Авторов новинок: %s.</content>'%newinfo[1][1])
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+am+'02&amp;news=1"/>')
   enc_print('<id>id:02:news</id></entry>')
   enc_print('<entry>')
   enc_print('<title>Новинки по Жанрам</title>')
#   enc_print('<content type="text">Жанров новинок: %s.</content>'%newinfo[2][1])
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id=04&amp;news=1"/>')
   enc_print('<id>id:04:news</id></entry>')
   enc_print('<entry>')
   enc_print('<title>Новинки по Сериям</title>')
#   enc_print('<content type="text">Серий новинок: %s.</content>'%newinfo[3][1])
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+am+'06&amp;news=1"/>')
   enc_print('<id>id:06:news</id></entry>')

def authors_submenu(author_id):
   enc_print('<entry>')
   enc_print('<title>Книги по сериям</title>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id=31'+str(author_id)+'"/>')
   enc_print('<id>id:31:authors</id></entry>')
   enc_print('<entry>')
   enc_print('<title>Книги вне серий</title>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id=34'+str(author_id)+'"/>')
   enc_print('<id>id:32:authors</id></entry>')
   enc_print('<entry>')
   enc_print('<title>Книги по алфавиту</title>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id=33'+str(author_id)+'"/>')
   enc_print('<id>id:33:authors</id></entry>')
   enc_print('<entry>')

def entry_start():
   enc_print('<entry>')

def entry_head(e_title,e_date,e_id):
   enc_print('<title>'+websym(e_title)+'</title>')
   if e_date!=None:
      enc_print('<updated>'+e_date.strftime("%Y-%m-%dT%H:%M:%S")+'</updated>')
   enc_print('<id>id:'+e_id+'</id>')

def entry_link_subsection(link_id):
#   enc_print('<link type="application/atom+xml" rel="alternate" href="'+cfg.CGI_PATH+'?id='+link_id+'"/>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="'+cfg.CGI_PATH+'?id='+link_id+nl+'"/>')

def entry_link_book(link_id,format):
   str_id=str(link_id)
#   enc_print('<link type="application/'+format+'" rel="alternate" href="'+cfg.CGI_PATH+'?id=91'+str_id+'"/>')
   if format.lower()=='fb2' and cfg.FB2TOEPUB:
      enc_print('<link type="application/epub" href="'+cfg.CGI_PATH+'?id=93'+str_id+'" rel="http://opds-spec.org/acquisition" />')
      enc_print('<link type="application/epub+zip" href="'+cfg.CGI_PATH+'?id=93'+str_id+'" rel="http://opds-spec.org/acquisition" />')
   enc_print('<link type="application/'+format+'" href="'+cfg.CGI_PATH+'?id=91'+str_id+'" rel="http://opds-spec.org/acquisition" />')
   enc_print('<link type="application/'+format+'+zip" href="'+cfg.CGI_PATH+'?id=92'+str_id+'" rel="http://opds-spec.org/acquisition" />')

def entry_authors(db,book_id,link_show=False):
   authors=""
   for (author_id,first_name,last_name) in db.getauthors(book_id):
       enc_print('<author><name>'+last_name+' '+first_name+'</name></author>')
       if len(authors)>0:
             authors+=', '
       authors+=last_name+' '+first_name
       if link_show:
          author_ref=cfg.CGI_PATH+'?id=22'+str(author_id)
          enc_print('<link href="'+author_ref+'" rel="related" type="application/atom+xml;profile=opds-catalog" title="Все книги автора '+websym(last_name,True)+' '+websym(first_name,True)+'" />')
       else:
          enc_print('<content type="text">'+authors+'</content>')
   return authors

def entry_genres(db,book_id):
   genres=""
   for (section,genre) in opdsdb.getgenres(book_id):
       enc_print('<category term="%s" label="%s" />'%(genre,genre))
       if len(genres)>0:
             genres+=', '
       genres+=genre
   return genres

def entry_series(db,book_id):
   series=""
   for (ser,) in opdsdb.getseries(book_id):
       if len(series)>0:
             series+=', '
       series+=ser
   return series

def entry_covers(cover,cover_type,book_id):
   have_extracted_cover=0
   if cfg.COVER_SHOW!=0:
      if cfg.COVER_SHOW!=2:
         if cover!=None and cover!='':
            enc_print( '<link href="%s/%s" rel="http://opds-spec.org/image" type="%s" />'%(cfg.COVER_PATH,cover,cover_type) )
            enc_print( '<link href="%s/%s" rel="x-stanza-cover-image" type="%s" />'%(cfg.COVER_PATH,cover,cover_type) )
            enc_print( '<link href="%s/%s" rel="http://opds-spec.org/thumbnail" type="%s" />'%(cfg.COVER_PATH,cover,cover_type) )
            enc_print( '<link href="%s/%s" rel="x-stanza-cover-image-thumbnail" type="%s" />'%(cfg.COVER_PATH,cover,cover_type) )
            have_extracted_cover=1
      if cfg.COVER_SHOW==2 or (cfg.COVER_SHOW==3 and have_extracted_cover==0):
            id='99'+str(book_id)
            enc_print( '<link href="%s?id=%s" rel="http://opds-spec.org/image" type="image/jpeg" />'%(cfg.CGI_PATH,id) )
            enc_print( '<link href="%s?id=%s" rel="x-stanza-cover-image" type="image/jpeg" />'%(cfg.CGI_PATH,id) )
            enc_print( '<link href="%s?id=%s" rel="http://opds-spec.org/thumbnail"  type="image/jpeg" />'%(cfg.CGI_PATH,id) )
            enc_print( '<link href="%s?id=%s" rel="x-stanza-cover-image-thumbnail"  type="image/jpeg" />'%(cfg.CGI_PATH,id) )

def entry_content(e_content):
  enc_print('<content type="text">'+websym(e_content)+'</content>')

def entry_content2(annotation='',title='',authors='',genres='',filename='',filesize=0,docdate='',series=''):
  enc_print('<content type="text/html">')
  if title!='':
     enc_print('&lt;b&gt;Название книги:&lt;/b&gt; '+websym(title)+'&lt;br/&gt;')
  if authors!='':
     enc_print('&lt;b&gt;Авторы:&lt;/b&gt; '+websym(authors)+'&lt;br/&gt;')
  if genres!='':
     enc_print('&lt;b&gt;Жанры:&lt;/b&gt; '+websym(genres)+'&lt;br/&gt;')
  if series!='':
     enc_print('&lt;b&gt;Серии:&lt;/b&gt; '+websym(series)+'&lt;br/&gt;')
  if filename!='':
     enc_print('&lt;b&gt;Файл:&lt;/b&gt; '+websym(filename)+'&lt;br/&gt;')
  if filesize>0:
     enc_print('&lt;b&gt;Размер файла:&lt;/b&gt; '+str(fsize//1000)+'Кб.&lt;br/&gt;')
  if docdate!='':
     enc_print('&lt;b&gt;Дата правки:&lt;/b&gt; '+docdate+'&lt;br/&gt;')
  if annotation!='':
     enc_print('&lt;p class=book&gt;'+websym(annotation)+'&lt;/p&gt;')
  enc_print('</content>')

def entry_finish():
   enc_print('</entry>')

def page_control(db, page, link_id):
   if page>0:
      prev_href=cfg.CGI_PATH+"?id="+link_id+"&amp;page="+str(page-1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'+prev_href+'" />')
   if db.next_page:
      next_href=cfg.CGI_PATH+"?id="+link_id+"&amp;page="+str(page+1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'+next_href+'" />')

def alphabet_menu(iid_value):
   entry_start()
   entry_head('А..Я (РУС)', None, 'alpha:1')
   id=iid_value+'&amp;alpha=1'+nl
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+id+'"/>')
   entry_finish()
   entry_start()
   entry_head('0..9 (Цифры)', None, 'alpha:2')
   id=iid_value+'&amp;alpha=2'+nl
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+id+'"/>')
   entry_finish()
   entry_start()
   entry_head('A..Z (ENG)', None, 'alpha:3')
   id=iid_value+'&amp;alpha=3'+nl
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+id+'"/>')
   entry_finish()
   entry_start()
   entry_head('Другие Символы', None, 'alpha:4')
   id=iid_value+'&amp;alpha=4'+nl
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+id+'"/>')
   entry_finish()
   entry_start()
   entry_head('Показать всё', None, 'alpha:5')
   id=iid_value+nl
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+cfg.CGI_PATH+'?id='+id+'"/>')
   entry_finish()


###########################################################################################################
# Основной код программы
#

locale.setlocale(locale.LC_ALL,'ru_RU.UTF-8')

type_value=0
slice_value=0
page_value=0
ser_value=0
alpha=0
news=0
np=0
nl=''

form = cgi.FieldStorage()
if 'id' in form:
   id_value=form.getvalue("id", "0")
   if id_value.isdigit():
      if len(id_value)>1:
         type_value = int(id_value[0:2])
      if len(id_value)>2:
         slice_value = int(id_value[2:])
if 'page' in form:
   page=form.getvalue("page","0")
   if page.isdigit():
         page_value=int(page)
if 'searchType' in form:
   searchType=form.getvalue("searchType","").strip()
   if searchType=='books': type_value=71
   if searchType=='authors': type_value=72
   if searchType=='series': type_value=73
if 'searchTerm' in form:
   searchTerm=form.getvalue("searchTerm","").strip()
   if type_value!=71 and type_value!=72 and type_value!=73: type_value=7
   slice_value=-1
   id_value='%02d&amp;searchTerm=%s'%(type_value,searchTerm)
if 'alpha' in form:
   salpha=form.getvalue("alpha","").strip()
   if salpha.isdigit(): alpha=int(salpha)
if 'news' in form:
   news=1
   nl='&amp;news=1'
   np=cfg.NEW_PERIOD
if 'ser' in form:
   ser=form.getvalue("ser","0")
   if ser.isdigit():
      ser_value=int(ser)

opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
opdsdb.openDB()

if type_value==0:
   header()
   main_menu()
   footer()

#########################################################
# Выбрана сортировка "По каталогам"
#
elif type_value==1:
   header()
   for (item_type,item_id,item_name,item_path,reg_date,item_title,annotation,docdate,format,fsize,cover,cover_type) in opdsdb.getitemsincat(slice_value,cfg.MAXITEMS,page_value):
       entry_start()
       entry_head(item_title, reg_date, id_value)
       if item_type==1:
          id='01'+str(item_id)
          entry_link_subsection(id)
       if item_type==2:
          id='90'+str(item_id)
          entry_link_book(item_id,format)
          entry_covers(cover,cover_type,item_id)
          authors=entry_authors(opdsdb,item_id,True)
          genres=entry_genres(opdsdb,item_id)
          series=entry_series(opdsdb,item_id)
          entry_content2(annotation,item_title,authors,genres,item_name,fsize,docdate,series)
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Вывод дополнительного меню алфавита для сортировок по Наименованиям, по Автроам и по Жанрам
#
elif (type_value==30):
   header()
   alphabet_menu(id_value[2:])
   footer()

#########################################################
# Выбрана сортировка "По авторам" - выбор по нескольким первым буквам автора
#
elif type_value==2:
   i=slice_value
   letter=""
   while i>0:
      letter=chr(i%10000)+letter
      i=i//10000

   header()
   for (letters,cnt) in opdsdb.getauthor_2letters(letter,alpha,np):
       id=""
       for i in range(len(letters)):
           id+='%04d'%(ord(letters[i]))

       if cfg.SPLITTITLES==0 or cnt<=cfg.SPLITTITLES or len(letters)>10:
         id='12'+id
       else:
         id='02'+id

       entry_start()
       entry_head(letters, None, id_value)
       entry_link_subsection(id)
       entry_content('Всего: '+str(cnt)+' автора(ов).')
       entry_finish()
   footer()

#########################################################
# Выбрана сортировка "По сериям" - выбор по нескольким первым буквам серии
#
elif type_value==6:
   i=slice_value
   letter=""
   while i>0:
      letter=chr(i%10000)+letter
      i=i//10000

   header()
   for (letters,cnt) in opdsdb.getseries_2letters(letter,alpha,np):
       id=""
       for i in range(len(letters)):
           id+='%04d'%(ord(letters[i]))

       if cfg.SPLITTITLES==0 or cnt<=cfg.SPLITTITLES or len(letters)>10:
         id='16'+id
       else:
         id='06'+id

       entry_start()
       entry_head(letters, None, id_value)
       entry_link_subsection(id)
       entry_content('Всего: '+str(cnt)+' серий.')
       entry_finish()
   footer()


#########################################################
# Выбрана сортировка "По наименованию" - выбор по нескольким первым буквам наименования
#
elif type_value==3:
   i=slice_value
   letter=""
   while i>0:
      letter=chr(i%10000)+letter
      i=i//10000

   header()
   for (letters,cnt) in opdsdb.gettitle_2letters(letter,cfg.DUBLICATES_SHOW,alpha,np):
       id=""
       for i in range(len(letters)):
           id+='%04d'%(ord(letters[i]))

       if cfg.SPLITTITLES==0 or cnt<=cfg.SPLITTITLES or len(letters)>10:
         id='13'+id
       else:
         id='03'+id
  
       entry_start()
       entry_head(letters, None, id_value)
       entry_link_subsection(id)
       entry_content('Всего: '+str(cnt)+' наименований.')
       entry_finish()
   footer()

#########################################################
# Выдача списка книг по наименованию или на основании поискового запроса
#
if type_value==13 or type_value==71:

   if slice_value>=0:
      i=slice_value
      letter=""
      while i>0:
         letter=chr(i%10000)+letter
         i=i//10000
   else:
      letter="%"+searchTerm

   header()
   for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in opdsdb.getbooksfortitle(letter,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW,np):
       id='90'+str(book_id)
       entry_start()
       entry_head(book_title, reg_date, id_value)
       entry_link_book(book_id,format)
       entry_covers(cover,cover_type,book_id)
       authors=entry_authors(opdsdb,book_id,True)
       genres=entry_genres(opdsdb,book_id)
       series=entry_series(opdsdb,book_id)
       entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Выбрана сортировка "По жанрам" - показ секций
#
elif type_value==4:
   header()
   for (genre_id,genre_section,cnt) in opdsdb.getgenres_sections(cfg.DUBLICATES_SHOW,np):
       id='14'+str(genre_id)
       entry_start()
       entry_head(genre_section, None, id_value)
       entry_link_subsection(id)
       entry_content('Всего: '+str(cnt)+' книг.')
       entry_finish()
   footer()

#########################################################
# Выбрана сортировка "По жанрам" - показ подсекций
#
elif type_value==14:
   header()
   for (genre_id,genre_subsection,cnt) in opdsdb.getgenres_subsections(slice_value,cfg.DUBLICATES_SHOW,np):
       id='24'+str(genre_id)
       if cfg.ALPHA: id='30'+id
       entry_start()
       entry_head(genre_subsection, None, id_value)
       entry_link_subsection(id)
       entry_content('Всего: '+str(cnt)+' книг.')
       entry_finish()
   footer()

#########################################################
# Выдача списка книг по жанру
#
if type_value==24:
   header()
   for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in opdsdb.getbooksforgenre(slice_value,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW,alpha,np):
       id='90'+str(book_id)
       entry_start()
       entry_head(book_title, reg_date, id_value)
       entry_link_book(book_id,format)
       entry_covers(cover,cover_type,book_id)
       authors=entry_authors(opdsdb,book_id,True)
       genres=entry_genres(opdsdb,book_id)
       series=entry_series(opdsdb,book_id)
       entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Выбрана сортировка "Последние поступления"
#
elif type_value==5:
   header()
   new_menu()
   footer()

#########################################################
# Выбор типа поиска по автору или наименованию или серии
#
if type_value==7:
   header_search(searchTerm)
   enc_print('<link href="'+cfg.SEARCHXML_PATH+'" rel="search" type="application/opensearchdescription+xml" />')
   enc_print('<link href="'+cfg.CGI_PATH+'?searchTerm={searchTerms}" rel="search" type="application/atom+xml" />')
   entry_start()
   entry_head('Поиск книг',None,'71')
   entry_content('Поиск книги по ее наименованию')
   enc_print('<link type="application/atom+xml;profile=opds-catalog" href="'+cfg.CGI_PATH+'?searchType=books&amp;searchTerm='+parse.quote(searchTerm)+'" />')
   entry_finish()
   entry_start()
   entry_head('Поиск авторов',None,'72')
   entry_content('Поиск авторов по имени')
   enc_print('<link type="application/atom+xml;profile=opds-catalog" href="'+cfg.CGI_PATH+'?searchType=authors&amp;searchTerm='+parse.quote(searchTerm)+'" />')
   entry_finish()
   entry_start()
   entry_head('Поиск серий',None,'73')
   entry_content('Поиск серий книг')
   enc_print('<link type="application/atom+xml;profile=opds-catalog" href="'+cfg.CGI_PATH+'?searchType=series&amp;searchTerm='+parse.quote(searchTerm)+'" />')
   entry_finish()
   footer()

#########################################################
# Выдача списка книг на книжной полке
#
if type_value==8:
   header()
   for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in opdsdb.getbooksforuser(user,cfg.MAXITEMS,page_value):
       id='90'+str(book_id)
       entry_start()
       entry_head(book_title, reg_date, id_value)
       entry_link_book(book_id,format)
       entry_covers(cover,cover_type,book_id)
       authors=entry_authors(opdsdb,book_id,True)
       genres=entry_genres(opdsdb,book_id)
       series=entry_series(opdsdb,book_id)
       entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Выдача списка авторов по имени или на основании поиска
#
if type_value==12 or type_value==72:

   if slice_value>0:
      i=slice_value
      letter=""
      while i>0:
         letter=chr(i%10000)+letter
         i=i//10000
   else:
      letter="%"+searchTerm

   header()
   for (author_id,first_name, last_name,cnt) in opdsdb.getauthorsbyl(letter,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW,np):
       id='22'+str(author_id)
       entry_start()
       entry_head(last_name+' '+first_name, None, id_value)
       entry_link_subsection(id)
       entry_content('Всего: '+str(cnt)+' книг.')
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()


#########################################################
# Выдача списка серий по названию или на основании поиска
#
if type_value==16 or type_value==73:

   if slice_value>0:
      i=slice_value
      letter=""
      while i>0:
         letter=chr(i%10000)+letter
         i=i//10000
   else:
      letter="%"+searchTerm

   header()
   for (ser_id,ser,cnt) in opdsdb.getseriesbyl(letter,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW,np):
       id='26'+str(ser_id)
       entry_start()
       entry_head(ser, None, id_value)
       entry_link_subsection(id)
       entry_content('Всего: '+str(cnt)+' книг.')
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Выдача подменю вывода книг по автору - в случае флага новинок будет сразу переход к выдаче книг автора
#
if type_value==22 and np==0:
   (first_name,last_name)=opdsdb.getauthor_name(slice_value)
   header_authors('Книги автора %s %s'%(last_name,first_name))
   authors_submenu(slice_value)
   footer()

#########################################################
# Выдача серий по автору
#
if type_value==31:
   (first_name,last_name)=opdsdb.getauthor_name(slice_value)
   header_authors('Сериии книг автора %s %s'%(last_name,first_name))
   for (ser_id,ser,cnt) in opdsdb.getseriesforauthor(slice_value,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW):
       id='34'+str(slice_value)+'&amp;ser='+str(ser_id)
       entry_start()
       entry_head(ser, None, id_value)
       entry_link_subsection(id)
       entry_content('Всего: '+str(cnt)+' книг.')
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Выдача списка книг по автору по алфавиту
#
if type_value==33 or (type_value==22 and np!=0):
   header()
   for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in opdsdb.getbooksforautor(slice_value,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW,np):
       id='90'+str(book_id)
       entry_start()
       entry_head(book_title, reg_date, id_value)
       entry_link_book(book_id,format)
       entry_covers(cover,cover_type,book_id)
       authors=entry_authors(opdsdb,book_id,True)
       genres=entry_genres(opdsdb,book_id)
       series=entry_series(opdsdb,book_id)
       entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Выдача списка книг по автору по выбранной серии (или вне серий если ser_value==0)
#
if type_value==34:
   header()
   for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in opdsdb.getbooksforautorser(slice_value,ser_value,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW):
       id='90'+str(book_id)
       entry_start()
       entry_head(book_title, reg_date, id_value)
       entry_link_book(book_id,format)
       entry_covers(cover,cover_type,book_id)
       authors=entry_authors(opdsdb,book_id,True)
       genres=entry_genres(opdsdb,book_id)
       series=entry_series(opdsdb,book_id)
       entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Выдача списка книг по серии
#
if type_value==26:
   header()
   for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in opdsdb.getbooksforser(slice_value,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW,np):
       id='90'+str(book_id)
       entry_start()
       entry_head(book_title, reg_date, id_value)
       entry_link_book(book_id,format)
       entry_covers(cover,cover_type,book_id)
       authors=entry_authors(opdsdb,book_id,True)
       genres=entry_genres(opdsdb,book_id)
       series=entry_series(opdsdb,book_id)
       entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
       entry_finish()
   page_control(opdsdb,page_value,id_value)
   footer()

#########################################################
# Выдача ссылок на книгу
#
elif type_value==90:
   id='90'+str(slice_value)
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="self" href="sopds.cgi?id='+id+'"/>')
   (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
   entry_start()
   entry_head(title, reg_date, id_value)
   entry_link_book(slice_value,format)
   entry_covers(cover,cover_type,slice_value)
   authors=entry_authors(opdsdb,slice_value,True)
   genres=entry_genres(opdsdb,slice_value)
   series=entry_series(opdsdb,book_id)
   entry_content2(annotation,title,authors,genres,book_name,fsize,docdate,series)
   entry_finish()
   footer()

#########################################################
# Выдача файла книги
#
elif type_value==91:
   (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
   if cfg.BOOK_SHELF and user!=None: opdsdb.addbookshelf(user,slice_value)
   full_path=os.path.join(cfg.ROOT_LIB,book_path)
   if cfg.TITLE_AS_FN: transname=translit(title+'.'+format)
   else: transname=translit(book_name)
   # HTTP Header
   enc_print('Content-Type:application/octet-stream; name="'+transname+'"')
   enc_print('Content-Disposition: attachment; filename="'+transname+'"')
   enc_print('Content-Transfer-Encoding: binary')
   if cat_type==sopdsdb.CAT_NORMAL:
      file_path=os.path.join(full_path,book_name)
      book_size=os.path.getsize(file_path.encode('utf-8'))
      enc_print('Content-Length: '+str(book_size))
      enc_print()
      fo=codecs.open(file_path.encode("utf-8"), "rb")
      str=fo.read()
      sys.stdout.buffer.write(str)
      fo.close()
   elif cat_type==sopdsdb.CAT_ZIP:
      fz=codecs.open(full_path.encode("utf-8"), "rb")
      z = zipf.ZipFile(fz, 'r', allowZip64=True)
      book_size=z.getinfo(book_name).file_size
      enc_print('Content-Length: '+str(book_size))
      enc_print()
      fo= z.open(book_name)
      str=fo.read()
      sys.stdout.buffer.write(str)
      fo.close()
      z.close()
      fz.close()

#########################################################
# Выдача файла книги в ZIP формате
#
elif type_value==92:
   (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
   if cfg.BOOK_SHELF and user!=None: opdsdb.addbookshelf(user,slice_value)
   full_path=os.path.join(cfg.ROOT_LIB,book_path)
   if cfg.TITLE_AS_FN: transname=translit(title+'.'+format)
   else: transname=translit(book_name)
   # HTTP Header
   enc_print('Content-Type:application/zip; name="'+transname+'"')
   enc_print('Content-Disposition: attachment; filename="'+transname+'.zip"')
   enc_print('Content-Transfer-Encoding: binary')
   if cat_type==sopdsdb.CAT_NORMAL:
      file_path=os.path.join(full_path,book_name)
      dio = io.BytesIO()
      z = zipf.ZipFile(dio, 'w', zipf.ZIP_DEFLATED)
      z.write(file_path.encode('utf-8'),transname)
      z.close()
      buf = dio.getvalue()
      enc_print('Content-Length: %s'%len(buf))
      enc_print()
      sys.stdout.buffer.write(buf)
   elif cat_type==sopdsdb.CAT_ZIP:
      fz=codecs.open(full_path.encode("utf-8"), "rb")
      zi = zipf.ZipFile(fz, 'r', allowZip64=True)
      fo= zi.open(book_name)
      str=fo.read()
      fo.close()
      zi.close()
      fz.close()

      dio = io.BytesIO()
      zo = zipf.ZipFile(dio, 'w', zipf.ZIP_DEFLATED)
      zo.writestr(transname,str)
      zo.close()

      buf = dio.getvalue()
      enc_print('Content-Length: %s'%len(buf))
      enc_print()
      sys.stdout.buffer.write(buf)

#########################################################
# Выдача файла книги после конвертации в EPUB
#
elif type_value==93:
   (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
   if cfg.BOOK_SHELF and user!=None: opdsdb.addbookshelf(user,slice_value)
   full_path=os.path.join(cfg.ROOT_LIB,book_path)
   (n,e)=os.path.splitext(book_name)
   if cfg.TITLE_AS_FN: transname=translit(title)+'.epub'
   else: transname=translit(n)+'.epub'
   if cat_type==sopdsdb.CAT_NORMAL:
      tmp_fb2_path=None
      file_path=os.path.join(full_path,book_name)
   elif cat_type==sopdsdb.CAT_ZIP:
      fz=codecs.open(full_path.encode("utf-8"), "rb")
      z = zipf.ZipFile(fz, 'r', allowZip64=True)
      z.extract(book_name,'/tmp')
      tmp_fb2_path=os.path.join(cfg.TEMP_DIR,book_name)
      file_path=tmp_fb2_path

   tmp_epub_path=os.path.join(cfg.TEMP_DIR,transname)
   proc = subprocess.Popen(("%s %s %s"%(cfg.FB2TOEPUB_PATH,("\"%s\""%file_path),"\"%s\""%tmp_epub_path)).encode('utf8'), shell=True, stdout=subprocess.PIPE)
   out = proc.stdout.readlines()
   
   if os.path.isfile(tmp_epub_path):
      fo=codecs.open(tmp_epub_path, "rb")
      str=fo.read()
      # HTTP Header
      enc_print('Content-Type:application/octet-stream; name="'+transname+'"')
      enc_print('Content-Disposition: attachment; filename="'+transname+'"')
      enc_print('Content-Transfer-Encoding: binary')
      enc_print('Content-Length: %s'%len(str))
      enc_print()
      sys.stdout.buffer.write(str)
      fo.close()
   else:
      print('Status: 404 Not Found')
      print()

   try: os.remove(tmp_fb2_path.encode('utf-8'))
   except: pass
   try: os.remove(tmp_epub_path)
   except: pass

######################################################
# Выдача Обложки На лету
#
elif type_value==99:
   (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
   c0=0
   if format=='fb2':
      full_path=os.path.join(cfg.ROOT_LIB,book_path)
      fb2=sopdsparse.fb2parser(1)
      if cat_type==sopdsdb.CAT_NORMAL:
         file_path=os.path.join(full_path,book_name)
         fo=codecs.open(file_path.encode("utf-8"), "rb")
         fb2.parse(fo,0)
         fo.close()
      elif cat_type==sopdsdb.CAT_ZIP:
         fz=codecs.open(full_path.encode("utf-8"), "rb")
         z = zipf.ZipFile(fz, 'r', allowZip64=True)
         fo = z.open(book_name)
         fb2.parse(fo,0)
         fo.close()
         z.close()
         fz.close()

      if len(fb2.cover_image.cover_data)>0:
         try:
           s=fb2.cover_image.cover_data
           dstr=base64.b64decode(s)
           ictype=fb2.cover_image.getattr('content-type')
           enc_print('Content-Type:'+ictype)
           enc_print()
           sys.stdout.buffer.write(dstr)
           c0=1
         except:
           c0=0

   if c0==0: 
      if os.path.exists(sopdscfg.NOCOVER_IMG):
         enc_print('Content-Type: image/jpeg')
         enc_print()
         f=open(sopdscfg.NOCOVER_IMG,"rb")
         sys.stdout.buffer.write(f.read())
         f.close()
      else:
         print('Status: 404 Not Found')
         print()

opdsdb.closeDB()


