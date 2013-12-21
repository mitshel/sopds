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
import time

#######################################################################
#
# Парсим конфигурационный файл
#
cfg=sopdscfg.cfgreader()

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

def enc_print(string='', encoding='utf8'):
    sys.stdout.buffer.write(string.encode(encoding) + b'\n')

def header(charset='utf-8'):
   enc_print('Content-Type: text/xml; charset='+charset)
   enc_print()
   enc_print('<?xml version="1.0" encoding="'+charset+'"?>')
   enc_print('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opds="http://opds-spec.org/">')
   enc_print('<id>'+cfg.SITE_ID+'</id>')
   enc_print('<title>'+cfg.SITE_TITLE+'</title>')
   enc_print('<updated>'+time.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
   enc_print('<icon>'+cfg.SITE_ICON+'</icon>')
   enc_print('<author><name>'+cfg.SITE_AUTOR+'</name><uri>'+cfg.SITE_URL+'</uri><email>'+cfg.SITE_EMAIL+'</email></author>')

def footer():
   enc_print('</feed>')

def main_menu():
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   dbinfo=opdsdb.getdbinfo()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="/"/>')
   enc_print('<entry>')
   enc_print('<title>По каталогам</title>')
   enc_print('<content type="text">Каталогов: %s, книг: %s.</content>'%(dbinfo[2][0],dbinfo[0][0]))
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="sopds.cgi?id=01"/>')
   enc_print('<id>sopds.cgi?id=1</id></entry>')
   enc_print('<entry>')
   enc_print('<title>По авторам</title>')
   enc_print('<content type="text">Авторов: %s, книг: %s.</content>'%(dbinfo[1][0],dbinfo[0][0]))
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="sopds.cgi?id=02"/>')
   enc_print('<id>sopds.cgi?id=2</id></entry>')
   enc_print('<entry>')
   enc_print('<title>Последние добавленные</title>')
   enc_print('<content type="text">Книг: %s.</content>'%(cfg.MAXITEMS))
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="sopds.cgi?id=04"/>')
   enc_print('<id>sopds.cgi?id=4</id></entry>')
   opdsdb.closeDB()

def covers(cover,cover_type):
   if cover!=None and cover!='':
      enc_print( '<link href="../covers/%s" rel="http://opds-spec.org/image" type="%s" />'%(cover,cover_type) )
      enc_print( '<link href="../covers/%s" rel="x-stanza-cover-image" type="%s" />'%(cover,cover_type) )
      enc_print( '<link href="../covers/%s" rel="http://opds-spec.org/thumbnail" type="%s" />'%(cover,cover_type) )
      enc_print( '<link href="../covers/%s" rel="x-stanza-cover-image-thumbnail" type="%s" />'%(cover,cover_type) )

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
      if len(id_value)>1:
         type_value = int(id_value[0:2])
      if len(id_value)>2:
         slice_value = int(id_value[2:])
if 'page' in form:
   page=form.getvalue("page","0")
   if page.isdigit():
         page_value=int(page)

if type_value==0:
   header()
   main_menu()
   footer()

#########################################################
# Выбрана сортировка "По каталогам"
#
elif type_value==1:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=0"/>')
   for (item_type,item_id,item_name,item_path,reg_date,item_title,item_genre) in opdsdb.getitemsincat(slice_value,cfg.MAXITEMS,page_value):
       if item_type==1:
          id='01'+str(item_id)
       elif item_type==2:
          id='07'+str(item_id)
       else:
          id='00'
       enc_print('<entry>')
       enc_print('<title>'+item_title+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id=00</id>')
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
# Выбрана сортировка "По авторам" - выбор по первой букве автора
#
elif type_value==2:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=0"/>')
   for (letter,cnt) in opdsdb.getauthor_letters():
       if cfg.SPLITAUTHORS==0 or cnt<=cfg.SPLITAUTHORS:
          id='05'
       else:
          id='03'
       if len(letter)==0:
          id+='0000'
       else:
          id+='%04d'%ord(letter)
       if letter=='&':
          letter='&amp;'
       enc_print('<entry>')
       enc_print('<title>-= '+letter+' =-</title>')
       enc_print('<id>sopds.cgi?id=02</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' автора(ов).</content>')
       enc_print('</entry>')
   footer()
   opdsdb.closeDB()

#########################################################
# Выбрана сортировка "По авторам" - выбор по двум первым буквам автора
#
elif type_value==3:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   if slice_value==0:
      letter=""
   else:
      letter=chr(slice_value)
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=00"/>')
   for (letters,cnt) in opdsdb.getauthor_2letters(letter):
       if len(letters)==0:
         id='050000'
       elif len(letters)==1:
         id='05%04d'%(ord(letters))
       else:
         id='05%04d%04d'%(ord(letters[0]),ord(letters[1]))
       enc_print('<entry>')
       enc_print('<title>-= '+letters+' =-</title>')
       enc_print('<id>sopds.cgi?id='+id_value+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' автора(ов).</content>')
       enc_print('</entry>')
   footer()
   opdsdb.closeDB()

#########################################################
# Выбрана сортировка "Последние поступления"
#
elif type_value==4:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   for (book_id,book_name,book_path,reg_date,book_title) in opdsdb.getlastbooks(cfg.MAXITEMS):
       id='07'+str(book_id)
       enc_print('<entry>')
       enc_print('<title>'+book_title+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id=04</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       authors=""
       for (first_name,last_name) in opdsdb.getauthors(book_id):
           enc_print('<author><name>'+last_name+' '+first_name+'</name></author>')
           if len(authors)>0:
              authors+=', '
           authors+=last_name+' '+first_name
       enc_print('<content type="text">'+authors+'</content>')
       enc_print('</entry>')
   footer()
   opdsdb.closeDB()

#########################################################
# Выдача списка авторов
#
if type_value==5:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   if slice_value==0:
      letters=""
   elif slice_value>=10000:
      letters=chr(slice_value//10000)+chr(slice_value%10000)
   else:
      letters=chr(slice_value)
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=00"/>')
   for (author_id,first_name, last_name,cnt) in opdsdb.getauthorsbyl(letters,cfg.MAXITEMS,page_value):
       id='06'+str(author_id)
       enc_print('<entry>')
       enc_print('<title>'+last_name+' '+first_name+'</title>')
       enc_print('<id>sopds.cgi?id='+id_value+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' книг.</content>')
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
# Выдача списка книг по автору
#
if type_value==6:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   for (book_id,book_name,book_path,reg_date,book_title,book_genre,cover,cover_type) in opdsdb.getbooksforautor(slice_value,cfg.MAXITEMS,page_value):
       id='07'+str(book_id)
       enc_print('<entry>')
       enc_print('<title>'+book_title+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id='+id+'</id>')
       covers(cover,cover_type)
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
   id='07'+str(slice_value)
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" href="sopds.cgi?id=0" title="'+cfg.SITE_MAINTITLE+'"/>')
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="self" href="sopds.cgi?id='+id+'"/>')
   (book_name,book_path,reg_date,format,title,cat_type,cover,cover_type)=opdsdb.getbook(slice_value)
   id='08'+str(slice_value)
   idzip='09'+str(slice_value)
   enc_print('<entry>')
   enc_print('<title>Файл: '+book_name+'</title>')
   covers(cover,cover_type)
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
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   (book_name,book_path,reg_date,format,title,cat_type,cover,cover_type)=opdsdb.getbook(slice_value)
   full_path=os.path.join(cfg.ROOT_LIB,book_path)
   transname=translit(book_name)
   # HTTP Header
   enc_print('Content-Type:application/octet-stream; name="'+book_name+'"')
   enc_print("Content-Disposition: attachment; filename="+transname)
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
      z = zipfile.ZipFile(fz, 'r')
      book_size=z.getinfo(book_name).file_size
      enc_print('Content-Length: '+str(book_size))
      enc_print()
      fo= z.open(book_name)
      str=fo.read()
      sys.stdout.buffer.write(str)
      fo.close()
      z.close()
      fz.close()
   opdsdb.closeDB()

#########################################################
# Выдача файла книги в ZIP формате
#
elif type_value==9:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   (book_name,book_path,reg_date,format,title,cat_type,cover,cover_type)=opdsdb.getbook(slice_value)
   full_path=os.path.join(cfg.ROOT_LIB,book_path)
   transname=translit(book_name)
   # HTTP Header
   enc_print('Content-Type:application/zip; name="'+book_name+'"')
   enc_print("Content-Disposition: attachment; filename="+transname+'.zip')
   enc_print('Content-Transfer-Encoding: binary')
   if cat_type==sopdsdb.CAT_NORMAL:
      file_path=os.path.join(full_path,book_name)
      dio = io.BytesIO()
      z = zipfile.ZipFile(dio, 'w', zipfile.ZIP_DEFLATED)
      z.write(file_path.encode('utf-8'),transname)
      z.close()
      buf = dio.getvalue()
      enc_print('Content-Length: %s'%len(buf))
      enc_print()
      sys.stdout.buffer.write(buf)
   elif cat_type==sopdsdb.CAT_ZIP:
      fz=codecs.open(full_path.encode("utf-8"), "rb")
      zi = zipfile.ZipFile(fz, 'r', allowZip64=True)
      fo= zi.open(book_name)
      str=fo.read()
      fo.close()
      zi.close()
      fz.close()

      dio = io.BytesIO()
      zo = zipfile.ZipFile(dio, 'w', zipfile.ZIP_DEFLATED)
      zo.writestr(transname,str)
      zo.close()

      buf = dio.getvalue()
      enc_print('Content-Length: %s'%len(buf))
      enc_print()
      sys.stdout.buffer.write(buf)

   opdsdb.closeDB()


