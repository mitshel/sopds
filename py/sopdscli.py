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
import sopdstempl
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

#######################################################################
#
# Основной класс OPDS-клиента
#
class opdsClient():
    def __init__(self,cfg,mode=modeCGI):
        self.cfg=cfg
        if mode==modeWSGI:
           self.moduleFile=self.cfg.WSGI_PATH
        elif mode==modeINT:
           self.moduleFile=''
        else:
           self.moduleFile=self.cfg.CGI_PATH
        self.modulePath=self.moduleFile
        self.opdsdb=sopdsdb.opdsDatabase(self.cfg.DB_NAME,self.cfg.DB_USER,self.cfg.DB_PASS,self.cfg.DB_HOST,self.cfg.ROOT_LIB)
        self.site_data={'site_title':self.cfg.SITE_TITLE, 'site_subtitle':'Simple OPDS Catalog by www.sopds.ru. Version '+sopdscfg.VERSION,'modulepath':self.modulePath,'site_icon':self.cfg.SITE_ICON,'site_author':self.cfg.SITE_AUTOR,'site_url':self.cfg.SITE_URL,'site_email':self.cfg.SITE_EMAIL, 'charset':'utf-8'}

        self.template1=sopdstempl.opdsTemplate()
        self.opdsWrapper=sopdswrap.baseWrapper(self.cfg, self.template1,self.site_data)

        self.template2=sopdstempl.webTemplate()
        self.webWrapper=sopdswrap.baseWrapper(self.cfg, self.template2,self.site_data)

        self.Wrapper=self.opdsWrapper


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
        self.method=0
        self.opdsWrapper.resetParams()
        self.webWrapper.resetParams()
        self.Wrapper=self.opdsWrapper

    def parseParams(self,environ):
        self.environ=environ
        qs   = None
        
        if 'QUERY_STRING' in environ:
           qs = parse.parse_qs(environ['QUERY_STRING'])
        if 'REQUEST_URI' in environ:
           URI=environ['REQUEST_URI']
        else:
           URI=environ['PATH_INFO']

        if self.cfg.WEB_PREFIX in URI:
           self.Wrapper=self.webWrapper        
           self.modulePath=os.path.join(self.cfg.WEB_PREFIX,self.moduleFile)
        if self.cfg.OPDS_PREFIX in URI:
           self.Wrapper=self.opdsWrapper
           self.modulePath=os.path.join(self.cfg.OPDS_PREFIX,self.moduleFile)
        self.modulePath=os.path.normpath(self.modulePath)

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
        self.Wrapper.add_response_body(string,encoding)

    def add_response_binary(self, data):
        self.Wrapper.add_response_binary(data)

    def add_response_header(self,list):
        self.Wrapper.add_response_header(list)

    def set_response_status(self,status):
        self.Wrapper.set_response_status(status)

    def write_response_headers(self, encoding='utf8'):
        self.Wrapper.write_response_headers(encoding)

    def write_response(self):
        self.Wrapper.write_response()

    def get_response_status(self):
        return self.Wrapper.response_status

    def get_response_headers(self):
        return self.Wrapper.response_headers

    def get_response_body(self):
        return self.Wrapper.response_body

    def header(self, page_data):
        self.Wrapper.document_header(page_data)
        self.Wrapper.page_top(page_data)
        self.Wrapper.page_title(page_data)

    def footer(self,page_data={}):
