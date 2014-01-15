#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import sopdscfg
import sopdsdb
import cgi
import codecs
import os
import urllib.parse
import zipf
import io
import locale
import time
import sopdsparse
import base64

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

def websym(s):
    """Replace special web-symbols"""
    result = s
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
   enc_print('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opds="http://opds-spec.org/">')
   enc_print('<id>'+cfg.SITE_ID+'</id>')
   enc_print('<title>'+cfg.SITE_TITLE+'</title>')
   enc_print('<updated>'+time.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
   enc_print('<icon>'+cfg.SITE_ICON+'</icon>')
   enc_print('<author><name>'+cfg.SITE_AUTOR+'</name><uri>'+cfg.SITE_URL+'</uri><email>'+cfg.SITE_EMAIL+'</email></author>')
#   enc_print('<cover_show>'+str(cfg.COVER_SHOW)+'</cover_show>')

def footer():
   enc_print('</feed>')

def main_menu():
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   dbinfo=opdsdb.getdbinfo(cfg.DUBLICATES_SHOW)
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="/"/>')
   enc_print('<link href="opensearch.xml" rel="search" type="application/opensearchdescription+xml" />')
   enc_print('<link href="sopds.cgi?search={searchTerms}" rel="search" type="application/atom+xml" />')
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
   enc_print('<title>По наименованию</title>')
   enc_print('<content type="text">Авторов: %s, книг: %s.</content>'%(dbinfo[1][0],dbinfo[0][0]))
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="sopds.cgi?id=03"/>')
   enc_print('<id>sopds.cgi?id=10</id></entry>')
   enc_print('<entry>')
   enc_print('<title>По Жанрам</title>')
   enc_print('<content type="text">Авторов: %s, книг: %s.</content>'%(dbinfo[1][0],dbinfo[0][0]))
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="sopds.cgi?id=11"/>')
   enc_print('<id>sopds.cgi?id=11</id></entry>')
   enc_print('<entry>')
   enc_print('<title>Последние добавленные</title>')
   enc_print('<content type="text">Книг: %s.</content>'%(cfg.MAXITEMS))
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="sopds.cgi?id=04"/>')
   enc_print('<id>sopds.cgi?id=4</id></entry>')
   opdsdb.closeDB()

def covers(cover,cover_type,book_id):
   have_extracted_cover=0
   if cfg.COVER_SHOW!=0:
      if cfg.COVER_SHOW!=2:
         if cover!=None and cover!='':
            enc_print( '<link href="../covers/%s" rel="http://opds-spec.org/image" type="%s" />'%(cover,cover_type) )
            enc_print( '<link href="../covers/%s" rel="x-stanza-cover-image" type="%s" />'%(cover,cover_type) )
            enc_print( '<link href="../covers/%s" rel="http://opds-spec.org/thumbnail" type="%s" />'%(cover,cover_type) )
            enc_print( '<link href="../covers/%s" rel="x-stanza-cover-image-thumbnail" type="%s" />'%(cover,cover_type) )
            have_extracted_cover=1
      if cfg.COVER_SHOW==2 or (cfg.COVER_SHOW==3 and have_extracted_cover==0):
            id='99'+str(book_id)
            enc_print( '<link href="sopds.cgi?id=%s" rel="http://opds-spec.org/image" />'%(id) )
            enc_print( '<link href="sopds.cgi?id=%s" rel="x-stanza-cover-image" />'%(id) )
            enc_print( '<link href="sopds.cgi?id=%s" rel="http://opds-spec.org/thumbnail" />'%(id) )
            enc_print( '<link href="sopds.cgi?id=%s" rel="x-stanza-cover-image-thumbnail" />'%(id) )


###########################################################################################################
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
if 'search' in form:
   searchTerm=form.getvalue("search","")
   type_value=10
   slice_value=-1
   id_value='10&amp;search='+searchTerm

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
   for (item_type,item_id,item_name,item_path,reg_date,item_title) in opdsdb.getitemsincat(slice_value,cfg.MAXITEMS,page_value):
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
# Выбрана сортировка "По авторам" - выбор по несскольким первым буквам автора
#
elif type_value==2:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()

   i=slice_value
   letter=""
   while i>0:
      letter=chr(i%10000)+letter
      i=i//10000

   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=00"/>')
   for (letters,cnt) in opdsdb.getauthor_2letters(letter):

       id=""
       for i in range(len(letters)):
           id+='%04d'%(ord(letters[i]))

       if cfg.SPLITTITLES==0 or cnt<=cfg.SPLITTITLES or len(letters)>10:
         id='05'+id
       else:
         id='02'+id

       enc_print('<entry>')
       enc_print('<title>-= '+websym(letters)+' =-</title>')
       enc_print('<id>sopds.cgi?id='+id_value+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' автора(ов).</content>')
       enc_print('</entry>')
   footer()
   opdsdb.closeDB()

#########################################################
# Выбрана сортировка "По наименованию" - выбор по нескольким первым буквам наименования
#
elif type_value==3:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()

   i=slice_value
   letter=""
   while i>0:
      letter=chr(i%10000)+letter
      i=i//10000

   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=00"/>')
   for (letters,cnt) in opdsdb.gettitle_2letters(letter,cfg.DUBLICATES_SHOW):
      
       id=""
       for i in range(len(letters)):
           id+='%04d'%(ord(letters[i]))

       if cfg.SPLITTITLES==0 or cnt<=cfg.SPLITTITLES or len(letters)>10:
         id='10'+id
       else:
         id='03'+id
   
       enc_print('<entry>')
       enc_print('<title>-= '+websym(letters)+' =-</title>')
       enc_print('<id>sopds.cgi?id='+id_value+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' наименований.</content>')
       enc_print('</entry>')
   footer()
   opdsdb.closeDB()

#########################################################
# Выдача списка книг по наименованию или на основании поискового запроса
#
if type_value==10:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()

   if slice_value>=0:
      i=slice_value
      letter=""
      while i>0:
         letter=chr(i%10000)+letter
         i=i//10000
   else:
      letter="%"+searchTerm

   header()
   for (book_id,book_name,book_path,reg_date,book_title,cover,cover_type) in opdsdb.getbooksfortitle(letter,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW):
       id='07'+str(book_id)
       enc_print('<entry>')
       enc_print('<title>'+websym(book_title)+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id='+id+'</id>')
       covers(cover,cover_type,book_id)
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
   if page_value>0:
      prev_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value-1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'+prev_href+'" />')
   if opdsdb.next_page:
      next_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value+1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'+next_href+'" />')
   footer()
   opdsdb.closeDB()


#########################################################
# Выбрана сортировка "По жанрам" - показ секций
#
elif type_value==11:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=00"/>')
   for (genre_id,genre_section,cnt) in opdsdb.getgenres_sections():
       id='12'+str(genre_id)
       enc_print('<entry>')
       enc_print('<title>'+genre_section+'</title>')
       enc_print('<id>sopds.cgi?id='+id_value+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' книг.</content>')
       enc_print('</entry>')
   footer()
   opdsdb.closeDB()

#########################################################
# Выбрана сортировка "По жанрам" - показ подсекций
#
elif type_value==12:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=00"/>')
   for (genre_id,genre_subsection,cnt) in opdsdb.getgenres_subsections(slice_value):
       id='13'+str(genre_id)
       enc_print('<entry>')
       enc_print('<title>'+genre_subsection+'</title>')
       enc_print('<id>sopds.cgi?id='+id_value+'</id>')
       enc_print('<link type="application/atom+xml" rel="alternate" href="sopds.cgi?id='+id+'"/>')
       enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="sopds.cgi?id='+id+'"/>')
       enc_print('<content type="text"> Всего: '+str(cnt)+' книг.</content>')
       enc_print('</entry>')
   footer()
   opdsdb.closeDB()

#########################################################
# Выдача списка книг по жанру
#
if type_value==13:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   header()
   for (book_id,book_name,book_path,reg_date,book_title,cover,cover_type) in opdsdb.getbooksforgenre(slice_value,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW):
       id='07'+str(book_id)
       enc_print('<entry>')
       enc_print('<title>'+websym(book_title)+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id='+id+'</id>')
       covers(cover,cover_type,book_id)
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
   if page_value>0:
      prev_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value-1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'+prev_href+'" />')
   if opdsdb.next_page:
      next_href="sopds.cgi?id="+id_value+"&amp;page="+str(page_value+1)
      enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'+next_href+'" />')
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
       enc_print('<title>'+websym(book_title)+'</title>')
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

   i=slice_value
   letter=""
   while i>0:
      letter=chr(i%10000)+letter
      i=i//10000

   header()
   enc_print('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" rel="start" title="'+cfg.SITE_MAINTITLE+'" href="sopds.cgi?id=00"/>')
   for (author_id,first_name, last_name,cnt) in opdsdb.getauthorsbyl(letter,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW):
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
   for (book_id,book_name,book_path,reg_date,book_title,cover,cover_type) in opdsdb.getbooksforautor(slice_value,cfg.MAXITEMS,page_value,cfg.DUBLICATES_SHOW):
       id='07'+str(book_id)
       enc_print('<entry>')
       enc_print('<title>'+websym(book_title)+'</title>')
       enc_print('<updated>'+reg_date.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
       enc_print('<id>sopds.cgi?id='+id+'</id>')
       covers(cover,cover_type,book_id)
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
   (book_name,book_path,reg_date,format,title,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
   id='08'+str(slice_value)
   idzip='09'+str(slice_value)
   enc_print('<entry>')
   enc_print('<title>Файл: '+book_name+'</title>')
   covers(cover,cover_type,slice_value)
   enc_print('<link type="application/'+format+'" rel="alternate" href="sopds.cgi?id='+id+'"/>')
   enc_print('<link type="application/'+format+'" href="sopds.cgi?id='+id+'" rel="http://opds-spec.org/acquisition" />')
   enc_print('<link type="application/'+format+'+zip" href="sopds.cgi?id='+idzip+'" rel="http://opds-spec.org/acquisition" />')
   authors=""
   for (first_name,last_name) in opdsdb.getauthors(slice_value):
       enc_print('<author><name>'+last_name+' '+first_name+'</name></author>')
       if len(authors)>0:
             authors+=', '
       authors+=last_name+' '+first_name
   genres=""
   for (section,genre) in opdsdb.getgenres(slice_value):
       enc_print('<category term="%s" label="%s" />'%(genre,genre))
       if len(genres)>0:
             genres+=', '
       genres+=genre

   enc_print('<content type="text"> Название книги: '+title+'\nАвтор(ы): '+authors+'\nЖанры: '+genres+'\nРазмер файла : '+str(fsize//1000)+'Кб</content>')
   
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
   (book_name,book_path,reg_date,format,title,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
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
      z = zipf.ZipFile(fz, 'r', allowZip64=True, codepage=cfg.ZIP_CODEPAGE)
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
   (book_name,book_path,reg_date,format,title,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
   full_path=os.path.join(cfg.ROOT_LIB,book_path)
   transname=translit(book_name)
   # HTTP Header
   enc_print('Content-Type:application/zip; name="'+book_name+'"')
   enc_print("Content-Disposition: attachment; filename="+transname+'.zip')
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
      zi = zipf.ZipFile(fz, 'r', allowZip64=True, codepage=cfg.ZIP_CODEPAGE)
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

   opdsdb.closeDB()

#########################################################
# Выдача Обложки На лету
#
elif type_value==99:
   opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
   opdsdb.openDB()
   (book_name,book_path,reg_date,format,title,cat_type,cover,cover_type,fsize)=opdsdb.getbook(slice_value)
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
         z = zipf.ZipFile(fz, 'r', allowZip64=True, codepage=cfg.ZIP_CODEPAGE)
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


