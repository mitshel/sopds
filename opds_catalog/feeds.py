from django.utils.translation import ugettext as _
from django.utils.feedgenerator import Atom1Feed
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from opds_catalog.models import Book, Catalog, Author, Genre, Series, bookshelf
from opds_catalog import settings
from itertools import chain

class opdsFeed(Atom1Feed):
    def root_attributes(self):
        attrs = super(opdsFeed, self).root_attributes()
        attrs['xmlns'] = 'http://www.w3.org/2005/Atom'
        attrs['xmlns:dcterms'] = 'http://purl.org/dc/terms'
        return attrs

    def add_root_elements(self, handler):
        super(opdsFeed, self).add_root_elements(handler)
        handler.addQuickElement('icon', settings.ICON)
        if self.feed.get('search_url') is not None:
            handler.addQuickElement('link', "", {"href":self.feed["search_url"],"rel":"search","type":"application/opensearchdescription+xml"})
        if self.feed.get('searchTerm_url') is not None:
            handler.addQuickElement('link', "", {"href":self.feed["searchTerm_url"],"rel":"search","type":"application/atom+xml"})

    def add_item_elements(self, handler, item):
        handler.addQuickElement("title", item['title'])
        handler.addQuickElement("id", item['unique_id'])
        handler.addQuickElement("link", "", {"href": item['link'], "rel": "alternate"})

        if item.get("nav_link") is not None:
            handler.addQuickElement("link", "", {"href":item["nav_link"],
                                                 "type":"application/atom+xml;profile=opds-catalog"})
        if item.get("acq_fb2_link") is not None:
            handler.addQuickElement("link", "", {"href":item["acq_fb2_link"],
                                                 "rel":"http://opds-spec.org/acquisition/open-access",
                                                 "type":"application/fb2"})
        if item.get("acq_fb2zip_link") is not None:
            handler.addQuickElement("link", "", {"href":item["acq_fb2zip_link"],
                                                 "rel":"http://opds-spec.org/acquisition/open-access",
                                                 "type":"application/fb2+zip"})
        if item.get("acq_cover_link") is not None:
            handler.addQuickElement("link", "", {"href":item["acq_cover_link"],
                                                 "rel":"http://opds-spec.org/image",
                                                 "type":item["acq_cover_type"]})

        if item.get("description") is not None:
            handler.addQuickElement("content", item["description"], {"type": "text"})

class MainFeed(Feed):
    feed_type = opdsFeed
    title = settings.TITLE
    subtitle = settings.SUBTITLE
    guid_prefix = "m:"

    def link(self):
        return reverse("opds:main")

    def feed_url(self):
        return reverse("opds:main")

    def feed_extra_kwargs(self, obj):
        return {"search_url":"sopds.wsgi?id=09",
                "searchTerm_url":"sopds.wsgi?searchTerm={searchTerms}"}

    def items(self):
        return (
               {"id":1, "title":_("By catalogs"), "link":"opds:catalogs", "descr": _("Catalogs: %(catalogs)s, books: %(books)s.")},
               {"id":2, "title":_("By authors"), "link":"opds:authors", "descr": _("Authors: %(authors)s.")},
               {"id":3, "title":_("By titles"), "link":"opds:titles", "descr": _("Books: %(books)s.")},
               {"id":4, "title":_("By genres"), "link":"opds:genres", "descr": _("Genres: %(genres)s.")},
               {"id":5, "title":_("By series"), "link":"opds:series", "descr": _("Series: %(series)s.")},
               {"id":6, "title":_("Book shelf"), "link":"opds:bookshelf", "descr": _("Books readed: %(bookshelf)s.")},
        )

    def item_link(self, item):
        return reverse(item['link'])

    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        descr = None
        if item["id"]:
            if item["id"]==1:
                content = item["descr"]%{"catalogs":Catalog.objects.count(),"books":Book.objects.count()}
            elif item["id"]==2:
                content = item["descr"]%{"authors":Author.objects.count()}
            elif item["id"]==3:
                content = item["descr"]%{"books":Book.objects.count()}
            elif item["id"]==4:
                content = item["descr"]%{"genres":Genre.objects.count()}
            elif item["id"]==5:
                content = item["descr"]%{"series":Series.objects.count()}
            elif item["id"]==6:
                content = item["descr"]%{"bookshelf":bookshelf.objects.count()}
        return descr

    def item_guid(self, item):
        return "%s%s"%(self.guid_prefix,item["id"])

class CatalogsFeed(Feed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE
    guid_prefix = "с:"

    def get_object(self, request, cat_id=None):
        if cat_id is not None:
            return Catalog.objects.get(id=cat_id)
        else:
            return Catalog.objects.get(parent__id=cat_id)

    def title(self, obj):
        if obj.parent:
            return "%s | %s | %s"%(settings.TITLE,_("By catalogs"), obj.path)
        else:
            return "%s | %s"%(settings.TITLE,_("By catalogs"))

    def link(self, obj):
            return reverse("opds:cat_tree", kwargs={"cat_id":obj.id})

    def feed_extra_kwargs(self, obj):
        return {"search_url":"sopds.wsgi?id=09",
                "searchTerm_url":"sopds.wsgi?searchTerm={searchTerms}"}

    def items(self, obj):
        catalogs_list = Catalog.objects.filter(parent=obj).order_by("cat_type","cat_name")
        books_list = Book.objects.filter(catalog=obj).order_by("title")
        return list(chain(catalogs_list,books_list))

    def item_title(self, item):
        if isinstance(item, Catalog):
            return item.cat_name
        else:
            return item.title

    def item_description(self, item):
        if isinstance(item, Catalog):
            return item.path
        else:
            return item.annotation

    def item_guid(self, item):
        if isinstance(item, Catalog):
            gp = self.guid_prefix
        else:
            gp = 'b:'
        return "%s%s"%(gp,item.id)

    def item_link(self, item):
        if isinstance(item, Catalog):
            return reverse("opds:cat_tree", kwargs={"cat_id":item.id})
        else:
            return reverse("opds:titles")

    def item_extra_kwargs(self, item):
        if isinstance(item, Catalog):
            return {"nav_link":reverse("opds:cat_tree", kwargs={"cat_id":item.id})}
        else:
            return {"acq_fb2_link":"#",
                    "acq_fb2zip_link":"#",
                    "acq_cover_link":"#",
                    "acq_cover_type":"#"}

class BooksFeed(Feed):
    feed_type = opdsFeed
    title = "Мои книги"
    subtitle = settings.SUBTITLE
    link = "/opds/books/"

    def items(self):
        return Book.objects.all()[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.annotation

    def item_link(self, item):
        return '/%s'%item.filename
