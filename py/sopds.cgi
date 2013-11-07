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
   enc_print('<id>http://bookserver.revues.org/OA</id>    </entry>')

###########################################################################
# Основной код программы
#

locale.setlocale(locale.LC_ALL,'ru_RU.UTF-8')

type_value=0
slice_value=0
page_value=0
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

if type_value==0:
   header()
   main_menu()
   footer()

elif type_value==1:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+sopdscfg.SITE_MAINTITLE+'" href="sopds.cgi?id=0"/>')
   for (item_type,item_id,item_name,item_path,reg_date) in opdsdb.getitemsincat(slice_value,sopdscfg.MAXITEMS,page_value):
       if item_type==1:
          id='1'+str(item_id)
       elif item_type==2:
          id='2'+str(item_id)
       else:
          id='0'
       enc_print('<entry>')
       enc_print('<title>'+item_name+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id='+id+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('</entry>')
   if page_value>0:
      prev_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value-1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'+prev_href+'" />')
   if opdsdb.next_page:
      next_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value+1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'+next_href+'" />')
   footer()
   opdsdb.closeDB()

elif type_value==2:
   id='2'+str(slice_value)
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" href="sopds.cgi?id=0" title="'+sopdscfg.SITE_MAINTITLE+'"/>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="self" href="sopds.cgi?id='+id+'"/>')
   (book_name,book_path,reg_date,format)=opdsdb.getbook(slice_value)
   id='3'+str(slice_value)
   idzip='4'+str(slice_value)
   enc_print('<entry>')
   enc_print('<title>Книга:'+book_name+'</title>')
   enc_print('<link type="application/'+format+'" rel="alternate" href="sopds.cgi?id='+id+'"/>')
   enc_print('<link type="application/'+format+'" href="sopds.cgi?id='+id+'" rel="http://opds-spec.org/acquisition" />')
   enc_print('<link type="application/'+format+'+zip" href="sopds.cgi?id='+idzip+'" rel="http://opds-spec.org/acquisition" />')
   enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
   enc_print('<id>tag:book:'+id+'</id>')
   enc_print('</entry>')
   footer()
   opdsdb.closeDB()   

elif type_value==3:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   (book_name,book_path,reg_date,format)=opdsdb.getbook(slice_value)
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

elif type_value==4:
   opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
   opdsdb.openDB()
   (book_name,book_path,reg_date,format)=opdsdb.getbook(slice_value)
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


