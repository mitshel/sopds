#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sopdscfg
import sopdsdb
import codecs
import os
import io
import time
import sopdsparse
import base64
import subprocess
import zipf
import sopdswrap
from urllib import parse

modeCGI  = 0
modeWSGI = 1
modeINT  = 2

#######################################################################
#
# Вспомогательные функции
#
def translit(s):
   """Russian translit: converts 'привет'->'privet'"""
   assert s is not str, "Error: argument MUST be string"

   table1 = str.maketrans("абвгдеёзийклмнопрстуфхъыьэАБВГДЕЁЗИЙКЛМНОПРСТУФХЪЫЬЭ",  "abvgdeezijklmnoprstufh'y'eABVGDEEZIJKLMNOPRSTUFH'Y'E")
   table2 = {'ж':'zh','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ю':'ju','я':'ja',  'Ж':'Zh','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Sch','Ю':'Ju','Я':'Ja', '«':'\'', '»':'\'','"':'\'','\n':' '}
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

def opensearch(script):
    code='''<?xml version="1.0" encoding="utf-8"?>
            <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
            <ShortName>SimpleOPDS</ShortName>
            <LongName>SimpleOPDS</LongName>
            <Url type="application/atom+xml" template="{0}?searchTerm={{searchTerms}}" />
            <Image width="16" height="16">http://www.sopds.ru/favicon.ico</Image>
            <Tags />
            <Contact />
            <Developer />
            <Attribution />
            <SyndicationRight>open</SyndicationRight>
            <AdultContent>false</AdultContent>
            <Language>*</Language>
            <OutputEncoding>UTF-8</OutputEncoding>
            <InputEncoding>UTF-8</InputEncoding>
            </OpenSearchDescription>'''.format(script)
    return code

#######################################################################
#
# Основной класс OPDS-клиента
#
class opdsClient():
    def __init__(self,cfg,mode=modeCGI):
        self.cfg=cfg
        if mode==modeWSGI:
           self.modulePath=self.cfg.WSGI_PATH
        elif mode==modeINT:
           self.modulePath=''
        else:
           self.modulePath=self.cfg.CGI_PATH
        self.opdsdb=sopdsdb.opdsDatabase(self.cfg.DB_NAME,self.cfg.DB_USER,self.cfg.DB_PASS,self.cfg.DB_HOST,self.cfg.ROOT_LIB)

        self.template1=sopdswrap.opdsTemplate(self.modulePath)
        self.opdsWrapper=sopdswrap.baseWrapper(self.cfg, self.template1)

    def resetParams(self):
        self.id_value='0'
        self.type_value=0
        self.slice_value=0
        self.page_value=0
        self.ser_value=0
        self.alpha=0
        self.news=0
        self.np=0
        self.nl=''
        self.searchTerm=''
        self.user=None
