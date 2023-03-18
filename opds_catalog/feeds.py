from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.feedgenerator import Atom1Feed, Enclosure, rfc3339_date
from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.shortcuts import render
from django.db.models import Count, Min
from django.utils.html import strip_tags

from opds_catalog.models import Book, Catalog, Author, Genre, Series, bookshelf, Counter, lang_menu
from opds_catalog import models
from opds_catalog import settings
from opds_catalog.middleware import BasicAuthMiddleware
from opds_catalog.opds_paginator import Paginator as OPDS_Paginator

from book_tools.format import mime_detector
from book_tools.format.mimetype import Mimetype

from constance import config


class AuthFeed(Feed):
    request = None
    def __call__(self,request,*args,**kwargs):
        self.request = request
        if config.SOPDS_AUTH:
            if request.user.is_authenticated:
                return super().__call__(request,*args,**kwargs)
        
        bau = BasicAuthMiddleware()
        result=bau.process_request(self.request)
        
        if result!=None:
            return result
        
        return super().__call__(request,*args,**kwargs)

class opdsEnclosure(Enclosure):
    def __init__(self, url, mime_type, rel):
        self.rel = rel
        super(opdsEnclosure,self).__init__(url, 0, mime_type)

class opdsFeed(Atom1Feed):
    #content_type = 'text/xml; charset=utf-8'
    content_type = 'application/atom+xml; charset=utf-8'
        
    def root_attributes(self):
        attrs = {}
        #attrs = super(opdsFeed, self).root_attributes()
        attrs['xmlns'] = 'http://www.w3.org/2005/Atom'
        attrs['xmlns:dcterms'] = 'http://purl.org/dc/terms'
        #attrs['xmlns:os'] = "http://a9.com/-/spec/opensearch/1.1/"
        #attrs['xmlns:opds'] = "http://opds-spec.org/2010/catalog"
        return attrs

    def add_root_elements(self, handler):
        handler._short_empty_elements = True
        #super(opdsFeed, self).add_root_elements(handler)
        handler.characters("\n")
        handler.addQuickElement("id", self.feed['id'])
        handler.addQuickElement('icon', settings.ICON)
        handler.characters("\n")
        if self.feed.get('link') is not None:
            handler.addQuickElement('link', None, {"href":self.feed["link"],"rel":"self","type":"application/atom+xml;profile=opds-catalog;kind=navigation"})
            handler.characters("\n")
        if self.feed.get('start_url') is not None:
            handler.addQuickElement('link', None, {"href":self.feed["start_url"],"rel":"start","type":"application/atom+xml;profile=opds-catalog;kind=navigation"})
            handler.characters("\n")
        handler.addQuickElement("title", self.feed['title'])
        handler.characters("\n")
        if self.feed.get('subtitle') is not None:
            handler.addQuickElement("subtitle", self.feed['subtitle'])
            handler.characters("\n")
        handler.addQuickElement("updated", rfc3339_date(self.latest_post_date()))
        handler.characters("\n")
        if self.feed.get('prev_url') is not None:
            handler.addQuickElement('link', None, {"href":self.feed["prev_url"],"rel":"prev","title":"Previous Page","type":"application/atom+xml;profile=opds-catalog"})
            handler.characters("\n")
        if self.feed.get('next_url') is not None:
            handler.addQuickElement('link', None, {"href":self.feed["next_url"],"rel":"next","title":"Next Page","type":"application/atom+xml;profile=opds-catalog"})
            handler.characters("\n")
        if self.feed.get('search_url') is not None:
            handler.addQuickElement('link', None, {"href":self.feed["search_url"],"rel":"search","type":"application/atom+xml;profile=opds-catalog;kind=navigation"})
            handler.characters("\n")
        if self.feed.get('searchTerm_url') is not None:
            handler.addQuickElement('link', None, {"href":self.feed["searchTerm_url"],"rel":"search","type":"application/atom+xml"})
            handler.characters("\n")


    def add_item_elements(self, handler, item):        
        disable_item_links = item.get('disable_item_links')    
        handler.characters("\n")
        handler.addQuickElement("id", item['unique_id'])
        handler.characters("\n")
        handler.addQuickElement("title", item['title'])
        handler.characters("\n")
        if not disable_item_links:
            handler.addQuickElement("link", "", {"href": item['link'], "rel": "alternate"})
            handler.characters("\n")
        # Enclosures.
        if not disable_item_links:
            if item.get('enclosures') is not None:
                for enclosure in item['enclosures']:
                    handler.addQuickElement('link', '', {
                        'rel': enclosure.rel,
                        'href': enclosure.url,
                        'type': enclosure.mime_type,
                    })
                    handler.characters("\n")

        if item.get('updateddate') is not None:
            handler.addQuickElement('updated', rfc3339_date(item['updateddate']))
            handler.characters("\n")

        if self.feed.get("description_mime_type") is not None:
            content_type = self.feed["description_mime_type"]
        else:
            content_type = "text/html"
        if item.get("description") is not None:
            handler.addQuickElement("content", item["description"], {"type": content_type})
            handler.characters("\n")
            
        if item.get("authors") is not None:
            for a in item["authors"]:
                handler.startElement("author", {})
                handler.addQuickElement("name", a['full_name'])
                #handler.addQuickElement("uri", item['author_link'])
                handler.endElement("author")
                handler.addQuickElement("link", "", {"href": reverse("opds_catalog:searchbooks", kwargs={"searchtype":'a', "searchterms":a['id']}), 
                                                     "rel": "related", 
                                                     "type":"application/atom+xml;profile=opds-catalog", 
                                                     "title":_("All books by %(author)s")%{'author':a['full_name']}})
                handler.characters("\n")
                        
        if item.get("genres") is not None:       
            for g in item["genres"]:
                handler.addQuickElement("category", "", {"term": g['subsection'], "label": g['subsection']})    
            handler.characters("\n")        
        
        if item.get("doubles") is not None:    
                handler.addQuickElement("link", "", {"href": reverse("opds_catalog:searchbooks", kwargs={"searchtype":'d', "searchterms":item['doubles']}), 
                                                     "rel": "related", 
                                                     "type":"application/atom+xml;profile=opds-catalog", 
                                                     "title":_("Book doublicates")})
                handler.characters("\n")
            
