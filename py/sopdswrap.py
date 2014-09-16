import sopdscfg
import datetime

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

class opdsTemplate():
    def __init__(self, modulepath, charset='utf-8'):
       self.charset=charset
       self.modulepath=modulepath
       self.response_header=('Content-Type','text/xml; charset='+self.charset)
       self.document_header=('<?xml version="1.0" encoding="%(charset)s"?>'
                               '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">'
                               '<id>%%(id)s</id>'
                               '<title>%%(title)s</title>'
                               '<subtitle>%%(subtitle)s</subtitle>'
                               '<updated>%%(updated)s</updated>'
                               '<icon>%%(site_icon)s</icon>'
                               '<author><name>%%(site_author)s</name><uri>%%(site_url)s</uri><email>%%(site_email)s</email></author>'
                               '<link type="application/atom+xml" rel="start" href="%(modulepath)s?id=00"/>'
                               )%{'charset':self.charset,'modulepath':self.modulepath}
       self.document_footer='</feed>'
       self.document_mainmenu_std=('<link href="%(modulepath)s?id=09" rel="search" type="application/opensearchdescription+xml" />'
                               '<link href="%(modulepath)s?searchTerm={searchTerms}" rel="search" type="application/atom+xml" />'
                               '<entry>'
                               '<title>По каталогам</title>'
                               '<content type="text">Каталогов: %%(cat_num)s, книг: %%(book_num)s.</content>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=01"/>'
                               '<id>id:01</id></entry>'
                               '<entry>'
                               '<title>По авторам</title>'
                               '<content type="text">Авторов: %%(author_num)s.</content>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s02"/>'
                               '<id>id:02</id></entry>'
                               '<entry>'
                               '<title>По наименованию</title>'
                               '<content type="text">Книг: %%(book_num)s.</content>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s03"/>'
                               '<id>id:03</id></entry>'
                               '<entry>'
                               '<title>По Жанрам</title>'
                               '<content type="text">Жанров: %%(genre_num)s.</content>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=04"/>'
                               '<id>id:04</id></entry>'
                               '<entry>'
                               '<title>По Сериям</title>'
                               '<content type="text">Серий: %%(series_num)s.</content>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s06"/>'
                               '<id>id:06</id></entry>'
                               )%{'modulepath':self.modulepath}
       self.document_mainmenu_new=('<entry>'
                               '<title>Новинки за %%(new_period)s суток</title>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=05"/>'
                               '<id>id:05</id></entry>'
                               )%{'modulepath':self.modulepath}
       self.document_mainmenu_shelf=('<entry>'
                               '<title>Книжная полка для %%(user)s</title>'
                               '<content type="text">Книг: %%(shelf_book_num)s.</content>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=08"/>'
                               '<id>id:08</id></entry>'
                               )%{'modulepath':self.modulepath}
       self.document_newmenu=('<entry>'
                               '<title>Все новинки за %%(new_period)s суток</title>'
                               '<content type="text">Новых книг: %%(newbook_num)s.</content>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s03&amp;news=1"/>'
                               '<id>id:03:news</id></entry>'
                               '<entry>'
                               '<title>Новинки по авторам</title>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s02&amp;news=1"/>'
                               '<id>id:02:news</id></entry>'
                               '<entry>'
                               '<title>Новинки по Жанрам</title>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=04&amp;news=1"/>'
                               '<id>id:04:news</id></entry>'
                               '<entry>'
                               '<title>Новинки по Сериям</title>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(alphabet_id)s06&amp;news=1"/>'
                               '<id>id:06:news</id></entry>'
                               )%{'modulepath':self.modulepath}
       self.document_authors_submenu=('<entry>'
                               '<title>Книги по сериям</title>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=31%%(author_id)s"/>'
                               '<id>id:31:authors</id></entry>'
                               '<entry>'
                               '<title>Книги вне серий</title>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=34%%(author_id)s"/>'
                               '<id>id:32:authors</id></entry>'
                               '<entry>'
                               '<title>Книги по алфавиту</title>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=33%%(author_id)s"/>'
                               '<id>id:33:authors</id></entry>'
                               )%{'modulepath':self.modulepath}
       self.document_entry_start='<entry>'
       self.document_entry_finish='</entry>'
       self.document_entry_head=('<title>%(e_title)s</title>'
                               '<updated>%(e_date)s</updated>'
                               '<id>id:%(e_id)s</id>')
       self.document_entry_link_subsection=('<link type="application/atom+xml" rel="alternate" href="%(modulepath)s?id=%%(link_id)s%%(nl)s"/>'
                               '<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="subsection" href="%(modulepath)s?id=%%(link_id)s%%(nl)s"/>'
                               )%{'modulepath':self.modulepath}
       self.document_entry_link_book_alternate=('<link type="application/%%(format)s" rel="alternate" href="%(modulepath)s?id=91%%(link_id)s"/>'
                               )%{'modulepath':self.modulepath}
       self.document_entry_link_book=('<link type="application/%%(format)s" href="%(modulepath)s?id=%%(id)s%%(link_id)s" rel="http://opds-spec.org/acquisition" />'
                               )%{'modulepath':self.modulepath}
       self.document_entry_authors=('<author><name>%%(last_name)s %%(first_name)s</name></author>'
                               '<link href="%(modulepath)s?id=22%%(author_id)s" rel="related" type="application/atom+xml;profile=opds-catalog" title="Все книги %%(last_name)s %%(first_name)s" />'
                               )%{'modulepath':self.modulepath}
       self.document_entry_doubles=('<link href="%(modulepath)s?id=23%%(book_id)s" rel="related" type="application/atom+xml;profile=opds-catalog" title="Дубликаты книги" />'
                               )%{'modulepath':self.modulepath}
       self.document_entry_genres='<category term="%(genre)s" label="%(genre)s" />'
       self.document_entry_series='' 
       self.document_entry_covers=('<link href="%(modulepath)s?id=99%%(book_id)s" rel="http://opds-spec.org/image" type="image/jpeg" />'
                               '<link href="%(modulepath)s?id=99%%(book_id)s" rel="x-stanza-cover-image" type="image/jpeg" />'
                               '<link href="%(modulepath)s?id=99%%(book_id)s" rel="http://opds-spec.org/thumbnail"  type="image/jpeg" />'
                               '<link href="%(modulepath)s?id=99%%(book_id)s" rel="x-stanza-cover-image-thumbnail"  type="image/jpeg" />'
                               )%{'modulepath':self.modulepath}
       self.document_entry_content='<content type="text">%(e_content)s</content>'
       self.document_entry_content2_start='<content type="text/html">'
       self.document_entry_content2_title='&lt;b&gt;Название книги:&lt;/b&gt; %(title)s&lt;br/&gt;'
       self.document_entry_content2_authors='&lt;b&gt;Авторы:&lt;/b&gt; %(authors)s&lt;br/&gt;'
       self.document_entry_content2_genres='&lt;b&gt;Жанры:&lt;/b&gt; %(genres)s&lt;br/&gt;'
       self.document_entry_content2_series='&lt;b&gt;Серии:&lt;/b&gt; %(series)s&lt;br/&gt;'
       self.document_entry_content2_filename='&lt;b&gt;Файл:&lt;/b&gt; %(filename)s&lt;br/&gt;'
       self.document_entry_content2_filesize='&lt;b&gt;Размер файла:&lt;/b&gt; %(filesize)sКб.&lt;br/&gt;'
       self.document_entry_content2_docdate='&lt;b&gt;Дата правки:&lt;/b&gt; %(docdate)s&lt;br/&gt;'
       self.document_entry_content2_annotation='&lt;p class=book&gt; %(annotation)s&lt;/p&gt;'
       self.document_entry_content2_finish='</content>'

       self.document_alphabet_menu=('<entry><title>А..Я (РУС)</title><id>alpha:1</id><link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(iid)s&amp;alpha=1%%(nl)s"/></entry>'
                                    '<entry><title>0..9 (Цифры)</title><id>alpha:2</id><link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(iid)s&amp;alpha=2%%(nl)s"/></entry>'
                                    '<entry><title>A..Z (ENG)</title><id>alpha:3</id><link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(iid)s&amp;alpha=3%%(nl)s"/></entry>'
                                    '<entry><title>Другие Символы</title><id>alpha:4</id><link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(iid)s&amp;alpha=4%%(nl)s"/></entry>'
                                    '<entry><title>Показать все</title><id>alpha:5</id><link type="application/atom+xml;profile=opds-catalog;kind=navigation" href="%(modulepath)s?id=%%(iid)s&amp;alpha=5%%(nl)s"/></entry>'
                                    )%{'modulepath':self.modulepath}

       self.document_page_control_prev=('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="prev" title="Previous Page" href="%(modulepath)s?id=%%(link_id)s&amp;page=%%(page)s" />'
                               )%{'modulepath':self.modulepath}
       self.document_page_control_next=('<link type="application/atom+xml;profile=opds-catalog;kind=acquisition" rel="next" title="Next Page" href="%(modulepath)s?id=%%(link_id)s&amp;page=%%(page)s" />'
                               )%{'modulepath':self.modulepath}


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
           self.add_response_body(self.template.document_mainmenu_shelf%{'user':USER,'shelf_book_num':DBINFO[5][1]})


    def new_menu(self,NEWINFO):
        if self.cfg.ALPHA: am='30'
        else: am=''
        self.add_response_body(self.template.document_newmenu%{'new_period':self.cfg.NEW_PERIOD,'newbook_num':NEWINFO[0][1],'alphabet_id':am})

    def authors_submenu(self,author_id):
        self.add_response_body(self.template.document_authors_submenu%{'author_id':author_id})

    def entry_start(self):
        self.add_response_body(self.template.document_entry_start)

    def entry_head(self,e_title,e_date,e_id):
        if e_date==None:
           e_date=datetime.datetime(2001,9,9,0,0,0)
        self.add_response_body(self.template.document_entry_head%{'e_title':e_title,'e_date':e_date.strftime("%Y-%m-%dT%H:%M:%S"),'e_id':e_id})

    def entry_link_subsection(self,link_id,nl):
        self.add_response_body(self.template.document_entry_link_subsection%{'link_id':link_id,'nl':nl})

    def entry_link_book(self,link_id,format):
        self.add_response_body(self.template.document_entry_link_book_alternate%{'format':format,'link_id':link_id})
        if format.lower()=='fb2' and self.cfg.FB2TOEPUB:
           self.add_response_body(self.template.document_entry_link_book%{'id':93,'format':'epub','link_id':link_id})
        if format.lower()=='fb2' and self.cfg.FB2TOMOBI:
           self.add_response_body(self.template.document_entry_link_book%{'id':94,'format':'mobi','link_id':link_id})
        self.add_response_body(self.template.document_entry_link_book%{'id':91,'format':format,'link_id':link_id})
        self.add_response_body(self.template.document_entry_link_book%{'id':92,'format':format+'.zip','link_id':link_id})

    def entry_authors(self,tupleAUTHORS):
        authors=""
        for (author_id,first_name,last_name) in tupleAUTHORS:
            self.add_response_body(self.template.document_entry_authors%{'author_id':author_id,'last_name':websym(last_name,True),'first_name':websym(first_name,True)})
            if len(authors)>0:
               authors+=', '
            authors+=last_name+' '+first_name
        return authors

    def entry_doubles(self,book_id,dcount):
        if dcount>0:
           self.add_response_body(self.template.document_entry_doubles%{'book_id':book_id})

    def entry_genres(self,tupleGENRES):
        genres=""
        for (section,genre) in tupleGENRES:
            self.add_response_body(self.template.document_entry_genres%{'genre':genre})
            if len(genres)>0:
                  genres+=', '
            genres+=genre
        return genres


    def entry_series(self,tupleSERIES):
        series=""
        for (ser,ser_no) in tupleSERIES:
            self.add_response_body(self.template.document_entry_series%{'ser':ser,'ser_no':ser_no})
            if len(series)>0:
                  series+=', '
            series+=ser
            if ser_no > 0:
                  series += ' #' + str(ser_no)
        return series

    def entry_covers(self,book_id):
        self.add_response_body(self.template.document_entry_covers%{'book_id':book_id})

    def entry_content(self,e_content):
        self.add_response_body(self.template.document_entry_content%{'e_content':websym(e_content)})

    def entry_content2(self,annotation='',title='',authors='',genres='',filename='',filesize=0,docdate='',series=''):
        self.add_response_body(self.template.document_entry_content2_start)
        if title!='':
           self.add_response_body(self.template.document_entry_content2_title%{'title':websym(title)})
        if authors!='':
           self.add_response_body(self.template.document_entry_content2_authors%{'authors':websym(authors)})
        if genres!='':
           self.add_response_body(self.template.document_entry_content2_genres%{'genres':websym(genres)})
        if series!='':
           self.add_response_body(self.template.document_entry_content2_series%{'series':websym(series)})
        if filename!='':
           self.add_response_body(self.template.document_entry_content2_filename%{'filename':websym(filename)})
        if filesize>0:
           self.add_response_body(self.template.document_entry_content2_filesize%{'filesize':str(filesize//1024)})
        if docdate!='':
           self.add_response_body(self.template.document_entry_content2_docdate%{'docdate':docdate})
        if annotation!='':
           self.add_response_body(self.template.document_entry_content2_annotation%{'annotation':websym(annotation)})
        self.add_response_body(self.template.document_entry_content2_finish)    


    def entry_finish(self):
        self.add_response_body(self.template.document_entry_finish)

    def page_control_prev(self, page, link_id):
           self.add_response_body(self.template.document_page_control_prev%{'link_id':link_id,'page':page-1})

    def page_control_next(self, page, link_id):
           self.add_response_body(self.template.document_page_control_next%{'link_id':link_id,'page':page+1})

    def alphabet_menu(self,iid_value,nl):
        self.add_response_body(self.template.document_alphabet_menu%{'iid':iid_value,'nl':nl})
