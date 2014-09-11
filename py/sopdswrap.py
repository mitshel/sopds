import sopdscfg

class opdsTemplate():
    def __init__(self, modulepath, charset='utf-8'):
       self.charset=charset
       self.modulepath=modulepath
       self.response_header=('Content-Type','text/xml; charset='+self.charset)
       self.document_header='''<?xml version="1.0" encoding="%(charset)s"?>
                               <feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">
                               <id>%%(id)s</id>
                               <title>%%(title)s</title>
                               <subtitle>%%(subtitle)s</subtitle>
                               <updated>%%(updated)s</updated>
                               <icon>%%(site_icon)s</icon>
                               <author><name>%%(site_author)s</name><uri>%%(site_url)s</uri><email>%%(site_email)s</email></author>
                               <link type="application/atom+xml" rel="start" href="%(modulepath)s?id=00"/>'''%{'charset':self.charset,'modulepath':self.modulepath}
       self.document_footer='''</feed>'''
       self.document_mainmenu_std='''<link href="%(modulepath)s?id=09" rel="search" type="application/opensearchdescription+xml" />
                               <link href="%(modulepath)s?searchTerm={searchTerms}" rel="search" type="application/atom+xml" />
                               <entry>
                               <title>По каталогам</title>
                               <content type="text">Каталогов: %%(cat_num)s, книг: %%(book_num)s.</content>
                               <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=01"/>')
                               <id>id:01</id></entry>
                               <entry>
                               <title>По авторам</title>
                               <content type="text">Авторов: %%(author_num)s.</content>
                               <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s02"/>
                               <id>id:02</id></entry>
                               <entry>
                               <title>По наименованию</title>
                               <content type="text">Книг: %%(book_num)s.</content>
                               <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s03"/>
                               <id>id:03</id></entry>
                               <entry>
                               <title>По Жанрам</title>
                               <content type="text">Жанров: %%(genre_num)s.</content>
                               <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=04"/>
                               <id>id:04</id></entry>
                               <entry>
                               <title>По Сериям</title>
                               <content type="text">Серий: %%(series_num)s.</content>
                               <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s06"/>
                               <id>id:06</id></entry>'''%{'modulepath':self.modulepath}
       self.document_mainmenu_new='''<entry>
                               <title>Новинки за %%(new_period)s суток</title>
                               <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=05"/>
                               <id>id:05</id></entry>'''%{'modulepath':self.modulepath}
       self.document_mainmenu_shelf='''<entry>
                               <title>Книжная полка для %%(user)s</title>
                               <content type="text">Книг: %%(book_num)s.</content>
                               <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=08"/>
                               <id>id:08</id></entry>'''%{'modulepath':self.modulepath}
       self.document_newmenu='''<entry>
        <title>Все новинки за %%(new_period)s суток</title>
        <content type="text">Новых книг: %%(newbook_num)s.</content>
        <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s03&amp;news=1"/>
        <id>id:03:news</id></entry>
        <entry>
        <title>Новинки по авторам</title>
        <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s02&amp;news=1"/>
        <id>id:02:news</id></entry>
        <entry>
        <title>Новинки по Жанрам</title>
        <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=04&amp;news=1"/>
        <id>id:04:news</id></entry>
        <entry>
        <title>Новинки по Сериям</title>
        <link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s06&amp;news=1"/>
        <id>id:06:news</id></entry>'''%{'modulepath':self.modulepath}



#######################################################################
#
# Базовый класс формирующий вывод
#
class baseWrapper():
    def __init__(self, cfg, template):
        self.cfg=cfg
        self.template=template
        self.response_status='200 Ok'
        self.response_headers=[]
        self.response_body=[]

    def resetParams(self):
        self.response_status='200 Ok'
        self.response_headers=[]
        self.response_body=[]

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

    def header(self, h_id=None, h_title=None, h_subtitle=None, h_time='2014-01-01 00:00:00'):
        self.add_response_header([self.template.response_header])
        self.add_response_body(self.template.document_header%{'id':h_id,'title':h_title,'subtitle':h_subtitle,'updated':h_time,'site_icon':self.cfg.SITE_ICON,'site_author':self.cfg.SITE_AUTOR,'site_url':self.cfg.SITE_URL,'site_email':self.cfg.SITE_EMAIL})

    def footer(self):
        self.add_response_body(self.template.document_footer)

    def main_menu(self,USER,DBINFO):
        if self.cfg.ALPHA: am='30'
        else: am=''
        self.add_response_body(self.template.document_mainmenu_std%{'cat_num':DBINFO[2][1],'book_num':DBINFO[0][1],'author_num':DBINFO[1][1],'genre_num':DBINFO[3][1],'series_num':DBINFO[4][1],'alphabet_id':am})
        if self.cfg.NEW_PERIOD!=0:
           self.add_response_body(self.template.document_mainmenu_new%{'new_period':self.cfg.NEW_PERIOD})
        if self.cfg.BOOK_SHELF and USER!=None:
           self.add_response_body(self.template.document_mainmenu_shelf%{'user':USER,'book_num':DBINFO[0][1]})


    def new_menu(self,NEWINFO):
        if self.cfg.ALPHA: am='30'
        else: am=''
        self.add_response_body(self.template.document_newmenu%{'new_period':self.cfg.NEW_PERIOD,'newbook_num':NEWINFO[0][1],'alphabet_id':am})

    def authors_submenu(self,author_id):
        pass

    def entry_start(self):
        pass

    def entry_head(self,e_title,e_date,e_id):
        pass

    def entry_link_subsection(self,link_id,modulePath):
        pass

    def entry_link_book(self,link_id,format,modulePath):
        pass

    def entry_authors(self,book_id,tupleAITHORS,link_show=False):
        authors=''
        return authors

    def entry_doubles(self,book_id,DCOUNT):
        pass

    def entry_genres(self,book_id,tupleGENRES):
        genres=""
        return genres

    def entry_series(self,book_id,tupleSERIES):
        series=""
        return series

    def entry_covers(self,cover,cover_type,book_id,modulePath,COVER_SHOW):
        pass

    def entry_content(self,e_content):
        pass

    def entry_content2(self,annotation='',title='',authors='',genres='',filename='',filesize=0,docdate='',series=''):
        pass

    def entry_finish(self):
        pass

    def page_control(self, page, link_id, modulePath):
        pass

    def alphabet_menu(self,iid_value,nl):
        pass

