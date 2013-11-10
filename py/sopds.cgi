#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import sopdscfg
import sopdsdb
import cgi
import codecs
import os
import urllib.parse
import zipfile
import io
import locale


def translit(s):
   """Russian translit: converts 'привет'->'privet'"""
   assert s is not str, "Error: argument MUST be string"

   table1 = str.maketrans("абвгдеёзийклмнопрстуфхъыьэАБВГДЕЁЗИЙКЛМНОПРСТУФХЪЫЬЭ",  "abvgdeezijklmnoprstufh'y'eABVGDEEZIJKLMNOPRSTUFH'Y'E")
   table2 = {'ж':'zh','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ю':'ju','я':'ja',  'Ж':'Zh','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Sch','Ю':'Ju','Я':'Ja'}
   for k in table2.keys():
       s = s.replace(k,table2[k])
   return s.translate(table1)

def enc_print(string='', encoding='utf8'):
    sys.stdout.buffer.write(string.encode(encoding) + b'\n')

def header(charset='utf-8'):
   enc_print('Content-Type: text/xml; charset='+charset)
   enc_print()
   enc_print('<?xml version="1.0" encoding="'+charset+'"?>')
   enc_print('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opds="http://opds-spec.org/">')
   enc_print('<id>'+sopdscfg.SITE_ID+'</id>')
   enc_print('<title>'+sopdscfg.SITE_TITLE+'</title>')
   enc_print('<updated>2013-10-20T02:41:33Z</updated>')
   enc_print('<icon>'+sopdscfg.SITE_ICON+'</icon>')
   enc_print('<author><name>'+sopdscfg.SITE_AUTOR+'</name><uri>'+sopdscfg.SITE_URL+'</uri><email>'+sopdscfg.SITE_EMAIL+'</email></author>')

def footer():
   enc_print('</feed>')

def main_menu():
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+sopdscfg.SITE_MAINTITLE+'" href="/"/>')
   enc_print('<entry>')
   enc_print('<title>По каталогам</title>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="sopds.cgi?id=1"/>')
   enc_print('<id>sopds.cgi?id=1</id></entry>')
   enc_print('<entry>')
   enc_print('<title>По авторам</title>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="sopds.cgi?id=2"/>')
   enc_print('<id>sopds.cgi?id=2</id></entry>')


###########################################################################
# Основной код программы
#

locale.setlocale(locale.LC_ALL,'ru_RU.UTF-8')

type_value=0
slice_value=0
page_value=0
letter=""
form = cgi.FieldStorage()
if 'id' in form:
   id_value=form.getvalue("id", "0")
   if id_value.isdigit():
      if len(id_value)>0:
         type_value = int(id_value[0])
      if len(id_value)>1:
         slice_value = int(id_value[1:])
if 'page' in form:
   page=form.getvalue("page","0")
   if page.isdigit():
         page_value=int(page)

if 'letter' in form:
   letter=form.getvalue("letter","А")

if type_value==0:
   header()
   main_menu()
   footer()

