from itertools import chain

from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.feedgenerator import Atom1Feed, Enclosure, rfc3339_date
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Substr, Upper
from django.db.models import Count, Min, Sum
from django.utils.encoding import escape_uri_path

from opds_catalog.models import Book, Catalog, Author, Genre, Series, bookshelf, Counter
from opds_catalog import models
from opds_catalog import settings
from django.http.response import Http404

class AuthFeed(Feed):
    request = None
    def __call__(self,request,*args,**kwargs):
        self.request = request
        return super().__call__(request,*args,**kwargs)

class opdsEnclosure(Enclosure):
    def __init__(self, url, mime_type, rel):
        self.rel = rel
        super(opdsEnclosure,self).__init__(url, 0, mime_type)

class opdsFeed(Atom1Feed):
    content_type = 'text/xml; charset=utf-8'

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
        handler.characters("\n")
        if self.feed.get('link') is not None:
            handler.addQuickElement('link', None, {"href":self.feed["link"],"rel":"self","type":"application/atom+xml;profile=opds-catalog;kind=navigation"})
            handler.characters("\n")
        if self.feed.get('start_url') is not None:
            handler.addQuickElement('link', None, {"href":self.feed["start_url"],"rel":"start","type":"application/atom+xml;profile=opds-catalog;kind=navigation"})
            handler.characters("\n")
        if self.feed.get('icon') is not None:
            handler.addQuickElement('icon', settings.ICON)
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
                handler.addQuickElement("name", "%s %s"%(a.last_name,a.first_name))
                #handler.addQuickElement("uri", item['author_link'])
                handler.endElement("author")
                handler.addQuickElement("link", "", {"href": reverse("opds_catalog:searchbooks", kwargs={"searchtype":'a', "searchterms":a.id}), 
                                                     "rel": "related", 
                                                     "type":"application/atom+xml;profile=opds-catalog", 
                                                     "title":_("All books by %(last_name)s %(first_name)s")%{"last_name":a.last_name,"first_name":a.first_name}})
                handler.characters("\n")
         
        if item.get("genres") is not None:       
            for g in item["genres"]:
                handler.addQuickElement("category", "", {"term": g.subsection, "label": g.subsection})    
            handler.characters("\n")        