#        Debug output commented
#        for key in self.environ.keys():
#            self.add_response_body("{0}:{1}".format(key,self.environ[key], end=" "))
        self.Wrapper.page_bottom(page_data)
        self.Wrapper.document_footer(page_data)

    def main_menu(self):
        dbinfo=self.opdsdb.getdbinfo(self.cfg.DUBLICATES_SHOW,self.cfg.BOOK_SHELF,self.user)
        self.Wrapper.main_menu(self.user,dbinfo)

    def new_menu(self):
        newinfo=self.opdsdb.getnewinfo(self.cfg.DUBLICATES_SHOW,self.cfg.NEW_PERIOD)
        self.Wrapper.new_menu(newinfo)

    def authors_submenu(self,author_id):
        self.Wrapper.authors_submenu(author_id)

    def opensearch_links(self,page_data):
        self.Wrapper.opensearch_links(page_data)

    def opensearch_forms(self,page_data):
        self.Wrapper.opensearch_forms(page_data)

    def get_authors(self,book_id):
        return self.Wrapper.get_authors(self.opdsdb.getauthors(book_id))

    def get_genres(self,book_id):
        return self.Wrapper.get_genres(self.opdsdb.getgenres(book_id))

    def get_series(self,book_id):
        return self.Wrapper.get_series(self.opdsdb.getseries(book_id))

    def entry_acquisition(self,acq_data):
        self.Wrapper.entry_acquisition(acq_data)
  
    def entry_navigation(self,nav_data):
        self.Wrapper.entry_navigation(nav_data)

    def page_control(self, page_data):
        data=page_data.copy()
        data['link_id']=self.id_value
        data['page']=self.page_value
        if self.page_value>0:
           data['page_prev']=self.page_value-1
        else:
           data['page_prev']=-1
        if self.opdsdb.next_page:
           data['page_next']=self.page_value+1
        else:
           data['page_next']=-1;
        self.Wrapper.page_control(data)

    def alphabet_menu(self,iid_value):
        self.Wrapper.alphabet_menu(iid_value,self.nl) 

    def response_search(self):
        self.Wrapper.opensearch()

    def response_main(self):
        page_data={'page_id':'id:main', 'page_title':'SOPDS|Главная', 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        self.main_menu()
        self.footer(page_data)

    def response_catalogs(self):
        """ Выбрана сортировка 'По каталогам' """
        page_data={'page_id':'id:catalogs', 'page_title':'Сортировка по каталогам хранения', 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (item_type,item_id,item_name,item_path,reg_date,item_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getitemsincat(self.slice_value,self.cfg.MAXITEMS,self.page_value):
            if item_type==1:
               id='01'+str(item_id)
               nav_data={'link_id':id,'item_id':item_id,'e_date':reg_date,'e_title':websym(item_title),'e_id':'item:%s'%(item_id),'e_nav_info':'',
                         'nl':self.nl}
               self.entry_navigation(nav_data)
            if item_type==2:
               id='90'+str(item_id)
               (authors, authors_link) = self.get_authors(item_id)
               (genres,  genres_link)  = self.get_genres(item_id)
               (series,  series_link)  = self.get_series(item_id)
               acq_data={'link_id':id,'item_id':item_id,'filename':item_name,'e_date':reg_date,'e_title':websym(item_title),'e_id':'item:%s'%(item_id),
                         'annotation':websym(annotation), 'docdate':docdate, 'format':format,'cover':cover,'cover_type':cover_type,'filesize':fsize//1024,
                         'authors':authors,'genres':genres,'series':series,'authors_link':authors_link,'genres_link':genres_link, 'series_link':series_link,
                         'nl':self.nl, 'dcount':0}
               self.entry_acquisition(acq_data)
        self.page_control(page_data)
        self.footer()

    def response_alpha(self):
        """ Вывод дополнительного меню алфавита для сортировок по Наименованиям, по Авторам и по Жанрам """
        page_data={'page_id':'id:alphabet', 'page_title':'SOPDS|Выбор языка', 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        self.alphabet_menu(self.id_value[2:])
        self.footer(page_data)

    def response_authors(self):
        """ Cортировка 'По авторам' - выбор по нескольким первым буквам автора """
        i=self.slice_value
        letter=""
        while i>0:
           letter=chr(i%10000)+letter
           i=i//10000
        page_data={'page_id':'id:preauthors:%s'%letter,'page_title':'Выбор авторов "%s"'%letter, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (letters,cnt) in self.opdsdb.getauthor_2letters(letter,self.alpha,self.np):
            id=""
            for i in range(len(letters)):
                id+='%04d'%(ord(letters[i]))

            if self.cfg.SPLITTITLES==0 or cnt<=self.cfg.SPLITTITLES or len(letters)>10:
               id='12'+id
            else:
               id='02'+id

            nav_data={'link_id':id,'e_date':None,'e_title':letters,'e_id':id,'e_nav_info':('Всего: '+str(cnt)+' автора(ов).'),
                      'nl':self.nl}
            self.entry_navigation(nav_data)
        self.footer(page_data)

    def response_series(self):
        """ Cортировка 'По сериям' - выбор по нескольким первым буквам серии """
        i=self.slice_value
        letter=""
        while i>0:
           letter=chr(i%10000)+letter
           i=i//10000
        page_data={'page_id':'id:preseries:%s'%letter,'page_title':'Выбор серий "%s"'%letter, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (letters,cnt) in self.opdsdb.getseries_2letters(letter,self.alpha,self.np):
            id=""
            for i in range(len(letters)):
                id+='%04d'%(ord(letters[i]))

            if self.cfg.SPLITTITLES==0 or cnt<=self.cfg.SPLITTITLES or len(letters)>10:
               id='16'+id
            else:
               id='06'+id

            nav_data={'link_id':id,'e_date':None,'e_title':letters,'e_id':id,'e_nav_info':('Всего: '+str(cnt)+' серий.'),
                      'nl':self.nl}
            self.entry_navigation(nav_data)
        self.footer(page_data)

    def response_titles(self):
        """ Cортировка 'По наименованию' - выбор по нескольким первым буквам наименования """
        i=self.slice_value
        letter=""
        while i>0:
           letter=chr(i%10000)+letter
           i=i//10000
        page_data={'page_id':'id:pretitle:%s'%letter,'page_title':'Выбор наименований "%s"'%letter, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (letters,cnt) in self.opdsdb.gettitle_2letters(letter,self.cfg.DUBLICATES_SHOW,self.alpha,self.np):
            id=""
            for i in range(len(letters)):
                id+='%04d'%(ord(letters[i]))

            if self.cfg.SPLITTITLES==0 or cnt<=self.cfg.SPLITTITLES or len(letters)>10:
               id='13'+id
            else:
               id='03'+id

            nav_data={'link_id':id,'e_date':None,'e_title':letters,'e_id':id,'e_nav_info':('Всего: '+str(cnt)+' наименований.'),
                      'nl':self.nl}
            self.entry_navigation(nav_data)
        self.footer(page_data)

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
        page_data={'page_id':'id:title:%s'%letter,'page_title':'Книги по наименованию "%s"'%letter, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksfortitle(letter,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='90'+str(book_id)
            (authors, authors_link) = self.get_authors(book_id)
            (genres,  genres_link)  = self.get_genres(book_id)
            (series,  series_link)  = self.get_series(book_id)
            acq_data={'link_id':id,'item_id':book_id,'filename':book_name,'e_date':reg_date,'e_title':websym(book_title),'e_id':'item:%s'%(book_id),
                      'annotation':websym(annotation), 'docdate':docdate, 'format':format,'cover':cover,'cover_type':cover_type,'filesize':fsize//1024,
                      'authors':authors,'genres':genres,'series':series,'authors_link':authors_link,'genres_link':genres_link, 'series_link':series_link,
                      'nl':self.nl, 'dcount':self.opdsdb.getdoublecount(book_id)}
            self.entry_acquisition(acq_data)
        self.page_control(page_data)
        self.footer(page_data)

    def response_doubles(self):
        """ Вывод дубликатов для выбранной книги """
        page_data={'page_id':'id:doubles:%s'%self.slice_value,'page_title':'Дубликаты для книги id=%s'%self.slice_value, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getdoubles(self.slice_value,self.cfg.MAXITEMS,self.page_value):
            id='90'+str(book_id)
            (authors, authors_link) = self.get_authors(book_id)
            (genres,  genres_link)  = self.get_genres(book_id)
            (series,  series_link)  = self.get_series(book_id)
            acq_data={'link_id':id,'item_id':book_id,'filename':book_name,'e_date':reg_date,'e_title':websym(book_title),'e_id':'item:%s'%(book_id),
                      'annotation':websym(annotation), 'docdate':docdate, 'format':format,'cover':cover,'cover_type':cover_type,'filesize':fsize//1024,
                      'authors':authors,'genres':genres,'series':series,'authors_link':authors_link,'genres_link':genres_link, 'series_link':series_link,
                      'nl':self.nl,'dcount':self.opdsdb.getdoublecount(book_id)}
            self.entry_acquisition(acq_data)
        self.page_control(page_data)
        self.footer(page_data)


    def response_genres_sections(self):
        """ Cортировка 'По жанрам' - показ секций """
        page_data={'page_id':'id:genre:sections','page_title':'Список жанров', 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (genre_id,genre_section,cnt) in self.opdsdb.getgenres_sections(self.cfg.DUBLICATES_SHOW,self.np):
            id='14'+str(genre_id)
            nav_data={'link_id':id,'e_date':None,'e_title':genre_section,'e_id':'genre:%s'%(genre_id),'e_nav_info':('Всего: '+str(cnt)+' книг.'),
                      'nl':self.nl}
            self.entry_navigation(nav_data)
        self.footer(page_data)

    def response_genres_subsections(self):
        """ Cортировка 'По жанрам' - показ подсекций """
        page_data={'page_id':'id:genre:subsections:%s'%self.slice_value,'page_title':'Список жанров (уровень 2)', 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (genre_id,genre_subsection,cnt) in self.opdsdb.getgenres_subsections(self.slice_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='24'+str(genre_id)
            if self.cfg.ALPHA: id='30'+id
            nav_data={'link_id':id,'e_date':None,'e_title':genre_subsection,'e_id':'genre:%s'%(genre_id),'e_nav_info':('Всего: '+str(cnt)+' книг.'),
                      'nl':self.nl}
            self.entry_navigation(nav_data)
        self.footer(page_data)

    def response_genres_books(self):
        """ Выдача списка книг по жанру """
        page_data={'page_id':'id:genres:%s'%self.slice_value,'page_title':'Список книг по выбранному жанру', 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforgenre(self.slice_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.alpha,self.np):
            id='90'+str(book_id)
            (authors, authors_link) = self.get_authors(book_id)
            (genres,  genres_link)  = self.get_genres(book_id)
            (series,  series_link)  = self.get_series(book_id)
            acq_data={'link_id':id,'item_id':book_id,'filename':book_name,'e_date':reg_date,'e_title':websym(book_title),'e_id':'item:%s'%(book_id),
                      'annotation':websym(annotation), 'docdate':docdate, 'format':format,'cover':cover,'cover_type':cover_type,'filesize':fsize//1024,
                      'authors':authors,'genres':genres,'series':series,'authors_link':authors_link,'genres_link':genres_link, 'series_link':series_link,
                      'nl':self.nl, 'dcount':self.opdsdb.getdoublecount(book_id)}
            self.entry_acquisition(acq_data)
        self.page_control(page_data)
        self.footer(page_data)

    def response_last(self):
        """ Cортировка 'Последние поступления' """  
        page_data={'page_id':'id:news','page_title':'Последние поступления за %s дней'%self.cfg.NEW_PERIOD, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        self.new_menu()
        self.footer(page_data)

    def response_search_type(self):
        page_data={'page_id':'id:search:%s'%self.searchTerm,'page_title':'Поиск %s'%self.searchTerm, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ"),'searchterm':parse.quote(self.searchTerm)}
        self.header(page_data)
        self.opensearch_forms(page_data)
        self.footer(page_data)

    def response_bookshelf(self):
        """ Выдача списка книг на книжной полке """
        page_data={'page_id':'id:bookshelf:%s'%self.user,'page_title':'Книги пользователя %s'%self.user, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforuser(self.user,self.cfg.MAXITEMS,self.page_value):
            id='90'+str(book_id)
            (authors, authors_link) = self.get_authors(book_id)
            (genres,  genres_link)  = self.get_genres(book_id)
            (series,  series_link)  = self.get_series(book_id)
            acq_data={'link_id':id,'item_id':book_id,'filename':book_name,'e_date':reg_date,'e_title':websym(book_title),'e_id':'item:%s'%(book_id),
                      'annotation':websym(annotation), 'docdate':docdate, 'format':format,'cover':cover,'cover_type':cover_type,'filesize':fsize//1024,
                      'authors':authors,'genres':genres,'series':series,'authors_link':authors_link,'genres_link':genres_link, 'series_link':series_link,
                      'nl':self.nl, 'dcount':self.opdsdb.getdoublecount(book_id)}
            self.entry_acquisition(acq_data)
        self.page_control(page_data)
        self.footer(page_data)

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

        page_data={'page_id':'id:authors:%s'%letter,'page_title':'Авторы по имени "%s"'%letter, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (author_id,first_name, last_name,cnt) in self.opdsdb.getauthorsbyl(letter,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='22'+str(author_id)
            nav_data={'link_id':id,'e_date':None,'e_title':(last_name+' '+first_name),'e_id':'author:%s'%(author_id),'e_nav_info':('Всего: '+str(cnt)+' книг.'),
                      'nl':self.nl}
            self.entry_navigation(nav_data)
        self.page_control(page_data)
        self.footer(page_data)

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

        page_data={'page_id':'id:series:%s'%letter,'page_title':'Список серий книг "%s"'%letter, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (ser_id,ser,cnt) in self.opdsdb.getseriesbyl(letter,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='26'+str(ser_id)
            nav_data={'link_id':id,'e_date':None,'e_title':ser,'e_id':'series:%s'%(ser_id),'e_nav_info':('Всего: '+str(cnt)+' книг.'),
                      'nl':self.nl}
            self.entry_navigation(nav_data)
        self.page_control(page_data)
        self.footer(page_data)

    def response_authors_submenu(self):
        """ Выдача подменю вывода книг по автору - в случае флага новинок будет сразу переход к выдаче книг автора """
        (first_name,last_name)=self.opdsdb.getauthor_name(self.slice_value)
        page_data={'page_id':'id:autor:%s %s'%(last_name,first_name),'page_title':'Книги автора %s %s'%(last_name,first_name), 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        self.authors_submenu(self.slice_value)
        self.footer(page_data)

    def response_authors_series(self):
        """ Выдача серий по автору """
        (first_name,last_name)=self.opdsdb.getauthor_name(self.slice_value)
        page_data={'page_id':'id:autorseries:%s %s'%(last_name,first_name),'page_title':'Серии книг автора %s %s'%(last_name,first_name), 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (ser_id,ser,cnt) in self.opdsdb.getseriesforauthor(self.slice_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW):
            id='34'+str(self.slice_value)+'&amp;ser='+str(ser_id)
            nav_data={'link_id':id,'e_date':None,'e_title':ser,'e_id':'series:%s'%(ser_id),'e_nav_info':('Всего: '+str(cnt)+' книг.'),
                      'nl':self.nl}
            self.entry_navigation(nav_data)
        self.page_control(page_data)
        self.footer(page_data)

    def response_authors_alpha(self):
        """ Выдача списка книг по автору по алфавиту """
        (first_name,last_name)=self.opdsdb.getauthor_name(self.slice_value)
        page_data={'page_id':'id:autorbooks:%s %s'%(last_name,first_name),'page_title':'Книги автора %s %s'%(last_name,first_name), 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforautor(self.slice_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='90'+str(book_id)
            (authors, authors_link) = self.get_authors(book_id)
            (genres,  genres_link)  = self.get_genres(book_id)
            (series,  series_link)  = self.get_series(book_id)
            acq_data={'link_id':id,'item_id':book_id,'filename':book_name,'e_date':reg_date,'e_title':websym(book_title),'e_id':'item:%s'%(book_id),
                      'annotation':websym(annotation), 'docdate':docdate, 'format':format,'cover':cover,'cover_type':cover_type,'filesize':fsize//1024,
                      'authors':authors,'genres':genres,'series':series,'authors_link':authors_link,'genres_link':genres_link, 'series_link':series_link,
                      'nl':self.nl, 'dcount':self.opdsdb.getdoublecount(book_id)}
            self.entry_acquisition(acq_data)
        self.page_control(page_data)
        self.footer(page_data)

    def response_authors_series_books(self):
        """ Выдача списка книг по автору по выбранной серии (или вне серий если ser_value==0) """
        (first_name,last_name)=self.opdsdb.getauthor_name(self.slice_value)
        page_data={'page_id':'id:autorbooks:%s %s'%(last_name,first_name),'page_title':'Книги автора %s %s'%(last_name,first_name), 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforautorser(self.slice_value,self.ser_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW):
            id='90'+str(book_id)
            (authors, authors_link) = self.get_authors(book_id)
            (genres,  genres_link)  = self.get_genres(book_id)
            (series,  series_link)  = self.get_series(book_id)
            acq_data={'link_id':id,'item_id':book_id,'filename':book_name,'e_date':reg_date,'e_title':websym(book_title),'e_id':'item:%s'%(book_id),
                      'annotation':websym(annotation), 'docdate':docdate, 'format':format,'cover':cover,'cover_type':cover_type,'filesize':fsize//1024,
                      'authors':authors,'genres':genres,'series':series,'authors_link':authors_link,'genres_link':genres_link, 'series_link':series_link,
                      'nl':self.nl, 'dcount':self.opdsdb.getdoublecount(book_id)}
            self.entry_acquisition(acq_data)
        self.page_control(page_data)
        self.footer(page_data)

    def response_series_books(self):
        """ Выдача списка книг по серии """
        (ser_name,)=self.opdsdb.getser_name(self.slice_value)
        page_data={'page_id':'id:ser:%s'%ser_name,'page_title':'Книги серии %s'%ser_name, 'page_updated':time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.header(page_data)
        for (book_id,book_name,book_path,reg_date,book_title,annotation,docdate,format,fsize,cover,cover_type) in self.opdsdb.getbooksforser(self.slice_value,self.cfg.MAXITEMS,self.page_value,self.cfg.DUBLICATES_SHOW,self.np):
            id='90'+str(book_id)
            (authors, authors_link) = self.get_authors(book_id)
            (genres,  genres_link)  = self.get_genres(book_id)
            (series,  series_link)  = self.get_series(book_id)
            acq_data={'link_id':id,'item_id':book_id,'filename':book_name,'e_date':reg_date,'e_title':websym(book_title),'e_id':'item:%s'%(book_id),
                      'annotation':websym(annotation), 'docdate':docdate, 'format':format,'cover':cover,'cover_type':cover_type,'filesize':fsize//1024,
                      'authors':authors,'genres':genres,'series':series,'authors_link':authors_link,'genres_link':genres_link, 'series_link':series_link,
                      'nl':self.nl, 'dcount':self.opdsdb.getdoublecount(book_id)}
            self.entry_acquisition(acq_data)
        self.page_control(page_data)
        self.footer(page_data)

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