#########################################################
# Выбрана сортировка "По каталогам"
#
elif type_value==1:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+sopdscfg.SITE_MAINTITLE+'" href="sopds.cgi?id=0"/>')
   for (item_type,item_id,item_name,item_path,reg_date,item_title,item_genre) in opdsdb.getitemsincat(slice_value,sopdscfg.MAXITEMS,page_value):
       if item_type==1:
          id='1'+str(item_id)
       elif item_type==2:
          id='7'+str(item_id)
       else:
          id='0'
       enc_print('<entry>')
       enc_print('<title>'+item_title+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id='+id+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       if item_type==2:
          authors=""
          enc_print('<genre>'+item_genre+'</genre>')
          for (first_name,last_name) in opdsdb.getauthors(item_id):
              enc_print('<author><name>'+last_name+' '+first_name+'</name></author>')
              if len(authors)>0:
                 authors+=', '
              authors+=last_name+' '+first_name
          enc_print('<content type="text">'+authors+'</content>') 
       enc_print('</entry>')
   if page_value>0:
      prev_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value-1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'+prev_href+'" />')
   if opdsdb.next_page:
      next_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value+1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'+next_href+'" />')
   footer()
   opdsdb.closeDB()

#########################################################
# Выбрана сортировка "По авторам"
#
elif type_value==2:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+sopdscfg.SITE_MAINTITLE+'" href="sopds.cgi?id=0"/>')
   for (letter,cnt) in opdsdb.getauthor_letters():
       enc_print('<entry>')
       enc_print('<title>-= '+letter+' =-</title>')
       enc_print('<id>sopds.cgi?id=2</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id=5&amp;letter='+letter+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id=5&amp;letter='+letter+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' автора(ов).</content>')
       enc_print('</entry>')
   footer()
   opdsdb.closeDB()

#########################################################
# Выдача списка авторов
#
if type_value==5:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+sopdscfg.SITE_MAINTITLE+'" href="sopds.cgi?id=0"/>')
   for (author_id,first_name, last_name,cnt) in opdsdb.getauthorsbyl(letter,sopdscfg.MAXITEMS,page_value):
       id='6'+str(author_id)
       enc_print('<entry>')
       enc_print('<title>'+last_name+' '+first_name+'</title>')
       enc_print('<id>sopds.cgi?id=5&amp;letter='+letter+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' книг.</content>')
       enc_print('</entry>')
   if page_value>0:
      prev_href="sopds.cgi?id=5&amp;letter="+letter+"&amp;page="+str(page_value-1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'+prev_href+'" />')
   if opdsdb.next_page:
      next_href="sopds.cgi?id=5&amp;letter="+letter+"&amp;page="+str(page_value+1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'+next_href+'" />')
   footer()
   opdsdb.closeDB()

#########################################################
# Выдача списка книг по автору
#
if type_value==6:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   for (book_id,book_name,book_path,reg_date,book_title,book_genre) in opdsdb.getbooksforautor(slice_value,sopdscfg.MAXITEMS,page_value):
       id='7'+str(book_id)
       enc_print('<entry>')
       enc_print('<title>'+book_title+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id='+id+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       authors=""
       enc_print('<genre>'+book_genre+'</genre>')
       for (first_name,last_name) in opdsdb.getauthors(book_id):
           enc_print('<author><name>'+last_name+' '+first_name+'</name></author>')
           if len(authors)>0:
              authors+=', '
           authors+=last_name+' '+first_name
       enc_print('<content type="text">'+authors+'</content>')
       enc_print('</entry>')
   if page_value>0:
      prev_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value-1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'+prev_href+'" />')
   if opdsdb.next_page:
      next_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value+1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'+next_href+'" />')
   footer()
   opdsdb.closeDB()


#########################################################
# Выдача ссылок на книгу
#
elif type_value==7:
   id='7'+str(slice_value)
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" href="sopds.cgi?id=0" title="'+sopdscfg.SITE_MAINTITLE+'"/>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="self" href="sopds.cgi?id='+id+'"/>')
   (book_name,book_path,reg_date,format,title)=opdsdb.getbook(slice_value)
   id='8'+str(slice_value)
   idzip='9'+str(slice_value)
   enc_print('<entry>')
   enc_print('<title>Файл: '+book_name+'</title>')
   enc_print('<link type="application/'+format+'" rel="alternate" href="sopds.cgi?id='+id+'"/>')
   enc_print('<link type="application/'+format+'" href="sopds.cgi?id='+id+'" rel="http://opds-spec.org/acquisition" />')
   enc_print('<link type="application/'+format+'+zip" href="sopds.cgi?id='+idzip+'" rel="http://opds-spec.org/acquisition" />')
   authors=""
   for (first_name,last_name) in opdsdb.getauthors(slice_value):
       enc_print('<author><name>'+last_name+' '+first_name+'</name></author>')
       if len(authors)>0:
             authors+=', '
       authors+=last_name+' '+first_name
   enc_print('<content type="text">'+title+' Автор(ы): '+authors+'</content>')
   
   enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
   enc_print('<id>tag:book:'+id+'</id>')
   enc_print('</entry>')
   footer()
   opdsdb.closeDB()   

#########################################################
# Выдача файла книги
#
elif type_value==8:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   (book_name,book_path,reg_date,format,title)=opdsdb.getbook(slice_value)
   full_path=os.path.join(sopdscfg.ROOT_LIB,book_path)
   book_size=os.path.getsize(full_path.encode('utf-8'))
   # HTTP Header
   enc_print('Content-Type:application/octet-stream; name="'+book_name+'"')
   enc_print("Content-Disposition: attachment; filename="+translit(book_name))
   enc_print('Content-Transfer-Encoding: binary')
   enc_print('Content-Length: '+str(book_size))
   enc_print()
   fo=codecs.open(full_path.encode("utf-8"), "rb")
   str=fo.read()
   sys.stdout.buffer.write(str)
   fo.close()
   opdsdb.closeDB()

#########################################################
# Выдача файла книги в ZIP формате
#
elif type_value==9:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   (book_name,book_path,reg_date,format,title)=opdsdb.getbook(slice_value)
   full_path=os.path.join(sopdscfg.ROOT_LIB,book_path)
   # HTTP Header
   enc_print('Content-Type:application/zip; name="'+book_name+'"')
   enc_print("Content-Disposition: attachment; filename="+translit(book_name)+'.zip')
   enc_print('Content-Transfer-Encoding: binary')
   dio = io.BytesIO()
   z = zipfile.ZipFile(dio, 'w', zipfile.ZIP_DEFLATED)
   z.write(full_path.encode('utf-8'),translit(book_name))
   z.close()
   buf = dio.getvalue()
   enc_print('Content-Length: '+str(len(buf)))
   enc_print()
   sys.stdout.buffer.write(buf)
   opdsdb.closeDB()


