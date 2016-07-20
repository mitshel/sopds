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
from django.db.models import Count
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
                    {"id":5, "title":_("By series"), "link":"opds_catalog:series",
                     "descr": _("Series: %(series)s."),"counters":{"series":Counter.objects.get_counter(models.counter_allseries)}},
        ]
        if settings.AUTH and self.request.user.is_authenticated():
            mainitems += [
                        {"id":6, "title":_("%(username)s Book shelf")%({"username":self.request.user.username}), "link":"opds_catalog:bookshelf",
                         "descr":_("%(username)s books readed: %(bookshelf)s."),"counters":{"bookshelf":bookshelf.objects.count(),"username":self.request.user.username}},
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
                    {"id":3, "title":_("Search genres"), "term":obj, "descr": _("Search genres")},
        ]

    def item_link(self, item):
        if item["id"] == 1:
           return reverse("opds_catalog:searchbooks", kwargs={"searchtype":"books", "searchterms":item["term"]})
        elif item["id"] == 2:
           return reverse("opds_catalog:searchauthors", kwargs={"searchtype":"authors", "searchterms":item["term"]})
        #elif item["id"] == 3:
        #   return reverse("opds_catalog:searchgenres", kwargs={"searchtype":"genres", "searchterms":item["term"]})
        return reverse("opds_catalog:searchbooks", kwargs={"searchtype":"books", "searchterms":item["term"]})
             
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

    def get_object(self, request, searchterms, searchtype, page=1):
        if not isinstance(page, int):
            page = int(page)

        if  searchtype == 'books':
            books = Book.objects.extra(where=["upper(title) like %s"], params=["%%%s%%"%searchterms.upper()])
        elif searchtype == 'sbooks':
            books = Book.objects.extra(where=["upper(title) like %s"], params=["%s%%"%searchterms.upper()])
        elif searchtype == 'abooks':
            try:
                author_id = int(searchterms)
            except:
                author_id = 0
            books = Book.objects.filter(authors=author_id)
            
        return {"books":books, "searchterms":searchterms, "searchtype":searchtype, "page":page}

    def link(self, obj):
        return reverse("opds_catalog:searchbooks", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"]})

    def feed_extra_kwargs(self, obj):
        if obj["page"] != 1:
            prev_url = reverse("opds_catalog:searchbooks", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["page"]-1)})
        else:
            prev_url  = None

        if obj["page"]*settings.MAXITEMS<obj["books"].count():
            next_url = reverse("opds_catalog:searchbooks", kwargs={"searchtype":obj["searchtype"], "searchterms":obj["searchterms"], "page":(obj["page"]+1)})
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
        
class SearchAuthorsFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE
    #description_template = "autor_description.html"
    
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Authors found"))    

    def get_object(self, request, searchterms, searchtype, page=1):
        if not isinstance(page, int):
            page = int(page)

        if searchtype == 'authors':
            authors = Author.objects.extra(where=["upper(last_name) like %s"], params=["%%%s%%"%searchterms.upper()])
        elif searchtype == 'sauthors':
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
                "description_mime_type":"text/html",
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

    def item_guid(self, item):
        return "a:%s"%(item.id)

    def item_link(self, item):
        return reverse("opds_catalog:searchbooks", kwargs={"searchtype":'abooks', "searchterms":item.id}) 

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
        if item.cnt>=settings.SPLITBOOKS:
            return reverse("opds_catalog:chars_books", kwargs={"lang_code":self.lang_code,"chars":item.id})
        else:
            return reverse("opds_catalog:searchbooks", kwargs={"searchtype":'sbooks', "searchterms":item.id})
        
    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
    

class AuthorsFeed(AuthFeed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE

    def link(self, obj):
        return self.request.path
        
    def title(self, obj):
        return "%s | %s"%(settings.TITLE,_("Select authorss by substring"))    
    
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
            sql="""select upper(substr(last_name,1,%(length)s)) as id, count(*) as cnt 
                   from opds_catalog_author 
                   where lang_code=%(lang_code)s and upper(last_name) like '%(chars)s%%'
                   group by upper(substr(last_name,1,%(length)s)) 
                   order by id"""%{'length':length, 'lang_code':self.lang_code, 'chars':chars}
        else:
            sql="""select upper(substr(last_name,1,%(length)s)) as id, count(*) as cnt 
                   from opds_catalog_author 
                   where upper(last_name) like '%(chars)s%%'
                   group by upper(substr(last_name,1,%(length)s)) 
                   order by id"""%{'length':length,'chars':chars}
          
        dataset = Author.objects.raw(sql)
        return dataset

    def item_title(self, item):
        return "%s"%item.id
    
    def item_description(self, item):
        return _("Found: %s authors")%item.cnt    

    def item_link(self, item):
        if item.cnt>=settings.SPLITAUTHORS:
            return reverse("opds_catalog:chars_authors", kwargs={"lang_code":self.lang_code,"chars":item.id})
        else:
            return reverse("opds_catalog:searchauthors", kwargs={"searchtype":'sauthors', "searchterms":item.id})
        
    def item_enclosures(self, item):
        return (opdsEnclosure(self.item_link(item),"application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
    
    