class MainFeed(AuthFeed):
    feed_type = opdsFeed
    title = settings.TITLE
    subtitle = settings.SUBTITLE

    def link(self):
        return reverse("opds_catalog:main")

    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"/opds/search/{searchTerms}/",
                #"searchTerm_url":reverse("opds_catalog:searchtypes",kwargs={"searchterms":"{searchTerms}"}),
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }

    def items(self):
        mainitems = [
                    {"id":1, "title":_("By catalogs"), "link":"opds_catalog:catalogs",
                     "descr": _("Catalogs: %(catalogs)s, books: %(books)s."),"counters":{"catalogs":Counter.objects.get_counter(models.counter_allcatalogs),"books":Counter.objects.get_counter(models.counter_allbooks)}},
                    {"id":2, "title":_("By authors"), "link":("opds_catalog:lang_authors" if settings.ALPHABET_MENU else "opds_catalog:nolang_authors"),
                     "descr": _("Authors: %(authors)s."),"counters":{"authors":Counter.objects.get_counter(models.counter_allauthors)}},
                    {"id":3, "title":_("By titles"), "link":("opds_catalog:lang_books" if settings.ALPHABET_MENU else "opds_catalog:nolang_books"),
                     "descr": _("Books: %(books)s."),"counters":{"books":Counter.objects.get_counter(models.counter_allbooks)}},
                    {"id":4, "title":_("By genres"), "link":"opds_catalog:genres",
                     "descr": _("Genres: %(genres)s."),"counters":{"genres":Counter.objects.get_counter(models.counter_allgenres)}},
                    {"id":5, "title":_("By series"), "link":("opds_catalog:lang_series" if settings.ALPHABET_MENU else "opds_catalog:nolang_series"),
                     "descr": _("Series: %(series)s."),"counters":{"series":Counter.objects.get_counter(models.counter_allseries)}},
        ]
        if settings.AUTH and self.request.user.is_authenticated():
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
    description_template = "book_description.html"

    def get_object(self, request, cat_id=None, page=1):
        if not isinstance(page, int):
            page = int(page)

        if cat_id is not None:
            return (Catalog.objects.get(id=cat_id), page)
        else:
            return (Catalog.objects.get(parent__id=cat_id), page)

    def title(self, obj):
        cat, current_page = obj
        if cat.parent:
            return "%s | %s | %s"%(settings.TITLE,_("By catalogs"), cat.path)
        else:
            return "%s | %s"%(settings.TITLE,_("By catalogs"))

    def link(self, obj):
        cat, current_page = obj
        return reverse("opds_catalog:cat_page", kwargs={"cat_id":cat.id, "page":current_page})

    def feed_extra_kwargs(self, obj):
        cat, current_page = obj
        start_url = reverse("opds_catalog:main")
        if current_page != 1:
            prev_url = reverse("opds_catalog:cat_page", kwargs={"cat_id":cat.id,"page":(current_page-1)})
        else:
            prev_url  = None

        if current_page*settings.MAXITEMS<Catalog.objects.filter(parent=cat).count() + Book.objects.filter(catalog=cat).count():
            next_url = reverse("opds_catalog:cat_page", kwargs={"cat_id":cat.id,"page":(current_page+1)})
        else:
            next_url  = None

        return {
                "searchTerm_url":"/opds/search/{searchTerms}/",
                "start_url":start_url,
                "prev_url":prev_url,
                "next_url":next_url,
        }

    def items(self, obj):
        cat, current_page = obj
        catalogs_list = Catalog.objects.filter(parent=cat).order_by("cat_type","cat_name")
        books_list = Book.objects.filter(catalog=cat).order_by("title")
        union_list = list(chain(catalogs_list,books_list))
        paginator = Paginator(union_list,settings.MAXITEMS)
        try:
            page = paginator.page(current_page)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        return page

    def item_title(self, item):
        if isinstance(item, Catalog):
            return item.cat_name
        else:
            return item.title

    def item_guid(self, item):
        if isinstance(item, Catalog):
            gp = 'c:'
        else:
            gp = 'b:'
        return "%s%s"%(gp,item.id)

    def item_link(self, item):
        if isinstance(item, Catalog):
            return reverse("opds_catalog:cat_tree", kwargs={"cat_id":item.id})
        else:
            return reverse("opds_catalog:download", kwargs={"book_id":item.id,"zip":0})

    def item_enclosures(self, item):
        if isinstance(item, Catalog):
            return (opdsEnclosure(reverse("opds_catalog:cat_tree", kwargs={"cat_id":item.id}),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
        else:
            return (
                opdsEnclosure(reverse("opds_catalog:download", kwargs={"book_id":item.id,"zip":0}),"application/fb2" ,"http://opds-spec.org/acquisition/open-access"),
                opdsEnclosure(reverse("opds_catalog:download", kwargs={"book_id":item.id,"zip":1}),"application/fb2+zip", "http://opds-spec.org/acquisition/open-access"),
                opdsEnclosure(reverse("opds_catalog:cover", kwargs={"book_id":item.id}),"image/jpeg", "http://opds-spec.org/image"),
            )
                            
def OpenSearch(request):
    """
    Выводим шаблон поиска
    """
    return render(request, 'opensearch.html')

class SearchTypesFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def get_object(self, request, searchterms=""):
        return searchterms

    def link(self, obj):
        return "/opds/search/{searchTerms}/"

    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"/opds/search/{searchTerms}/",
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
    description_template = "book_description.html"
    
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Books found"))    

    def get_object(self, request, searchtype="m", searchterms=None, searchterms0=None, page=1):
        if not isinstance(page, int):
            page = int(page)
        
        # Поиск книг по подсроке
        if  searchtype == 'm':
            books = Book.objects.extra(where=["upper(title) like %s"], params=["%%%s%%"%searchterms.upper()])
        # Поиск книг по начальной подстроке
        elif searchtype == 'b':
            books = Book.objects.extra(where=["upper(title) like %s"], params=["%s%%"%searchterms.upper()])
        # Поиск книг по автору
        elif searchtype == 'a':
            try:
                author_id = int(searchterms)
            except:
                author_id = 0
            books = Book.objects.filter(authors=author_id)
        # Поиск книг по серии
        elif searchtype == 's':
            try:
                ser_id = int(searchterms)
            except:
                ser_id = 0
            books = Book.objects.filter(series=ser_id)    
        # Поиск книг по автору и серии
        elif searchtype == 'as':
            try:
                ser_id = int(searchterms0)
                author_id = int(searchterms)
            except:
                ser_id = 0
                author_id = 0 
            books = Book.objects.filter(authors=author_id, series=ser_id if ser_id else None)
        # Поиск книг по жанру
        elif searchtype == 'g':
            try:
                genre_id = int(searchterms)
            except:
                genre_id = 0
            books = Book.objects.filter(genres=genre_id)    
        # Поиск книг на книжной полке            
        elif searchtype == 'u':
            if settings.AUTH:
                books = Book.objects\
                .filter(bookshelf__user=self.request.user)\
                .order_by('-readtime')
            else:
                books={}      
                 
        return {"books":books, "searchterms":searchterms, "searchterms0":searchterms0, "searchtype":searchtype, "page":page}

    def get_link_kwargs(self, obj):
        kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"]}
        if obj.get("serarchterms0") is not None:
            kwargs["searchterms0"]=obj["serarchterms0"]
        return kwargs
        
    def link(self, obj):
        return reverse("opds_catalog:searchbooks", kwargs=self.get_link_kwargs(obj))

    def feed_extra_kwargs(self, obj):
        kwargs = self.get_link_kwargs(obj)
        if obj["page"] != 1:
            kwargs["page"]=obj["page"]-1
            prev_url = reverse("opds_catalog:searchbooks", kwargs=kwargs)
        else:
            prev_url  = None

        if obj["page"]*settings.MAXITEMS<obj["books"].count():
            kwargs["page"]=obj["page"]+1
            next_url = reverse("opds_catalog:searchbooks", kwargs=kwargs)
        else:
            next_url  = None
        return {
                "searchTerm_url":"/opds/search/{searchTerms}/",
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text/html",
                "prev_url":prev_url,
                "next_url":next_url,
        }

    def items(self, obj):
        books_list = obj["books"].order_by("title")

        paginator = Paginator(books_list,settings.MAXITEMS)
        try:
            page = paginator.page(obj["page"])
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        return page

    def item_title(self, item):
        return item.title

    def item_guid(self, item):
        return "b:%s"%(item.id)

    def item_link(self, item):
        return reverse("opds_catalog:download", kwargs={"book_id":item.id,"zip":0})
  
    def item_updateddate(self, item):
        return item.registerdate   
         
    def item_enclosures(self, item):
        return (
            opdsEnclosure(reverse("opds_catalog:download", kwargs={"book_id":item.id,"zip":0}),"application/fb2" ,"http://opds-spec.org/acquisition/open-access"),
            opdsEnclosure(reverse("opds_catalog:download", kwargs={"book_id":item.id,"zip":1}),"application/fb2+zip", "http://opds-spec.org/acquisition/open-access"),
            opdsEnclosure(reverse("opds_catalog:cover", kwargs={"book_id":item.id}),"image/jpeg", "http://opds-spec.org/image"),
        )
        
    def item_extra_kwargs(self, item): 
        return {'authors':item.authors.all(),
                'genres':item.genres.all()}        

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
        return reverse("opds_catalog:searchbooks",kwargs={'searchtype':'as','searchterms':obj})

    def feed_extra_kwargs(self, obj):
        return {
                "searchTerm_url":"/opds/search/{searchTerms}/",
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
           return reverse("opds_catalog:searchbooks", kwargs={"searchtype":'as', "searchterms":item["author"], "searchterms0":0})
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

        if searchtype == 'm':
            authors = Author.objects.extra(where=["upper(last_name) like %s"], params=["%%%s%%"%searchterms.upper()])
        elif searchtype == 'b':
            authors = Author.objects.extra(where=["upper(last_name) like %s"], params=["%s%%"%searchterms.upper()])            
        return {"authors":authors, "searchterms":searchterms, "searchtype":searchtype, "page":page}

    def link(self, obj):
        return reverse("opds_catalog:searchauthors", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"]})

    def feed_extra_kwargs(self, obj):
        if obj["page"] != 1:
            prev_url = reverse("opds_catalog:searchauthors", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["page"]-1)})
        else:
            prev_url  = None

        if obj["page"]*settings.MAXITEMS<obj["authors"].count():
            next_url = reverse("opds_catalog:searchauthors", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["page"]+1)})
        else:
            next_url  = None
        return {
                "searchTerm_url":"/opds/search/{searchTerms}/",
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
                "prev_url":prev_url,
                "next_url":next_url,
        }

    def items(self, obj):
        authors_list = obj["authors"].order_by("last_name","first_name")

        paginator = Paginator(authors_list,settings.MAXITEMS)
        try:
            page = paginator.page(obj["page"])
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        return page

    def item_title(self, item):
        return "%s %s"%(item.last_name,item.first_name)
    
    def item_description(self, item):
        return _("Books count: %s")%(Book.objects.filter(authors=item.id).count())     

    def item_guid(self, item):
        return "a:%s"%(item.id)

    def item_link(self, item):
        return reverse("opds_catalog:searchbooks", kwargs={"searchtype":"as", "searchterms":item.id}) 

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

        if searchtype == 'm':
            series = Series.objects.extra(where=["upper(ser) like %s"], params=["%%%s%%"%searchterms.upper()])
        elif searchtype == 'b':
            series = Series.objects.extra(where=["upper(ser) like %s"], params=["%s%%"%searchterms.upper()]) 
        elif searchtype == 'a':
            try:
                self.author_id = int(searchterms)
                books = Book.objects.filter(authors=self.author_id)
            except:
                books = None
              
            series = Series.objects.filter(book__in=books)                 

        return {"series":series, "searchterms":searchterms, "searchtype":searchtype, "page":page}

    def link(self, obj):
        return reverse("opds_catalog:searchseries", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"]})

    def feed_extra_kwargs(self, obj):
        if obj["page"] != 1:
            prev_url = reverse("opds_catalog:searchseries", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["page"]-1)})
        else:
            prev_url  = None

        if obj["page"]*settings.MAXITEMS<obj["series"].count():
            next_url = reverse("opds_catalog:searchseries", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["page"]+1)})
        else:
            next_url  = None
        return {
                "searchTerm_url":"/opds/search/{searchTerms}/",
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
                "prev_url":prev_url,
                "next_url":next_url,
        }

    def items(self, obj):
        series_list = obj["series"].order_by("ser")

        paginator = Paginator(series_list,settings.MAXITEMS)
        try:
            page = paginator.page(obj["page"])
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        return page

    def item_title(self, item):
        return "%s"%(item.ser)
    
    def item_description(self, item):
        return _("Books count: %s")%(Book.objects.filter(series=item.id).count())    

    def item_guid(self, item):
        return "a:%s"%(item.id)

    def item_link(self, item):        
        if self.author_id:
            kwargs={"searchtype":"as", "searchterms":self.author_id,"searchterms0":item.id}
        else:
            kwargs={"searchtype":"s", "searchterms":item.id}

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
                "searchTerm_url":"/opds/search/{searchTerms}/",
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text",
        }
        
    def items(self):
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
                "searchTerm_url":"/opds/search/{searchTerms}/",
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
            sql="""select upper(substr(title,1,%(length)s)) as id, count(*) as cnt 
                   from opds_catalog_book 
                   where lang_code=%(lang_code)s and upper(title) like '%(chars)s%%'
                   group by upper(substr(title,1,%(length)s)) 
                   order by id"""%{'length':length, 'lang_code':self.lang_code, 'chars':chars}
        else:
            sql="""select upper(substr(title,1,%(length)s)) as id, count(*) as cnt 
                   from opds_catalog_book 
                   where upper(title) like '%(chars)s%%'
                   group by upper(substr(title,1,%(length)s)) 
                   order by id"""%{'length':length,'chars':chars}
          
        dataset = Book.objects.raw(sql)
        return dataset

    def item_title(self, item):
        return "%s"%item.id
    
    def item_description(self, item):
        return _("Found: %s books")%item.cnt    

    def item_link(self, item):
        if item.cnt>=settings.SPLITITEMS:
            return reverse("opds_catalog:chars_books", kwargs={"lang_code":self.lang_code,"chars":item.id})
        else:
            return reverse("opds_catalog:searchbooks", kwargs={"searchtype":'b', "searchterms":item.id})
        
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
                "searchTerm_url":"/opds/search/{searchTerms}/",
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
            sql="""select upper(substr(last_name || ' ' || first_name,1,%(length)s)) as id, count(*) as cnt 
                   from opds_catalog_author 
                   where lang_code=%(lang_code)s and upper(last_name || ' ' || first_name) like '%(chars)s%%'
                   group by upper(substr(last_name || ' ' || first_name,1,%(length)s)) 
                   order by id"""%{'length':length, 'lang_code':self.lang_code, 'chars':chars}
        else:
            sql="""select upper(substr(last_name || ' ' || first_name,1,%(length)s)) as id, count(*) as cnt 
                   from opds_catalog_author 
                   where upper(last_name || ' ' || first_name) like '%(chars)s%%'
                   group by upper(substr(last_name || ' ' || first_name,1,%(length)s)) 
                   order by id"""%{'length':length,'chars':chars}
          
        dataset = Author.objects.raw(sql)
        return dataset

    def item_title(self, item):
        return "%s"%item.id
    
    def item_description(self, item):
        return _("Found: %s authors")%item.cnt    

    def item_link(self, item):
        if item.cnt>=settings.SPLITITEMS:
            return reverse("opds_catalog:chars_authors", kwargs={"lang_code":self.lang_code,"chars":item.id})
        else:
            return reverse("opds_catalog:searchauthors", kwargs={"searchtype":'b', "searchterms":item.id})
        
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
                "searchTerm_url":"/opds/search/{searchTerms}/",
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
            sql="""select upper(substr(ser,1,%(length)s)) as id, count(*) as cnt 
                   from opds_catalog_series 
                   where lang_code=%(lang_code)s and upper(ser) like '%(chars)s%%'
                   group by upper(substr(ser,1,%(length)s)) 
                   order by id"""%{'length':length, 'lang_code':self.lang_code, 'chars':chars}
        else:
            sql="""select upper(substr(ser,1,%(length)s)) as id, count(*) as cnt 
                   from opds_catalog_series 
                   where upper(ser) like '%(chars)s%%'
                   group by upper(substr(ser,1,%(length)s)) 
                   order by id"""%{'length':length,'chars':chars}
          
        dataset = Series.objects.raw(sql)
        return dataset

    def item_title(self, item):
        return "%s"%item.id
    
    def item_description(self, item):
        return _("Found: %s series")%item.cnt    

    def item_link(self, item):
        if item.cnt>=settings.SPLITITEMS:
            return reverse("opds_catalog:chars_series", kwargs={"lang_code":self.lang_code,"chars":item.id})
        else:
            return reverse("opds_catalog:searchseries", kwargs={"searchtype":'b', "searchterms":item.id})
        
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
                "searchTerm_url":"/opds/search/{searchTerms}/",
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
