from django.utils.translation import ugettext as _
from django.utils.feedgenerator import Atom1Feed, Enclosure
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from opds_catalog.models import Book, Catalog, Author, Genre, Series, bookshelf
from opds_catalog import settings
from itertools import chain


class opdsEnclosure(Enclosure):
    def __init__(self, url, mime_type, rel):
        self.rel = rel
        super(opdsEnclosure,self).__init__(url, 0, mime_type)

class opdsFeed(Atom1Feed):
    def root_attributes(self):
        attrs = super(opdsFeed, self).root_attributes()
        attrs['xmlns'] = 'http://www.w3.org/2005/Atom'
        attrs['xmlns:dcterms'] = 'http://purl.org/dc/terms'
        return attrs

    def add_root_elements(self, handler):
        super(opdsFeed, self).add_root_elements(handler)
        handler.addQuickElement('icon', settings.ICON)

        if self.feed.get('start_url') is not None:
            handler.addQuickElement('link', "", {"href":self.feed["start_url"],"rel":"start","type":"application/atom+xml;profile=opds-catalog;kind=navigation"})
        if self.feed.get('search_url') is not None:
            handler.addQuickElement('link', "", {"href":self.feed["search_url"],"rel":"search","type":"application/atom+xml;profile=opds-catalog;kind=navigation"})
        if self.feed.get('searchTerm_url') is not None:
            handler.addQuickElement('link', "", {"href":self.feed["searchTerm_url"],"rel":"search","type":"application/atom+xml"})

    def add_item_elements(self, handler, item):
        handler.addQuickElement("title", item['title'])
        handler.addQuickElement("id", item['unique_id'])
        handler.addQuickElement("link", "", {"href": item['link'], "rel": "alternate"})

        # Enclosures.
        for enclosure in item['enclosures']:
            enclosure = enclosure
            handler.addQuickElement('link', '', {
                'rel': enclosure.rel,
                'href': enclosure.url,
                'type': enclosure.mime_type,
            })

        if self.feed.get("description_mime_type") is not None:
            content_type = self.feed["description_mime_type"]
        else:
            content_type = "text/html"
        if item.get("description") is not None:
            handler.addQuickElement("content", item["description"], {"type": content_type})

class MainFeed(Feed):
    feed_type = opdsFeed
    title = settings.TITLE
    subtitle = settings.SUBTITLE
    guid_prefix = "m:"

    items = [
       {"id":1, "title":_("By catalogs"), "link":"opds_catalog:catalogs", "descr": _("Catalogs: %(catalogs)s, books: %(books)s.")%{"catalogs":Catalog.objects.count(),"books":Book.objects.count()}},
       {"id":2, "title":_("By authors"), "link":"opds_catalog:authors", "descr": _("Authors: %(authors)s.")%{"authors":Author.objects.count()}},
       {"id":3, "title":_("By titles"), "link":"opds_catalog:titles", "descr": _("Books: %(books)s.")%{"books":Book.objects.count()}},
       {"id":4, "title":_("By genres"), "link":"opds_catalog:genres", "descr": _("Genres: %(genres)s.")%{"genres":Genre.objects.count()}},
       {"id":5, "title":_("By series"), "link":"opds_catalog:series", "descr": _("Series: %(series)s.")%{"series":Series.objects.count()}},
       {"id":6, "title":_("Book shelf"), "link":"opds_catalog:bookshelf", "descr": _("Books readed: %(bookshelf)s.")%{"bookshelf":bookshelf.objects.count()}},
    ]

    def link(self):
        """
        Return link for rel="alternate"
        """
        return reverse("opds_catalog:main")

    def feed_url(self):
        """
        Return link for rel="self"
        """
        return reverse("opds_catalog:main")

    def feed_extra_kwargs(self, obj):
        return {"search_url":"sopds.wsgi?id=09",
                "searchTerm_url":"sopds.wsgi?searchTerm={searchTerms}",
                "start_url":reverse("opds_catalog:main"),
                "description_mime_type":"text"}

    def item_link(self, item):
        return reverse(item['link'])

    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return item['descr']

    def item_guid(self, item):
        return "%s%s"%(self.guid_prefix,item["id"])

class CatalogsFeed(Feed):
    feed_type = opdsFeed
    subtitle = settings.SUBTITLE
    description_template = "book_description.html"
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
        """
        Return link for rel="alternate"
        """
        return reverse("opds:cat_tree", kwargs={"cat_id":obj.id})

    def feed_url(self, obj):
        """
        Return link for rel="self"
        """
        return reverse("opds:cat_tree", kwargs={"cat_id":obj.id})

    def feed_extra_kwargs(self, obj):
        return {"search_url":"sopds.wsgi?id=09",
                "searchTerm_url":"sopds.wsgi?searchTerm={searchTerms}",
                "start_url":reverse("opds_catalog:main"),}

    def items(self, obj):
        catalogs_list = Catalog.objects.filter(parent=obj).order_by("cat_type","cat_name")
        books_list = Book.objects.filter(catalog=obj).order_by("title")
        return list(chain(catalogs_list,books_list))

    def item_title(self, item):
        if isinstance(item, Catalog):
            return item.cat_name
        else:
            return item.title

    # def item_description(self, item):
    #     if isinstance(item, Catalog):
    #         return item.path
    #     else:
    #         return item.annotation

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

    def item_enclosures(self, item):
        if isinstance(item, Catalog):
            return (opdsEnclosure("#","application/atom+xml;profile=opds-catalog;kind=navigation", "subsection"),)
        else:
            return (
                opdsEnclosure("#","application/fb2" ,"http://opds-spec.org/acquisition/open-access"),
                opdsEnclosure("#","application/fb2+zip", "http://opds-spec.org/acquisition/open-access"),
                opdsEnclosure("#","image/jpeg", "http://opds-spec.org/image"),
            )
    # def item_extra_kwargs(self, item):
    #     if isinstance(item, Catalog):
    #         return {"nav_link":reverse("opds:cat_tree", kwargs={"cat_id":item.id})}
    #     else:
    #         return {"acq_fb2_link":"#",
    #                 "acq_fb2zip_link":"#",
    #                 "acq_cover_link":"#",
    #                 "acq_cover_type":"#"}

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
