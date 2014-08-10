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
        self.response_status='200 Ok'
        self.response_headers=[]
        self.response_body=[]

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
        self.response_body+=[string.encode(encoding)]

    def add_response_binary(self, data):
        self.response_body+=[data]

    def add_response_header(self,list):
        self.response_headers+=list

    def set_response_status(self,status):
        self.response_status=status

    def write_response_headers(self, encoding='utf8'):
        sys.stdout.buffer.write(b'Status: '+self.response_status.encode(encoding)+ b'\n')
        for header in self.response_headers:
            (a,b)=header
            sys.stdout.buffer.write(a.encode(encoding)+b': '+b.encode(encoding) + b'\n')
        sys.stdout.buffer.write(b'\n')

    def write_response(self):
        for element in self.response_body:
            sys.stdout.buffer.write(element + b'\n')

    def header(self, h_id=None, h_title=None, h_subtitle=None,charset='utf-8'):
        if h_id==None: h_id=self.cfg.SITE_ID
        if h_title==None: h_title=self.cfg.SITE_TITLE
        if h_subtitle==None: h_subtitle='Simple OPDS Catalog by www.sopds.ru. Version '+sopdscfg.VERSION
        self.add_response_header([('Content-Type','text/xml; charset='+charset)])
        self.add_response_body('<?xml version="1.0" encoding="'+charset+'"?>')
        self.add_response_body('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">')
        self.add_response_body('<id>%s</id>'%h_id)
        self.add_response_body('<title>%s</title>'%h_title)
        self.add_response_body('<subtitle>%s</subtitle>'%h_subtitle)
        self.add_response_body('<updated>'+time.strftime("%Y-%m-%dT%H:%M:%SZ")+'</updated>')
        self.add_response_body('<icon>'+self.cfg.SITE_ICON+'</icon>')
        self.add_response_body('<author><name>'+self.cfg.SITE_AUTOR+'</name><uri>'+self.cfg.SITE_URL+'</uri><email>'+self.cfg.SITE_EMAIL+'</email></author>')
        self.add_response_body('<link type="application/atom+xml" rel="start" href="'+self.modulePath+'?id=00"/>')

    def footer(self):
        self.add_response_body('</feed>')

    def main_menu(self):
        if self.cfg.ALPHA: am='30'
        else: am=''
        dbinfo=self.opdsdb.getdbinfo(self.cfg.DUBLICATES_SHOW,self.cfg.BOOK_SHELF,self.user)
        self.add_response_body('<link href="'+self.modulePath+'?id=09" rel="search" type="application/opensearchdescription+xml" />')
        self.add_response_body('<link href="'+self.modulePath+'?searchTerm={searchTerms}" rel="search" type="application/atom+xml" />')
        self.add_response_body('<entry>')
        self.add_response_body('<title>По каталогам</title>')
        self.add_response_body('<content type="text">Каталогов: %s, книг: %s.</content>'%(dbinfo[2][1],dbinfo[0][1]))
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id=01"/>')
        self.add_response_body('<id>id:01</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>По авторам</title>')
        self.add_response_body('<content type="text">Авторов: %s.</content>'%dbinfo[1][1])
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+am+'02"/>')
        self.add_response_body('<id>id:02</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>По наименованию</title>')
        self.add_response_body('<content type="text">Книг: %s.</content>'%dbinfo[0][1])
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+am+'03"/>')
        self.add_response_body('<id>id:03</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>По Жанрам</title>')
        self.add_response_body('<content type="text">Жанров: %s.</content>'%dbinfo[3][1])
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id=04"/>')
        self.add_response_body('<id>id:04</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>По Сериям</title>')
        self.add_response_body('<content type="text">Серий: %s.</content>'%dbinfo[4][1])
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+am+'06"/>')
        self.add_response_body('<id>id:06</id></entry>')
        if self.cfg.NEW_PERIOD!=0:
           self.add_response_body('<entry>')
           self.add_response_body('<title>Новинки за %s суток</title>'%self.cfg.NEW_PERIOD)
           self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id=05"/>')
           self.add_response_body('<id>id:05</id></entry>')
        if self.cfg.BOOK_SHELF and self.user!=None:
           self.add_response_body('<entry>')
           self.add_response_body('<title>Книжная полка для %s</title>'%self.user)
           self.add_response_body('<content type="text">Книг: %s.</content>'%dbinfo[5][1])
           self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id=08"/>')
           self.add_response_body('<id>id:08</id></entry>')

    def new_menu(self):
        if self.cfg.ALPHA: am='30'
        else: am=''
        newinfo=self.opdsdb.getnewinfo(self.cfg.DUBLICATES_SHOW,self.cfg.NEW_PERIOD)
        self.add_response_body('<entry>')
        self.add_response_body('<title>Все новинки за %s суток</title>'%self.cfg.NEW_PERIOD)
        self.add_response_body('<content type="text">Новых книг: %s.</content>'%newinfo[0][1])
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+am+'03&amp;news=1"/>')
        self.add_response_body('<id>id:03:news</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>Новинки по авторам</title>')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+am+'02&amp;news=1"/>')
        self.add_response_body('<id>id:02:news</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>Новинки по Жанрам</title>')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id=04&amp;news=1"/>')
        self.add_response_body('<id>id:04:news</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>Новинки по Сериям</title>')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+am+'06&amp;news=1"/>')
        self.add_response_body('<id>id:06:news</id></entry>')

    def authors_submenu(self,author_id):
        self.add_response_body('<entry>')
        self.add_response_body('<title>Книги по сериям</title>')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id=31'+str(author_id)+'"/>')
        self.add_response_body('<id>id:31:authors</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>Книги вне серий</title>')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id=34'+str(author_id)+'"/>')
        self.add_response_body('<id>id:32:authors</id></entry>')
        self.add_response_body('<entry>')
        self.add_response_body('<title>Книги по алфавиту</title>')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id=33'+str(author_id)+'"/>')
        self.add_response_body('<id>id:33:authors</id></entry>')

    def entry_start(self):
        self.add_response_body('<entry>')

    def entry_head(self,e_title,e_date,e_id):
        self.add_response_body('<title>'+websym(e_title)+'</title>')
        if e_date!=None:
           self.add_response_body('<updated>'+e_date.strftime("%Y-%m-%dT%H:%M:%S")+'</updated>')
        self.add_response_body('<id>id:'+e_id+'</id>')

    def entry_link_subsection(self,link_id):
        self.add_response_body('<link type="application/atom+xml" rel="alternate" href="'+self.modulePath+'?id='+link_id+self.nl+'"/>')
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="'+self.modulePath+'?id='+link_id+self.nl+'"/>')

    def entry_link_book(self,link_id,format):
        str_id=str(link_id)
        self.add_response_body('<link type="application/'+format+'" rel="alternate" href="'+self.modulePath+'?id=91'+str_id+'"/>')
        if format.lower()=='fb2' and self.cfg.FB2TOEPUB:
           self.add_response_body('<link type="application/epub" href="'+self.modulePath+'?id=93'+str_id+'" rel="http://opds-spec.org/acquisition" />')
           self.add_response_body('<link type="application/epub+zip" href="'+self.modulePath+'?id=93'+str_id+'" rel="http://opds-spec.org/acquisition" />')
        if format.lower()=='fb2' and self.cfg.FB2TOMOBI:
           self.add_response_body('<link type="application/mobi" href="'+self.modulePath+'?id=94'+str_id+'" rel="http://opds-spec.org/acquisition" />')
           self.add_response_body('<link type="application/mobi+zip" href="'+self.modulePath+'?id=94'+str_id+'" rel="http://opds-spec.org/acquisition" />')
        self.add_response_body('<link type="application/'+format+'" href="'+self.modulePath+'?id=91'+str_id+'" rel="http://opds-spec.org/acquisition" />')
        self.add_response_body('<link type="application/'+format+'+zip" href="'+self.modulePath+'?id=92'+str_id+'" rel="http://opds-spec.org/acquisition" />')

    def entry_authors(self,book_id,link_show=False):
        authors=""
        for (author_id,first_name,last_name) in self.opdsdb.getauthors(book_id):
            self.add_response_body('<author><name>'+last_name+' '+first_name+'</name></author>')
            if len(authors)>0:
               authors+=', '
            authors+=last_name+' '+first_name
            if link_show:
               author_ref=self.modulePath+'?id=22'+str(author_id)
               self.add_response_body('<link href="'+author_ref+'" rel="related" type="application/atom+xml;profile=opds-catalog" title="Все книги автора '+websym(last_name,True)+' '+websym(first_name,True)+'" />')
            else:
               self.add_response_body('<content type="text">'+authors+'</content>')
        return authors

    def entry_doubles(self,book_id):
        dcount=self.opdsdb.getdoublecount(book_id)
        if dcount>0:
           doubles_ref=self.modulePath+'?id=23'+str(book_id)
           self.add_response_body('<link href="'+doubles_ref+'" rel="related" type="application/atom+xml;profile=opds-catalog" title="Дубликаты книги" />')

    def entry_genres(self,book_id):
        genres=""
        for (section,genre) in self.opdsdb.getgenres(book_id):
            self.add_response_body('<category term="%s" label="%s" />'%(genre,genre))
            if len(genres)>0:
                  genres+=', '
            genres+=genre
        return genres

    def entry_series(self,book_id):
        series=""
        for (ser,ser_no) in self.opdsdb.getseries(book_id):
            if len(series)>0:
                  series+=', '
            series+=ser
            if ser_no > 0:
                  series += ' #' + str(ser_no)
        return series

    def entry_covers(self,cover,cover_type,book_id):
        have_extracted_cover=0
        if self.cfg.COVER_SHOW!=0:
             id='99'+str(book_id)
             self.add_response_body( '<link href="%s?id=%s" rel="http://opds-spec.org/image" type="image/jpeg" />'%(self.modulePath,id) )
             self.add_response_body( '<link href="%s?id=%s" rel="x-stanza-cover-image" type="image/jpeg" />'%(self.modulePath,id) )
             self.add_response_body( '<link href="%s?id=%s" rel="http://opds-spec.org/thumbnail"  type="image/jpeg" />'%(self.modulePath,id) )
             self.add_response_body( '<link href="%s?id=%s" rel="x-stanza-cover-image-thumbnail"  type="image/jpeg" />'%(self.modulePath,id) )

    def entry_content(self,e_content):
        self.add_response_body('<content type="text">'+websym(e_content)+'</content>')

    def entry_content2(self,annotation='',title='',authors='',genres='',filename='',filesize=0,docdate='',series=''):
        self.add_response_body('<content type="text/html">')
        if title!='':
           self.add_response_body('&lt;b&gt;Название книги:&lt;/b&gt; '+websym(title)+'&lt;br/&gt;')
        if authors!='':
           self.add_response_body('&lt;b&gt;Авторы:&lt;/b&gt; '+websym(authors)+'&lt;br/&gt;')
        if genres!='':
           self.add_response_body('&lt;b&gt;Жанры:&lt;/b&gt; '+websym(genres)+'&lt;br/&gt;')
        if series!='':
           self.add_response_body('&lt;b&gt;Серии:&lt;/b&gt; '+websym(series)+'&lt;br/&gt;')
        if filename!='':
           self.add_response_body('&lt;b&gt;Файл:&lt;/b&gt; '+websym(filename)+'&lt;br/&gt;')
        if filesize>0:
           self.add_response_body('&lt;b&gt;Размер файла:&lt;/b&gt; '+str(filesize//1024)+'Кб.&lt;br/&gt;')
        if docdate!='':
           self.add_response_body('&lt;b&gt;Дата правки:&lt;/b&gt; '+docdate+'&lt;br/&gt;')
        if annotation!='':
           self.add_response_body('&lt;p class=book&gt;'+websym(annotation)+'&lt;/p&gt;')
        self.add_response_body('</content>')

    def entry_finish(self):
        self.add_response_body('</entry>')

    def page_control(self, page, link_id):
        if page>0:
           prev_href=self.modulePath+"?id="+link_id+"&amp;page="+str(page-1)
           self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="'+prev_href+'" />')
        if self.opdsdb.next_page:
           next_href=self.modulePath+"?id="+link_id+"&amp;page="+str(page+1)
           self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="'+next_href+'" />')

    def alphabet_menu(self,iid_value):
        self.entry_start()
        self.entry_head('А..Я (РУС)', None, 'alpha:1')
        id=iid_value+'&amp;alpha=1'+self.nl
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+id+'"/>')
        self.entry_finish()
        self.entry_start()
        self.entry_head('0..9 (Цифры)', None, 'alpha:2')
        id=iid_value+'&amp;alpha=2'+self.nl
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+id+'"/>')
        self.entry_finish()
        self.entry_start()
        self.entry_head('A..Z (ENG)', None, 'alpha:3')
        id=iid_value+'&amp;alpha=3'+self.nl
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+id+'"/>')
        self.entry_finish()
        self.entry_start()
        self.entry_head('Другие Символы', None, 'alpha:4')
        id=iid_value+'&amp;alpha=4'+self.nl
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+id+'"/>')
        self.entry_finish()
        self.entry_start()
        self.entry_head('Показать всё', None, 'alpha:5')
        id=iid_value+self.nl
        self.add_response_body('<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="'+self.modulePath+'?id='+id+'"/>')
        self.entry_finish()

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