class MainFeed(AuthFeed):
    feed_type = opdsFeed
    title = settings.TITLE
    subtitle = settings.SUBTITLE

    def link(self):
        return reverse("opds_catalog:main")

    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                #"searchTerm_url":reverse("opds_catalog:searchtypes",kwargs={"searchterms":"{searchTerms}"}),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }

    def items(self):
        mainitems = [
                    {"id":1, "title":_("By catalogs"), "link":"opds_catalog:catalogs",
                     "descr": _("Catalogs: %(catalogs)s, books: %(books)s."),"counters":{"catalogs":Counter.objects.get_counter(models.counter_allcatalogs),"books":Counter.objects.get_counter(models.counter_allbooks)}},
                    {"id":2, "title":_("By authors"), "link":("opds_catalog:lang_authors" if config.SOPDS_ALPHABET_MENU else "opds_catalog:nolang_authors"),
                     "descr": _("Authors: %(authors)s."),"counters":{"authors":Counter.objects.get_counter(models.counter_allauthors)}},
                    {"id":3, "title":_("By titles"), "link":("opds_catalog:lang_books" if config.SOPDS_ALPHABET_MENU else "opds_catalog:nolang_books"),
                     "descr": _("Books: %(books)s."),"counters":{"books":Counter.objects.get_counter(models.counter_allbooks)}},
                    {"id":4, "title":_("By genres"), "link":"opds_catalog:genres",
                     "descr": _("Genres: %(genres)s."),"counters":{"genres":Counter.objects.get_counter(models.counter_allgenres)}},
                    {"id":5, "title":_("By series"), "link":("opds_catalog:lang_series" if config.SOPDS_ALPHABET_MENU else "opds_catalog:nolang_series"),
                     "descr": _("Series: %(series)s."),"counters":{"series":Counter.objects.get_counter(models.counter_allseries)}},
        ]
        if config.SOPDS_AUTH and self.request.user.is_authenticated:
            mainitems += [
                        {"id":6, "title":_("%(username)s Book shelf")%({"username":self.request.user.username}), "link":"opds_catalog:bookshelf",
                         "descr":_("%(username)s books readed: %(bookshelf)s."),"counters":{"bookshelf":bookshelf.objects.filter(user=self.request.user).count(),"username":self.request.user.username}},
            ]

        return mainitems

    def item_link(self, item):
        return reverse(item['link'])

    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return item['descr']%item['counters']

    def item_guid(self, item):
        return "m:%s"%item["id"]

    def item_updateddate(self):
        return timezone.now()

    def item_enclosures(self, item):
        return (opdsEnclosure(reverse(item['link']),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)

    def item_extra_kwargs(self, item):
        disable_item_links = (list(item['counters'].values())[0]==0)   
        return {'disable_item_links':disable_item_links}      
                
class CatalogsFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def get_object(self, request, cat_id=None, page=1):
        if not isinstance(page, int):
            page = int(page)
        page_num = page if page>0 else 1

        try:
            if cat_id is not None:
                cat = Catalog.objects.get(id=cat_id)
            else:
                cat = Catalog.objects.get(parent__id=cat_id)
        except Catalog.DoesNotExist:
            cat = None
        
        catalogs_list = Catalog.objects.filter(parent=cat).order_by("cat_name")
        catalogs_count = catalogs_list.count()
        # prefetch_related on sqlite on items >999 therow error "too many SQL variables"
        #books_list = Book.objects.filter(catalog=cat).prefetch_related('authors','genres','series').order_by("title")
        books_list = Book.objects.filter(catalog=cat).order_by("search_title")
        books_count = books_list.count()
        
        # Получаем результирующий список
        op = OPDS_Paginator(catalogs_count, books_count, page_num, config.SOPDS_MAXITEMS)
        items = []
        
        for row in catalogs_list[op.d1_first_pos:op.d1_last_pos+1]:
            p = {'is_catalog':1, 'title': row.cat_name,'id': row.id, 'cat_type':row.cat_type, 'parent_id':row.parent_id}       
            items.append(p)
              
        for row in books_list[op.d2_first_pos:op.d2_last_pos+1]:
            p = {'is_catalog':0, 'lang_code': row.lang_code, 'filename': row.filename, 'path': row.path, \
                  'registerdate': row.registerdate, 'id': row.id, 'annotation': strip_tags(row.annotation), \
                  'docdate': row.docdate, 'format': row.format, 'title': row.title, 'filesize': row.filesize//1000,
                  'authors':row.authors.values(), 'genres':row.genres.values(), 'series':row.series.values(), 'ser_no':row.bseries_set.values('ser_no')}
            items.append(p)
            
        return items, cat, op.get_data_dict()            

    def title(self, obj):
        items, cat, paginator = obj
        if cat.parent:
            return "%s | %s | %s"%(settings.TITLE,_("By catalogs"), cat.path)
        else:
            return "%s | %s"%(settings.TITLE,_("By catalogs"))

    def link(self, obj):
        items, cat, paginator = obj
        return reverse("opds_catalog:cat_page", kwargs={"cat_id":cat.id, "page":paginator['number']})

    def feed_extra_kwargs(self, obj):
        items, cat, paginator = obj
        start_url = reverse("opds_catalog:main")
        if paginator['has_previous']:
            prev_url = reverse("opds_catalog:cat_page", kwargs={"cat_id":cat.id,"page":paginator['previous_page_number']})
        else:
            prev_url  = None

        if paginator['has_next']:
            next_url = reverse("opds_catalog:cat_page", kwargs={"cat_id":cat.id,"page":paginator['next_page_number']})
        else:
            next_url  = None

        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":start_url,
                "prev_url":prev_url,
                "next_url":next_url,
        }

    def items(self, obj):
        items, cat, paginator = obj
        return items

    def item_title(self, item):
        return item['title']

    def item_guid(self, item):
        gp = 'c:' if item['is_catalog'] else 'b:'
        return "%s%s"%(gp,item['id'])

    def item_link(self, item):
        if item['is_catalog']:
            return reverse("opds_catalog:cat_tree", kwargs={"cat_id":item['id']})
        else:
            return reverse("opds_catalog:download", kwargs={"book_id":item['id'],"zip_flag":0})

    def item_enclosures(self, item):
        if item['is_catalog']:
            return (opdsEnclosure(reverse("opds_catalog:cat_tree", kwargs={"cat_id":item['id']}),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
        else:
            mime = mime_detector.fmt(item['format'])
            enclosure = [opdsEnclosure(reverse("opds_catalog:download", kwargs={"book_id": item['id'], "zip_flag": 0}), mime, "http://opds-spec.org/acquisition/open-access"),]
            if not item['format'] in settings.NOZIP_FORMATS:
                mimezip = Mimetype.FB2_ZIP if mime == Mimetype.FB2 else "%s+zip" % mime
                enclosure += [opdsEnclosure(reverse("opds_catalog:download", kwargs={"book_id": item['id'], "zip_flag": 1}), mimezip, "http://opds-spec.org/acquisition/open-access")]
            enclosure += [opdsEnclosure(reverse("opds_catalog:cover", kwargs={"book_id": item['id']}), "image/jpeg","http://opds-spec.org/image"),
                          opdsEnclosure(reverse("opds_catalog:thumb", kwargs={"book_id": item['id']}), "image/jpeg","http://opds-spec.org/thumbnail"),
                          ]
            if (config.SOPDS_FB2TOEPUB != "") and (item['format'] == 'fb2'):
                enclosure += [opdsEnclosure(reverse("opds_catalog:convert", kwargs={"book_id": item['id'], "convert_type": "epub"}),Mimetype.EPUB, "http://opds-spec.org/acquisition/open-access")]
            if (config.SOPDS_FB2TOMOBI != "") and (item['format'] == 'fb2'):
                enclosure += [opdsEnclosure(reverse("opds_catalog:convert", kwargs={"book_id": item['id'], "convert_type": "mobi"}),Mimetype.MOBI, "http://opds-spec.org/acquisition/open-access")]

            return enclosure
    
    def item_description(self, item):
        if item['is_catalog']:
            return item['title']
        else: 
            s="<b> Book name: </b>%(title)s<br/>"
            if item['authors']: s += _("<b>Authors: </b>%(authors)s<br/>")
            if item['genres']: s += _("<b>Genres: </b>%(genres)s<br/>")
            if item['series']: s += _("<b>Series: </b>%(series)s<br/>")
            if item['ser_no']: s += _("<b>No in Series: </b>%(ser_no)s<br/>")
            s += _("<b>File: </b>%(filename)s<br/><b>File size: </b>%(filesize)s<br/><b>Changes date: </b>%(docdate)s<br/>")
            s +="<p class='book'>%(annotation)s</p>"
            return s%{'title':item['title'],'filename':item['filename'], 'filesize':item['filesize'],'docdate':item['docdate'],'annotation':item['annotation'],
                      'authors':", ".join(a['full_name'] for a in item['authors']),
                      'genres':", ".join(g['subsection'] for g in item['genres']),
                      'series':", ".join(s['ser'] for s in item['series']),
                      'ser_no': ", ".join(str(s['ser_no']) for s in item['ser_no']),
                      }
                            
def OpenSearch(request):
    """
    Выводим шаблон поиска
    """
    return render(request, 'opensearch.html')

class SearchTypesFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def get_object(self, request, searchterms=""):
        return searchterms.replace('+',' ')

    def link(self, obj):
        return "%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/')

    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }

    def items(self, obj):
        return [
                    {"id":1, "title":_("Search by titles"), "term":obj, "descr": _("Search books by title")},
                    {"id":2, "title":_("Search by authors"), "term":obj, "descr": _("Search authors by name")},
                    {"id":3, "title":_("Search series"), "term":obj, "descr": _("Search series")},
        ]

    def item_link(self, item):
        if item["id"] == 1:
            return reverse("opds_catalog:searchbooks", kwargs={"searchtype":"m", "searchterms":item["term"]})
        elif item["id"] == 2:
            return reverse("opds_catalog:searchauthors", kwargs={"searchtype":"m", "searchterms":item["term"]})
        elif item["id"] == 3:
            return reverse("opds_catalog:searchseries", kwargs={"searchtype":"m", "searchterms":item["term"]})
        return None
             
    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return item['descr']

    def item_guid(self, item):
        return "st:%s"%item["id"]

    def item_updateddate(self):
        return timezone.now()

    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)

class SearchBooksFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE
    
    def title(self, obj):
        return "%s | %s (%s)"%(settings.TITLE,_("Books found"),_("doubles hide") if config.SOPDS_DOUBLES_HIDE else _("doubles show"))    

    def get_object(self, request, searchtype="m", searchterms=None, searchterms0=None, page=1):   
        if not isinstance(page, int):
            page = int(page)
        page_num = page if page>0 else 1
        
        # Поиск книг по подсроке
        if  searchtype == 'm':
            #books = Book.objects.extra(where=["upper(title) like %s"], params=["%%%s%%"%searchterms.upper()]).order_by('title','-docdate')
            books = Book.objects.filter(search_title__contains=searchterms.upper()).order_by('search_title','-docdate')
        # Поиск книг по начальной подстроке
        elif searchtype == 'b':
            #books = Book.objects.extra(where=["upper(title) like %s"], params=["%s%%"%searchterms.upper()]).order_by('title','-docdate')
            books = Book.objects.filter(search_title__startswith=searchterms.upper()).order_by('search_title','-docdate')
        # Поиск книг по точному совпадению наименования
        elif searchtype == 'e':
            #books = Book.objects.extra(where=["upper(title)=%s"], params=["%s"%searchterms.upper()]).order_by('title','-docdate')
            books = Book.objects.filter(search_title=searchterms.upper()).order_by('search_title','-docdate')
        # Поиск книг по автору
        elif searchtype == 'a':
            try:
                author_id = int(searchterms)
            except:
                author_id = 0
            books = Book.objects.filter(authors=author_id).order_by('search_title','-docdate')
        # Поиск книг по серии
        elif searchtype == 's':
            try:
                ser_id = int(searchterms)
            except:
                ser_id = 0
            #books = Book.objects.filter(series=ser_id).order_by('search_title','-docdate')
            books = Book.objects.filter(series=ser_id).order_by('bseries__ser_no', 'search_title', '-docdate')
        # Поиск книг по автору и серии
        elif searchtype == "as":
            try:
                ser_id = int(searchterms0)
                author_id = int(searchterms)
            except:
                ser_id = 0
                author_id = 0 
            books = Book.objects.filter(authors=author_id, series=ser_id if ser_id else None).order_by('bseries__ser_no', 'search_title', '-docdate')
        # Поиск книг по жанру
        elif searchtype == 'g':
            try:
                genre_id = int(searchterms)
            except:
                genre_id = 0
            books = Book.objects.filter(genres=genre_id).order_by('search_title','-docdate')    
        # Поиск книг на книжной полке            
        elif searchtype == 'u':
            if config.SOPDS_AUTH:
                books = Book.objects.filter(bookshelf__user=request.user).order_by('-bookshelf__readtime')
            else:
                books=Book.objects.filter(id=0)  
        # Поиск дубликатов для книги            
        elif searchtype == 'd':
            book_id = int(searchterms)
            mbook = Book.objects.get(id=book_id)
            books = Book.objects.filter(title__iexact=mbook.title, authors__in=mbook.authors.all()).exclude(id=book_id).order_by('search_title','-docdate')
                    
        # prefetch_related on sqlite on items >999 therow error "too many SQL variables"
        #if len(books)>0:            
            #books = books.prefetch_related('authors','genres','series').order_by('title','authors','-docdate')
                 
        # Фильтруем дубликаты
        books_count = books.count()
        op = OPDS_Paginator(books_count, 0, page_num,config.SOPDS_MAXITEMS)
        items = []
        
        prev_title = ''
        prev_authors_set = set()
        
        # Начаинам анализ с последнего элемента на предидущей странице, чторбы он "вытянул" с этой страницы
        # свои дубликаты если они есть
        summary_DOUBLES_HIDE =  config.SOPDS_DOUBLES_HIDE and (searchtype != 'd')
        start = op.d1_first_pos if ((op.d1_first_pos==0) or (not summary_DOUBLES_HIDE)) else op.d1_first_pos-1
        finish = op.d1_last_pos
        
        for row in books[start:finish+1]:
            p = {'doubles':0, 'lang_code': row.lang_code, 'filename': row.filename, 'path': row.path, \
                  'registerdate': row.registerdate, 'id': row.id, 'annotation': strip_tags(row.annotation), \
                  'docdate': row.docdate, 'format': row.format, 'title': row.title, 'filesize': row.filesize//1000,
                  'authors':row.authors.values(), 'genres':row.genres.values(), 'series':row.series.values(), 'ser_no':row.bseries_set.values('ser_no')}
            if summary_DOUBLES_HIDE:
                title = p['title'] 
                authors_set = {a['id'] for a in p['authors']}         
                if title.upper()==prev_title.upper() and authors_set==prev_authors_set:
                    items[-1]['doubles']+=1
                else:
                    items.append(p)                   
                prev_title = title
                prev_authors_set = authors_set
            else:
                items.append(p)
                
        # "вытягиваем" дубликаты книг со следующей страницы и удаляем первый элемент который с предыдущей страницы и "вытягивал" дубликаты с текущей
        if summary_DOUBLES_HIDE:
            double_flag = True
            while ((finish+1)<books_count) and double_flag:
                finish += 1  
                if books[finish].title.upper()==prev_title.upper() and {a['id'] for a in books[finish].authors.values()}==prev_authors_set:
                    items[-1]['doubles']+=1
                else:
                    double_flag = False   
            
            if op.d1_first_pos!=0:     
                items.pop(0)          
                  
        return {"books":items, "searchterms":searchterms, "searchterms0":searchterms0, "searchtype":searchtype, "paginator":op.get_data_dict()}

    def get_link_kwargs(self, obj):
        kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"]}
        if obj.get("searchterms0") is not None:
            kwargs["searchterms0"]=obj["searchterms0"]
        return kwargs
        
    def link(self, obj):
        return reverse("opds_catalog:searchbooks", kwargs=self.get_link_kwargs(obj))

    def feed_extra_kwargs(self, obj):
        kwargs = self.get_link_kwargs(obj)
        if obj["paginator"]["has_previous"]:
            kwargs["page"]=obj["paginator"]['previous_page_number']
            prev_url = reverse("opds_catalog:searchbooks", kwargs=kwargs)
        else:
            prev_url  = None

        if obj["paginator"]["has_next"]:
            kwargs["page"]=obj["paginator"]['next_page_number']
            next_url = reverse("opds_catalog:searchbooks", kwargs=kwargs)
        else:
            next_url  = None
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text/html",
                "prev_url":prev_url,
                "next_url":next_url,
        }

    def items(self, obj):
        return obj["books"]

    def item_title(self, item):     
        return item['title']

    def item_guid(self, item):
        return "b:%s"%(item['id'])

    def item_link(self, item):
        return reverse("opds_catalog:download", kwargs={"book_id":item['id'],"zip_flag":0})
  
    def item_updateddate(self, item):
        return item['registerdate'] 
         
    def item_enclosures(self, item):
        mime = mime_detector.fmt(item['format'])
        enclosure = [
            opdsEnclosure(reverse("opds_catalog:download", kwargs={"book_id": item['id'], "zip_flag": 0}), mime, "http://opds-spec.org/acquisition/open-access"), ]
        if not item['format'] in settings.NOZIP_FORMATS:
            mimezip = Mimetype.FB2_ZIP if mime==Mimetype.FB2 else "%s+zip"%mime
            enclosure += [opdsEnclosure(reverse("opds_catalog:download", kwargs={"book_id": item['id'], "zip_flag": 1}), mimezip, "http://opds-spec.org/acquisition/open-access")]
        enclosure += [opdsEnclosure(reverse("opds_catalog:cover", kwargs={"book_id": item['id']}), "image/jpeg", "http://opds-spec.org/image"),
                      opdsEnclosure(reverse("opds_catalog:thumb", kwargs={"book_id": item['id']}), "image/jpeg", "http://opds-spec.org/thumbnail"),
                      ]
        if (config.SOPDS_FB2TOEPUB != "") and (item['format'] == 'fb2'):
            enclosure += [
                opdsEnclosure(reverse("opds_catalog:convert", kwargs={"book_id": item['id'], "convert_type": "epub"}), Mimetype.EPUB, "http://opds-spec.org/acquisition/open-access")]
        if (config.SOPDS_FB2TOMOBI != "") and (item['format'] == 'fb2'):
            enclosure += [
                opdsEnclosure(reverse("opds_catalog:convert", kwargs={"book_id": item['id'], "convert_type": "mobi"}), Mimetype.MOBI, "http://opds-spec.org/acquisition/open-access")]

        return enclosure
        
    def item_extra_kwargs(self, item): 
        return {'authors':item['authors'],'genres':item['genres'], 'doubles': item['id'] if item['doubles']>0 else None}    
    
    def item_description(self, item):
        s="<b> Book name: </b>%(title)s<br/>"
        if item['authors']: s += _("<b>Authors: </b>%(authors)s<br/>")
        if item['genres']: s += _("<b>Genres: </b>%(genres)s<br/>")
        if item['series']: s += _("<b>Series: </b>%(series)s<br/>")
        if item['ser_no']: s += _("<b>No in Series: </b>%(ser_no)s<br/>")
        s += _("<b>File: </b>%(filename)s<br/><b>File size: </b>%(filesize)s<br/><b>Changes date: </b>%(docdate)s<br/>")
        if item['doubles']: s += _("<b>Doubles count: </b>%(doubles)s<br/>")
        s +="<p class='book'>%(annotation)s</p>"
        return s%{'title':item['title'],'filename':item['filename'], 'filesize':item['filesize'],'docdate':item['docdate'],
                  'doubles':item['doubles'],'annotation':item['annotation'],
                  'authors':", ".join(a['full_name'] for a in item['authors']),
                  'genres':", ".join(g['subsection'] for g in item['genres']),
                  'series':", ".join(s['ser'] for s in item['series']),
                  'ser_no': ", ".join(str(s['ser_no']) for s in item['ser_no']),
                  }                        

class SelectSeriesFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE
    
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Series by authors select")) 

    def get_object(self, request, searchtype, searchterms):
        try:
            author_id=int(searchterms)
        except:
            author_id = 0
        return author_id
    
    def link(self, obj):
        return reverse("opds_catalog:searchbooks",kwargs={'searchtype':"as",'searchterms':obj})

    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }

    def items(self, obj):
        return [
                    {"id":1, "title":_("Books by series"), "author":obj, "descr": _("Books by author and series")},
                    {"id":2, "title":_("Books outside series"), "author":obj, "descr": _("Books by author outside series")},
                    {"id":3, "title":_("Books by alphabet"), "author":obj, "descr": _("Books by author alphabetical order")},
        ]

    def item_link(self, item):
        if item["id"] == 1:
            return reverse("opds_catalog:searchseries", kwargs={"searchtype":'a', "searchterms":item["author"]})
        elif item["id"] == 2:
            return reverse("opds_catalog:searchbooks", kwargs={"searchtype":"as", "searchterms":item["author"], "searchterms0":0})
        elif item["id"] == 3:
            return reverse("opds_catalog:searchbooks", kwargs={"searchtype":'a', "searchterms":item["author"]})
             
    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return item['descr']

    def item_guid(self, item):
        return "as:%s"%item["id"]

    def item_updateddate(self):
        return timezone.now()

    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
            
class SearchAuthorsFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE
    
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Authors found"))    

    def get_object(self, request, searchterms, searchtype, page=1):
        if not isinstance(page, int):
            page = int(page)
        page_num = page if page>0 else 1   

        if searchtype == 'm':
            authors = Author.objects.filter(search_full_name__contains=searchterms.upper()).order_by("search_full_name")
        elif searchtype == 'b':
            authors = Author.objects.filter(search_full_name__startswith=searchterms.upper()).order_by("search_full_name") 
        elif searchtype == 'e':
            authors = Author.objects.filter(search_full_name=searchterms.upper()).order_by("search_full_name")
            
        # Создаем результирующее множество
        authors_count = authors.count()
        op = OPDS_Paginator(authors_count, 0, page_num, config.SOPDS_MAXITEMS)        
        items = []
        
        for row in authors[op.d1_first_pos:op.d1_last_pos+1]:
            p = {'id':row.id, 'full_name':row.full_name, 'lang_code': row.lang_code, 'book_count': Book.objects.filter(authors=row).count()}
            items.append(p)    
                                
        return {"authors":items, "searchterms":searchterms, "searchtype":searchtype, "paginator":op.get_data_dict()}

    def link(self, obj):
        return reverse("opds_catalog:searchauthors", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"]})

    def feed_extra_kwargs(self, obj):
        if obj["paginator"]['has_previous']:
            prev_url = reverse("opds_catalog:searchauthors", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["paginator"]['previous_page_number'])})
        else:
            prev_url  = None

        if obj["paginator"]['has_next']:
            next_url = reverse("opds_catalog:searchauthors", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["paginator"]['next_page_number'])})
        else:
            next_url  = None
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
                "prev_url":prev_url,
                "next_url":next_url,
        }

    def items(self, obj):
        return obj["authors"]

    def item_title(self, item):
        return item['full_name']
    
    def item_description(self, item):
        return _("Books count: %s")%(Book.objects.filter(authors=item['id']).count())     

    def item_guid(self, item):
        return "a:%s"%(item['id'])

    def item_link(self, item):
        return reverse("opds_catalog:searchbooks", kwargs={"searchtype":"as", "searchterms":item['id']}) 

    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)

class SearchSeriesFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE
    
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Series found"))    

    def get_object(self, request, searchterms, searchtype, page=1):
        self.author_id = None
        if not isinstance(page, int):
            page = int(page)
        page_num = page if page>0 else 1  

        if searchtype == 'm':
            series = Series.objects.filter(search_ser__contains=searchterms.upper())
        elif searchtype == 'b':
            series = Series.objects.filter(search_ser__startswith=searchterms.upper())
        elif searchtype == 'e':     
            series = Series.objects.filter(search_ser=searchterms.upper())       
        elif searchtype == 'a':
            try:
                self.author_id = int(searchterms)
            except:
                self.author_id = None
            series = Series.objects.filter(book__authors=self.author_id)
            
        series = series.annotate(count_book=Count('book')).distinct().order_by('search_ser')  
        
        # Создаем результирующее множество
        series_count = series.count()
        op = OPDS_Paginator(series_count, 0, page_num, config.SOPDS_MAXITEMS)        
        items = []
        
        for row in series[op.d1_first_pos:op.d1_last_pos+1]:
            p = {'id':row.id, 'ser':row.ser, 'lang_code': row.lang_code, 'book_count': row.count_book}
            items.append(p)   
        
        return {"series":items, "searchterms":searchterms, "searchtype":searchtype, "paginator":op.get_data_dict()}
    
    def link(self, obj):
        return reverse("opds_catalog:searchseries", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"]})

    def feed_extra_kwargs(self, obj):
        if obj["paginator"]['has_previous']:
            prev_url = reverse("opds_catalog:searchseries", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["paginator"]['previous_page_number'])})
        else:
            prev_url  = None

        if obj["paginator"]['has_next']:
            next_url = reverse("opds_catalog:searchseries", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["paginator"]['next_page_number'])})
        else:
            next_url  = None
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
                "prev_url":prev_url,
                "next_url":next_url,
        }

    def items(self, obj):
        return obj["series"]

    def item_title(self, item):
        return "%s"%(item['ser'])
    
    def item_description(self, item):
        return _("Books count: %s")%item['book_count']    

    def item_guid(self, item):
        return "a:%s"%item['id']

    def item_link(self, item):        
        if self.author_id:
            kwargs={"searchtype":"as", "searchterms":self.author_id,"searchterms0":item['id']}
        else:
            kwargs={"searchtype":"s", "searchterms":item['id']}

        return reverse("opds_catalog:searchbooks", kwargs=kwargs) 

    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
    
class LangFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def link(self, obj):
        return self.request.path
        
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Select language"))    
    
    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }
        
    def items(self):
    # TODO: переделать, используя словарь lang_codes
        langitems = [
                    {"id":1, "title":_("Cyrillic")},
                    {"id":2, "title":_("Latin")},
                    {"id":3, "title":_("Digits")},
                    {"id":9, "title":_("Other symbols")},
                    {"id":0, "title":_("Show all")}
        ]
        return langitems
    
    def item_link(self, item):
        return self.request.path+str(item["id"])+'/'

    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return None
    
    def item_guid(self, item):
        return "l:%s"%item["id"]

    def item_updateddate(self):
        return timezone.now()

    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)

class BooksFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def link(self, obj):
        return self.request.path
        
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Select books by substring"))    
    
    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }

    def get_object(self, request, lang_code=0, chars = None):    
        self.lang_code = int(lang_code)
        if chars==None:
            chars=''
        return (len(chars)+1, chars.upper())
        
    def items(self, obj):
        length, chars = obj
        if self.lang_code:
            sql="""select %(length)s as l, substring(search_title,1,%(length)s) as id, count(*) as cnt 
                   from opds_catalog_book 
                   where lang_code=%(lang_code)s and search_title like '%(chars)s%%%%'
                   group by substring(search_title,1,%(length)s)
                   order by id"""%{'length':length, 'lang_code':self.lang_code, 'chars':chars}
        else:
            sql="""select %(length)s as l, substring(search_title,1,%(length)s) as id, count(*) as cnt 
                   from opds_catalog_book 
                   where search_title like '%(chars)s%%%%'
                   group by substring(search_title,1,%(length)s)
                   order by id"""%{'length':length,'chars':chars}
          
        dataset = Book.objects.raw(sql)
        return dataset

    def item_title(self, item):
        return "%s"%item.id
    
    def item_description(self, item):
        return _("Found: %s books")%item.cnt    

    def item_link(self, item):
        title_full = len(item.id)<item.l
        if item.cnt>=config.SOPDS_SPLITITEMS and not title_full:
            return reverse("opds_catalog:chars_books", kwargs={"lang_code":self.lang_code,"chars":item.id})
        else:
            return reverse("opds_catalog:searchbooks", \
                           kwargs={"searchtype":'b' if not title_full else 'e', "searchterms":item.id})
        
    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
    
class AuthorsFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def link(self, obj):
        return self.request.path
        
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Select authors by substring"))    
    
    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }

    def get_object(self, request, lang_code=0, chars = None):    
        self.lang_code = int(lang_code)
        if chars==None:
            chars=''
        return (len(chars)+1, chars.upper())
        
    def items(self, obj):
        length, chars = obj
        if self.lang_code:
            sql="""select %(length)s as l, substring(search_full_name,1,%(length)s) as id, count(*) as cnt 
                   from opds_catalog_author 
                   where lang_code=%(lang_code)s and search_full_name like '%(chars)s%%%%'
                   group by substring(search_full_name,1,%(length)s)
                   order by id"""%{'length':length, 'lang_code':self.lang_code, 'chars':chars}
        else:
            sql="""select %(length)s as l, substring(search_full_name,1,%(length)s) as id, count(*) as cnt 
                   from opds_catalog_author 
                   where search_full_name like '%(chars)s%%%%'
                   group by substring(search_full_name,1,%(length)s) 
                   order by id"""%{'length':length,'chars':chars}
          
        dataset = Author.objects.raw(sql)
        return dataset

    def item_title(self, item):
        return "%s"%item.id
    
    def item_description(self, item):
        return _("Found: %s authors")%item.cnt    

    def item_link(self, item):
        last_name_full = len(item.id)<item.l
        if (item.cnt>=config.SOPDS_SPLITITEMS) and not last_name_full:
            return reverse("opds_catalog:chars_authors", kwargs={"lang_code":self.lang_code,"chars":item.id})
        else:
            return reverse("opds_catalog:searchauthors", \
                           kwargs={"searchtype":'b' if not last_name_full else 'e', "searchterms":item.id})
        
    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
    
class SeriesFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def link(self, obj):
        return self.request.path
        
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Select series by substring"))    
    
    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }

    def get_object(self, request, lang_code=0, chars = None):    
        self.lang_code = int(lang_code)
        if chars==None:
            chars=''
        return (len(chars)+1, chars.upper())
        
    def items(self, obj):
        length, chars = obj
        if self.lang_code:
            sql="""select %(length)s as l, substring(search_ser,1,%(length)s) as id, count(*) as cnt 
                   from opds_catalog_series 
                   where lang_code=%(lang_code)s and search_ser like '%(chars)s%%%%'
                   group by substring(search_ser,1,%(length)s) 
                   order by id"""%{'length':length, 'lang_code':self.lang_code, 'chars':chars}
        else:
            sql="""select %(length)s as l, substring(search_ser,1,%(length)s) as id, count(*) as cnt 
                   from opds_catalog_series 
                   where search_ser like '%(chars)s%%%%'
                   group by substring(search_ser,1,%(length)s) 
                   order by id"""%{'length':length,'chars':chars}
          
        dataset = Series.objects.raw(sql)
        return dataset

    def item_title(self, item):
        return "%s"%item.id
    
    def item_description(self, item):
        return _("Found: %s series")%item.cnt    

    def item_link(self, item):
        series_full = len(item.id)<item.l
        if item.cnt>=config.SOPDS_SPLITITEMS and not series_full:
            return reverse("opds_catalog:chars_series", kwargs={"lang_code":self.lang_code,"chars":item.id})
        else:
            return reverse("opds_catalog:searchseries", \
                           kwargs={"searchtype":'b' if not series_full else 'e', "searchterms":item.id})
        
    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
    
class GenresFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def link(self, obj):
        return self.request.path
        
    def title(self, obj):
            return "%s | %s"%(settings.TITLE,_("Select genres (%s)")%(_("section") if obj==0 else _("subsection")))    
    
    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"%s%s"%(reverse("opds_catalog:opensearch"),'{searchTerms}/'),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }

    def get_object(self, request, section = 0):  
        if not isinstance(section, int):
            self.section_id = int(section)
        else:
            self.section_id = section
        return self.section_id
        
    def items(self, obj):
        section_id = obj
        if section_id==0:
            dataset = Genre.objects.values('section').annotate(section_id=Min('id'), num_book=Count('book')).filter(num_book__gt=0).order_by('section')
        else:
            section = Genre.objects.get(id=section_id).section
            dataset = Genre.objects.filter(section=section).annotate(num_book=Count('book')).filter(num_book__gt=0).values().order_by('subsection')       
        return dataset

    def item_title(self, item):
        return "%s"%(item['section'] if self.section_id==0 else item['subsection'])
    
    def item_description(self, item):
        return _("Found: %s books")%item['num_book']   

    def item_link(self, item):
        if self.section_id==0:
            return reverse("opds_catalog:genres", kwargs={"section":item['section_id']})
        else:
            return reverse("opds_catalog:searchbooks", kwargs={"searchtype":'g', "searchterms":item["id"]})
        
    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)

        