#        self.response_status='200 Ok'
#        self.response_headers=[]
#        self.response_body=[]
        self.opdsWrapper.resetParams()

    def parseParams(self,qs):
        if 'id' in qs:
           self.id_value=qs.get("id")[0]
        else:
           self.id_value="0"
        if self.id_value.isdigit():
           if len(self.id_value)>1:
              self.type_value = int(self.id_value[0:2])
           if len(self.id_value)>2:
              self.slice_value = int(self.id_value[2:])

        if 'page' in qs:
           page=qs.get("page")[0]
           if page.isdigit():
              self.page_value=int(page)

        if 'searchType' in qs:
           searchType=qs.get("searchType")[0].strip()
           if searchType=='books': self.type_value=71
           if searchType=='authors': self.type_value=72
           if searchType=='series': self.type_value=73

        if 'searchTerm' in qs:
           self.searchTerm=qs.get("searchTerm")[0].strip()
           if self.type_value!=71 and self.type_value!=72 and self.type_value!=73: self.type_value=7
           self.slice_value=-1
           self.id_value='%02d&amp;searchTerm=%s'%(self.type_value,self.searchTerm)
        else:
           self.searchTerm=''

        if 'alpha' in qs:
           salpha=qs.get("alpha")[0].strip()
           if salpha.isdigit(): self.alpha=int(salpha)

        if 'news' in qs:
           self.news=1
           self.nl='&amp;news=1'
           self.np=self.cfg.NEW_PERIOD

        if 'ser' in qs:
           ser=qs.get("ser")[0]
           if ser.isdigit():
              self.ser_value=int(ser)

    def setUser(self,user):
        self.user=user

    def add_response_body(self, string='', encoding='utf8'):
        self.opdsWrapper.add_response_body(string,encoding)

    def add_response_binary(self, data):
        self.opdsWrapper.add_response_binary(data)

    def add_response_header(self,list):
        self.opdsWrapper.add_response_header(list)

    def set_response_status(self,status):
        self.opdsWrapper.set_response_status(status)

    def write_response_headers(self, encoding='utf8'):
        self.opdsWrapper.write_response_headers(encoding)

    def write_response(self):
        self.opdsWrapper.write_response()

    def get_response_status(self):
        return self.opdsWrapper.response_status

    def get_response_headers(self):
        return self.opdsWrapper.response_headers

    def get_response_body(self):
        return self.opdsWrapper.response_body

    def header(self, h_id=None, h_title=None, h_subtitle=None,charset='utf-8'):
        if h_id==None: h_id=self.cfg.SITE_ID
        if h_title==None: h_title=self.cfg.SITE_TITLE
        if h_subtitle==None: h_subtitle='Simple OPDS Catalog by www.sopds.ru. Version '+sopdscfg.VERSION
        self.opdsWrapper.header(h_id,h_title,h_subtitle,time.strftime("%Y-%m-%dT%H:%M:%SZ"))

    def footer(self):
        self.opdsWrapper.footer()

    def main_menu(self):
        dbinfo=self.opdsdb.getdbinfo(self.cfg.DUBLICATES_SHOW,self.cfg.BOOK_SHELF,self.user)
        self.opdsWrapper.main_menu(self.user,dbinfo)

    def new_menu(self):
        newinfo=self.opdsdb.getnewinfo(self.cfg.DUBLICATES_SHOW,self.cfg.NEW_PERIOD)
        self.opdsWrapper.new_menu(newinfo)

    def authors_submenu(self,author_id):
        self.opdsWrapper.authors_submenu(author_id)

    def entry_start(self):
        self.opdsWrapper.entry_start()

    def entry_head(self,e_title,e_date,e_id):
        self.opdsWrapper.entry_head(e_title,e_date,e_id)

    def entry_link_subsection(self,link_id):
         self.opdsWrapper.entry_link_subsection(link_id,self.nl)

    def entry_link_book(self,link_id,format):
         self.opdsWrapper.entry_link_book(link_id,format)

    def entry_authors(self,book_id,link_show=False):
        return self.opdsWrapper.entry_authors(self.opdsdb.getauthors(book_id))

    def entry_doubles(self,book_id):
        self.opdsWrapper.entry_doubles(book_id,self.opdsdb.getdoublecount(book_id))

    def entry_genres(self,book_id):
        return self.opdsWrapper.entry_genres(self.opdsdb.getgenres(book_id))

    def entry_series(self,book_id):
        return self.opdsWrapper.entry_series(self.opdsdb.getseries(book_id))

    def entry_covers(self,cover,cover_type,book_id):
        if self.cfg.COVER_SHOW!=0:
           self.opdsWrapper.entry_covers(book_id)

    def entry_content(self,e_content):
        self.opdsWrapper.entry_content(e_content)

    def entry_content2(self,annotation='',title='',authors='',genres='',filename='',filesize=0,docdate='',series=''):
         self.opdsWrapper.entry_content2(annotation,title,authors,genres,filename,filesize,docdate,series)

    def entry_finish(self):
        self.opdsWrapper.entry_finish()

    def page_control(self, page, link_id):
        if page>0:
           self.opdsWrapper.page_control_prev(page,link_id)
        if self.opdsdb.next_page:
           self.opdsWrapper.page_control_next(page,link_id)

    def alphabet_menu(self,iid_value):
        self.opdsWrapper.alphabet_menu(iid_value,self.nl) 

    def response_main(self):
        self.header()
        self.main_menu()
        self.footer()

    def response_catalogs(self):
        """ Выбрана сортировка 'По каталогам' """
        self.header('id:catalogs','Сортировка по каталогам хранения')
        for (item_type,item_id,item_name,item_path,reg_date,item_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getitemsincat(self.slice_value,self.cfg.MAXITEMS,self.page_value):
            self.entry_start()
            self.entry_head(item_title, reg_date, 'item:'+str(item_id))
            if item_type==1:
               id='01'+str(item_id)
               self.entry_link_subsection(id)
            if item_type==2:
               id='90'+str(item_id)
               self.entry_link_book(item_id,format)
               self.entry_covers(cover,cover_type,item_id)
               authors=self.entry_authors(item_id,True)
               genres=self.entry_genres(item_id)
               series=self.entry_series(item_id)
               self.entry_content2(annotation,item_title,authors,genres,item_name,fsize,docdate,series)
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_alpha(self):
        """ Вывод дополнительного меню алфавита для сортировок по Наименованиям, по Авторам и по Жанрам """
        self.header()
        self.alphabet_menu(self.id_value[2:])
        self.footer()

    def response_authors(self):
        """ Cортировка 'По авторам' - выбор по нескольким первым буквам автора """
        i=self.slice_value
        letter=""
        while i>0:
           letter=chr(i%10000)+letter
           i=i//10000
        self.header('id:preauthors:%s'%letter,'Выбор авторов "%s"'%letter)
        for (letters,cnt) in self.opdsdb.getauthor_2letters(letter,self.alpha,self.np):
            id=""
            for i in range(len(letters)):
                id+='%04d'%(ord(letters[i]))

            if self.cfg.SPLITTITLES==0 or cnt<=self.cfg.SPLITTITLES or len(letters)>10:
               id='12'+id
            else:
               id='02'+id

            self.entry_start()
            self.entry_head(letters, None, id)
            self.entry_link_subsection(id)
            self.entry_content('Всего: '+str(cnt)+' автора(ов).')
            self.entry_finish()
        self.footer()

    def response_series(self):
        """ Cортировка 'По сериям' - выбор по нескольким первым буквам серии """
        i=self.slice_value
        letter=""
        while i>0:
           letter=chr(i%10000)+letter
           i=i//10000
        self.header('id:preseries:%s'%letter,'Выбор серий "%s"'%letter)
        for (letters,cnt) in self.opdsdb.getseries_2letters(letter,self.alpha,self.np):
            id=""
            for i in range(len(letters)):
                id+='%04d'%(ord(letters[i]))

            if self.cfg.SPLITTITLES==0 or cnt<=self.cfg.SPLITTITLES or len(letters)>10:
               id='16'+id
            else:
               id='06'+id

            self.entry_start()
            self.entry_head(letters, None, id)
            self.entry_link_subsection(id)
            self.entry_content('Всего: '+str(cnt)+' серий.')
            self.entry_finish()
        self.footer()

    def response_titles(self):
        """ Cортировка 'По наименованию' - выбор по нескольким первым буквам наименования """
        i=self.slice_value
        letter=""
        while i>0:
           letter=chr(i%10000)+letter
           i=i//10000
        self.header('id:pretitle:%s'%letter,'Выбор наименований "%s"'%letter)
        for (letters,cnt) in self.opdsdb.gettitle_2letters(letter,self.cfg.DUBLICATES_SHOW,self.alpha,self.np):
            id=""
            for i in range(len(letters)):
                id+='%04d'%(ord(letters[i]))

            if self.cfg.SPLITTITLES==0 or cnt<=self.cfg.SPLITTITLES or len(letters)>10:
               id='13'+id
            else:
               id='03'+id

            self.entry_start()
            self.entry_head(letters, None, id)
            self.entry_link_subsection(id)
            self.entry_content('Всего: '+str(cnt)+' наименований.')
            self.entry_finish()
        self.footer()

    def response_titles_search(self):
        """ Выдача списка книг по наименованию или на основании поискового запроса """
        if self.slice_value>=0:
           i=self.slice_value
           letter=""
           while i>0:
              letter=chr(i%10000)+letter
              i=i//10000
        else:
           letter="%"+self.searchTerm

        self.header('id:title:%s'%letter,'Книги по наименованию "%s"'%letter)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksfortitle(letter,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='90'+str(book_id)
            self.entry_start()
            self.entry_head(book_title, reg_date, 'book:'+str(book_id))
            self.entry_link_book(book_id,format)
            self.entry_covers(cover,cover_type,book_id)
            authors=self.entry_authors(book_id,True)
            genres=self.entry_genres(book_id)
            series=self.entry_series(book_id)
            self.entry_doubles(book_id)
            self.entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_doubles(self):
        """ Вывод дубликатов для выбранной книги """
        self.header('id:doubles:%s'%self.slice_value,'Дубликаты для книги id=%s'%self.slice_value)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getdoubles(self.slice_value,self.cfg.MAXITEMS,self.page_value):
            id='90'+str(book_id)
            self.entry_start()
            self.entry_head(book_title, reg_date, 'book:'+str(book_id))
            self.entry_link_book(book_id,format)
            self.entry_covers(cover,cover_type,book_id)
            authors=self.entry_authors(book_id,True)
            genres=self.entry_genres(book_id)
            series=self.entry_series(book_id)
            self.entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()


    def response_genres_sections(self):
        """ Cортировка 'По жанрам' - показ секций """
        self.header('id:genre:sections','Список жанров')
        for (genre_id,genre_section,cnt) in self.opdsdb.getgenres_sections(self.cfg.DUBLICATES_SHOW,self.np):
            id='14'+str(genre_id)
            self.entry_start()
            self.entry_head(genre_section, None, 'genre:'+str(genre_id))
            self.entry_link_subsection(id)
            self.entry_content('Всего: '+str(cnt)+' книг.')
            self.entry_finish()
        self.footer()

    def response_genres_subsections(self):
        """ Cортировка 'По жанрам' - показ подсекций """
        self.header('id:genre:subsections:%s'%self.slice_value,'Список жанров (уровень 2)')
        for (genre_id,genre_subsection,cnt) in self.opdsdb.getgenres_subsections(self.slice_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='24'+str(genre_id)
            if self.cfg.ALPHA: id='30'+id
            self.entry_start()
            self.entry_head(genre_subsection, None, 'genre:'+str(genre_id))
            self.entry_link_subsection(id)
            self.entry_content('Всего: '+str(cnt)+' книг.')
            self.entry_finish()
        self.footer()

    def response_genres_books(self):
        """ Выдача списка книг по жанру """
        self.header('id:genres:%s'%self.slice_value,'Список книг по выбранному жанру')
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforgenre(self.slice_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.alpha,self.np):
            id='90'+str(book_id)
            self.entry_start()
            self.entry_head(book_title, reg_date, 'book:'+str(book_id))
            self.entry_link_book(book_id,format)
            self.entry_covers(cover,cover_type,book_id)
            authors=self.entry_authors(book_id,True)
            genres=self.entry_genres(book_id)
            series=self.entry_series(book_id)
            self.entry_doubles(book_id)
            self.entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_last(self):
        """ Cортировка 'Последние поступления' """  
        self.header('id:news','Последние поступления за %s дней'%self.cfg.NEW_PERIOD)
        self.new_menu()
        self.footer()

    def response_search_type(self):
        """ Выбор типа поиска по автору или наименованию или серии """
        self.header('id:search:%s'%self.searchTerm,'Поиск %s'%self.searchTerm)
        self.add_response_body('<link href="'+self.modulePath+'?id=09" rel="search" type="application/opensearchdescription+xml" />')
        self.add_response_body('<link href="'+self.modulePath+'?searchTerm={searchTerms}" rel="search" type="application/atom+xml" />')
        self.entry_start()
        self.entry_head('Поиск книг',None,'71')
        self.entry_content('Поиск книги по ее наименованию')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog" href="'+self.modulePath+'?searchType=books&amp;searchTerm='+parse.quote(self.searchTerm)+'" />')
        self.entry_finish()
        self.entry_start()
        self.entry_head('Поиск авторов',None,'72')
        self.entry_content('Поиск авторов по имени')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog" href="'+self.modulePath+'?searchType=authors&amp;searchTerm='+parse.quote(self.searchTerm)+'" />')
        self.entry_finish()
        self.entry_start()
        self.entry_head('Поиск серий',None,'73')
        self.entry_content('Поиск серий книг')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog" href="'+self.modulePath+'?searchType=series&amp;searchTerm='+parse.quote(self.searchTerm)+'" />')
        self.entry_finish()
        self.footer()

    def response_bookshelf(self):
        """ Выдача списка книг на книжной полке """
        self.header('id:bookshelf:%s'%self.user,'Книги пользователя %s'%self.user)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforuser(self.user,self.cfg.MAXITEMS,self.page_value):
            id='90'+str(book_id)
            self.entry_start()
            self.entry_head(book_title, reg_date, 'book:'+str(book_id))
            self.entry_link_book(book_id,format)
            self.entry_covers(cover,cover_type,book_id)
            authors=self.entry_authors(book_id,True)
            genres=self.entry_genres(book_id)
            series=self.entry_series(book_id)
            self.entry_doubles(book_id)
            self.entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_authors_search(self):
        """ Выдача списка авторов по имени или на основании поиска """
        if self.slice_value>0:
           i=self.slice_value
           letter=""
           while i>0:
              letter=chr(i%10000)+letter
              i=i//10000
        else:
           letter="%"+self.searchTerm

        self.header('id:authors:%s'%letter,'Авторы по имени "%s"'%letter)
        for (author_id,first_name, last_name,cnt) in self.opdsdb.getauthorsbyl(letter,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='22'+str(author_id)
            self.entry_start()
            self.entry_head(last_name+' '+first_name, None, 'author:'+str(author_id))
            self.entry_link_subsection(id)
            self.entry_content('Всего: '+str(cnt)+' книг.')
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_series_search(self):
        """ Выдача списка серий по названию или на основании поиска """
        if self.slice_value>0:
           i=self.slice_value
           letter=""
           while i>0:
              letter=chr(i%10000)+letter
              i=i//10000
        else:
           letter="%"+self.searchTerm

        self.header('id:series:%s'%letter,'Список серий книг "%s"'%letter)
        for (ser_id,ser,cnt) in self.opdsdb.getseriesbyl(letter,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='26'+str(ser_id)
            self.entry_start()
            self.entry_head(ser, None, 'series:'+str(ser_id))
            self.entry_link_subsection(id)
            self.entry_content('Всего: '+str(cnt)+' книг.')
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_authors_submenu(self):
        """ Выдача подменю вывода книг по автору - в случае флага новинок будет сразу переход к выдаче книг автора """
        (first_name,last_name)=self.opdsdb.getauthor_name(self.slice_value)
        self.header('id:autor:%s %s'%(last_name,first_name),'Книги автора %s %s'%(last_name,first_name))
        self.authors_submenu(self.slice_value)
        self.footer()

    def response_authors_series(self):
        """ Выдача серий по автору """
        (first_name,last_name)=self.opdsdb.getauthor_name(self.slice_value)
        self.header('id:autorseries:%s %s'%(last_name,first_name),'Серии книг автора %s %s'%(last_name,first_name))
        for (ser_id,ser,cnt) in self.opdsdb.getseriesforauthor(self.slice_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW):
            id='34'+str(self.slice_value)+'&amp;ser='+str(ser_id)
            self.entry_start()
            self.entry_head(ser, None, 'series:'+str(ser_id))
            self.entry_link_subsection(id)
            self.entry_content('Всего: '+str(cnt)+' книг.')
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_authors_alpha(self):
        """ Выдача списка книг по автору по алфавиту """
        (first_name,last_name)=self.opdsdb.getauthor_name(self.slice_value)
        self.header('id:autorbooks:%s %s'%(last_name,first_name),'Книги автора %s %s'%(last_name,first_name))
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforautor(self.slice_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='90'+str(book_id)
            self.entry_start()
            self.entry_head(book_title, reg_date, 'book:'+str(book_id))
            self.entry_link_book(book_id,format)
            self.entry_covers(cover,cover_type,book_id)
            authors=self.entry_authors(book_id,True)
            genres=self.entry_genres(book_id)
            series=self.entry_series(book_id)
            self.entry_doubles(book_id)
            self.entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_authors_series_books(self):
        """ Выдача списка книг по автору по выбранной серии (или вне серий если ser_value==0) """
        (first_name,last_name)=self.opdsdb.getauthor_name(self.slice_value)
        self.header('id:autorbooks:%s %s'%(last_name,first_name),'Книги автора %s %s'%(last_name,first_name))
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforautorser(self.slice_value,self.ser_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW):
            id='90'+str(book_id)
            self.entry_start()
            self.entry_head(book_title, reg_date, 'book:'+str(book_id))
            self.entry_link_book(book_id,format)
            self.entry_covers(cover,cover_type,book_id)
            authors=self.entry_authors(book_id,True)
            genres=self.entry_genres(book_id)
            series=self.entry_series(book_id)
            self.entry_doubles(book_id)
            self.entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_series_books(self):
        """ Выдача списка книг по серии """
        (ser_name,)=self.opdsdb.getser_name(self.slice_value)
        self.header('id:ser:%s'%ser_name,'Книги серии %s'%ser_name)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforser(self.slice_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='90'+str(book_id)
            self.entry_start()
            self.entry_head(book_title, reg_date, 'book:'+str(book_id))
            self.entry_link_book(book_id,format)
            self.entry_covers(cover,cover_type,book_id)
            authors=self.entry_authors(book_id,True)
            genres=self.entry_genres(book_id)
            series=self.entry_series(book_id)
            self.entry_doubles(book_id)
            self.entry_content2(annotation,book_title,authors,genres,book_name,fsize,docdate,series)
            self.entry_finish()
        self.page_control(self.page_value,self.id_value)
        self.footer()

    def response_book_file(self):
        """ Выдача файла книги """
        (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=self.opdsdb.getbook(self.slice_value)
        if self.cfg.BOOK_SHELF and self.user!=None: self.opdsdb.addbookshelf(self.user,self.slice_value)
        full_path=os.path.join(self.cfg.ROOT_LIB,book_path)
        if self.cfg.TITLE_AS_FN: transname=translit(title+'.'+format)
        else: transname=translit(book_name)
        if format=="fb2":    content_type='text/xml'
        elif format=="epub": content_type='application/epub+zip'
        elif format=="mobi": content_type='application/x-mobipocket-ebook'
        else:                content_type='application/octet-stream'
        # HTTP Header
        self.add_response_header([('Content-Type',content_type+'; name="'+transname+'"')])
        self.add_response_header([('Content-Disposition','attachment; filename="'+transname+'"')])
        self.add_response_header([('Content-Transfer-Encoding','binary')])
        if cat_type==sopdsdb.CAT_NORMAL:
           file_path=os.path.join(full_path,book_name)
           book_size=os.path.getsize(file_path.encode('utf-8'))
           self.add_response_header([('Content-Length',str(book_size))])
           fo=codecs.open(file_path.encode("utf-8"), "rb")
           s=fo.read()
           self.add_response_binary(s)
           fo.close()
        elif cat_type==sopdsdb.CAT_ZIP:
           fz=codecs.open(full_path.encode("utf-8"), "rb")
           z = zipf.ZipFile(fz, 'r', allowZip64=True)
           book_size=z.getinfo(book_name).file_size
           self.add_response_header([('Content-Length',str(book_size))])
           fo= z.open(book_name)
           s=fo.read()
           self.add_response_binary(s)
           fo.close()
           z.close()
           fz.close()

    def response_book_zip(self):
        """ Выдача файла книги в ZIP формате """
        (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=self.opdsdb.getbook(self.slice_value)
        if self.cfg.BOOK_SHELF and self.user!=None: self.opdsdb.addbookshelf(self.user,self.slice_value)
        full_path=os.path.join(self.cfg.ROOT_LIB,book_path)
        if self.cfg.TITLE_AS_FN: transname=translit(title+'.'+format)
        else: transname=translit(book_name)
        # HTTP Header
        self.add_response_header([('Content-Type','application/zip; name="'+transname+'"')])
        self.add_response_header([('Content-Disposition','attachment; filename="'+transname+'.zip"')])
        self.add_response_header([('Content-Transfer-Encoding','binary')])
        if cat_type==sopdsdb.CAT_NORMAL:
           file_path=os.path.join(full_path,book_name)
           dio = io.BytesIO()
           z = zipf.ZipFile(dio, 'w', zipf.ZIP_DEFLATED)
           z.write(file_path.encode('utf-8'),transname)
           z.close()
           buf = dio.getvalue()
           self.add_response_header([('Content-Length',str(len(buf)))])
           self.add_response_binary(buf)
        elif cat_type==sopdsdb.CAT_ZIP:
           fz=codecs.open(full_path.encode("utf-8"), "rb")
           zi = zipf.ZipFile(fz, 'r', allowZip64=True)
           fo= zi.open(book_name)
           s=fo.read()
           fo.close()
           zi.close()
           fz.close()

           dio = io.BytesIO()
           zo = zipf.ZipFile(dio, 'w', zipf.ZIP_DEFLATED)
           zo.writestr(transname,s)
           zo.close()

           buf = dio.getvalue()
           self.add_response_header([('Content-Length',str(len(buf)))])
           self.add_response_binary(buf)

    def response_book_convert(self):
        """ Выдача файла книги после конвертации в EPUB или mobi """
        (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=self.opdsdb.getbook(self.slice_value)
        if self.cfg.BOOK_SHELF and self.user!=None: self.opdsdb.addbookshelf(self.user, self.slice_value)
        full_path=os.path.join(self.cfg.ROOT_LIB,book_path)
        (n,e)=os.path.splitext(book_name)
        if self.type_value==93:
           convert_type='.epub'
           converter_path=self.cfg.FB2TOEPUB_PATH
           content_type='application/epub+zip'
        elif self.type_value==94:
           convert_type='.mobi'
           converter_path=self.cfg.FB2TOMOBI_PATH
           content_type='application/x-mobipocket-ebook'
        else:
           content_type='application/octet-stream'
        if self.cfg.TITLE_AS_FN: transname=translit(title)+convert_type
        else: transname=translit(n)+convert_type
        if cat_type==sopdsdb.CAT_NORMAL:
           tmp_fb2_path=None
           file_path=os.path.join(full_path,book_name)
        elif cat_type==sopdsdb.CAT_ZIP:
           fz=codecs.open(full_path.encode("utf-8"), "rb")
           z = zipf.ZipFile(fz, 'r', allowZip64=True)
           z.extract(book_name,self.cfg.TEMP_DIR)
           tmp_fb2_path=os.path.join(self.cfg.TEMP_DIR,book_name)
           file_path=tmp_fb2_path

        tmp_conv_path=os.path.join(self.cfg.TEMP_DIR,transname)
        proc = subprocess.Popen(("%s %s %s"%(converter_path,("\"%s\""%file_path),"\"%s\""%tmp_conv_path)).encode('utf8'), shell=True, stdout=subprocess.PIPE)
        out = proc.stdout.readlines()

        if os.path.isfile(tmp_conv_path):
           fo=codecs.open(tmp_conv_path, "rb")
           s=fo.read()
           # HTTP Header
           self.add_response_header([('Content-Type',content_type+'; name="'+transname+'"')])
           self.add_response_header([('Content-Disposition','attachment; filename="'+transname+'"')])
           self.add_response_header([('Content-Transfer-Encoding','binary')])
           self.add_response_header([('Content-Length',str(len(s)))])
           self.add_response_binary(s)
           fo.close()
        else:
           self.set_response_status('404 Not Found')

        try: os.remove(tmp_fb2_path.encode('utf-8'))
        except: pass
        try: os.remove(tmp_conv_path)
        except: pass

    def response_book_cover(self):
        """ Выдача Обложки На лету """
        (book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=self.opdsdb.getbook(self.slice_value)
        c0=0
        if format=='fb2':
           full_path=os.path.join(self.cfg.ROOT_LIB,book_path)
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
                self.add_response_header([('Content-Type',ictype)])
                self.add_response_binary(dstr)
                c0=1
              except:
                c0=0

        if c0==0:
           if os.path.exists(sopdscfg.NOCOVER_PATH):
              self.add_response_header([('Content-Type','image/jpeg')])
              f=open(sopdscfg.NOCOVER_PATH,"rb")
              self.add_response_binary(f.read())
              f.close()
           else:
              self.set_response_status('404 Not Found')

    def response_search(self):
        self.add_response_header([('Content-Type','text/xml')])
        self.add_response_body(opensearch(self.modulePath))

    def make_response(self):
        self.opdsdb.openDB()

        if self.type_value==0:
           self.response_main()
        elif self.type_value==1:
           self.response_catalogs()

        elif self.type_value==2:
           self.response_authors()
        elif self.type_value==12 or self.type_value==72:
           self.response_authors_search()
        elif self.type_value==22 and self.np==0:
           self.response_authors_submenu()
        elif self.type_value==31:
           self.response_authors_series()
        elif self.type_value==33 or (self.type_value==22 and self.np!=0):
           self.response_authors_alpha()
        elif self.type_value==34:
           self.response_authors_series_books()

        elif self.type_value==3:
           self.response_titles()
        elif self.type_value==13 or self.type_value==71:
           self.response_titles_search()
        elif self.type_value==23:
           self.response_doubles()

        elif self.type_value==4:
           self.response_genres_sections()
        elif self.type_value==14:
           self.response_genres_subsections()
        elif self.type_value==24:
           self.response_genres_books()

        elif self.type_value==5:
           self.response_last()

        elif self.type_value==6:
           self.response_series()
        elif self.type_value==16 or self.type_value==73:
           self.response_series_search()
        elif self.type_value==26:
           self.response_series_books()

        elif self.type_value==7:
           self.response_search_type()
        elif self.type_value==8:
           self.response_bookshelf()
        elif self.type_value==30:
           self.response_alpha()

        elif self.type_value==9:
           self.response_search()

        elif self.type_value==91:
           self.response_book_file()
        elif self.type_value==92:
           self.response_book_zip()
        elif self.type_value==93 or self.type_value==94:
           self.response_book_convert()
        elif self.type_value==99:
           self.response_book_cover()
        
        self.opdsdb.closeDB()



