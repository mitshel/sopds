from django.utils.translation import ugettext as _
from django.utils.feedgenerator import Atom1Feed
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from opds_catalog.models import Book, Catalog, Author, Genre, Series, bookshelf
from opds_catalog import settings

class opdsFeed(Atom1Feed):
    def root_attributes(self):
        attrs = super(opdsFeed, self).root_attributes()
        attrs['xmlns'] = 'http://www.w3.org/2005/Atom'
        attrs['xmlns:dcterms'] = 'http://purl.org/dc/terms'
        return attrs

    def add_root_elements(self, handler):
        super(opdsFeed, self).add_root_elements(handler)
        handler.addQuickElement('icon', settings.ICON)
        if self.feed['search_url'] is not None:
            handler.addQuickElement('link', "", {"href":self.feed["search_url"],"rel":"search","type":"application/opensearchdescription+xml"})
        if self.feed['searchTerm_url'] is not None:
            handler.addQuickElement('link', "", {"href":self.feed["searchTerm_url"],"rel":"search","type":"application/atom+xml"})

    def add_item_elements(self, handler, item):
        super(opdsFeed, self).add_item_elements(handler, item)
        handler.addQuickElement('content', item['content'], {'type': 'text'})


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
               {"id":1, "title":_("By catalogs"), "link":"opds:catalogs", "content": _("Catalogs: %(catalogs)s, books: %(books)s.")},
               {"id":2, "title":_("By authors"), "link":"opds:authors", "content": _("Authors: %(authors)s.")},
               {"id":3, "title":_("By titles"), "link":"opds:titles", "content": _("Books: %(books)s.")},
               {"id":4, "title":_("By genres"), "link":"opds:genres", "content": _("Genres: %(genres)s.")},
               {"id":5, "title":_("By series"), "link":"opds:series", "content": _("Series: %(series)s.")},
               {"id":6, "title":_("Book shelf"), "link":"opds:bookshelf", "content": _("Books readed: %(bookshelf)s.")},
        )

    def item_link(self, item):
        return reverse(item['link'])

    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return None

    def item_guid(self, item):
        return "%s%s"%(self.guid_prefix,item["id"])

    def item_extra_kwargs(self, item):
        content = None
        if item["id"]:
            if item["id"]==1:
                content = item["content"]%{"catalogs":Catalog.objects.count(),"books":Book.objects.count()}
            elif item["id"]==2:
                content = item["content"]%{"authors":Author.objects.count()}
            elif item["id"]==3:
                content = item["content"]%{"books":Book.objects.count()}
            elif item["id"]==4:
                content = item["content"]%{"genres":Genre.objects.count()}
            elif item["id"]==5:
                content = item["content"]%{"series":Series.objects.count()}
            elif item["id"]==6:
                content = item["content"]%{"bookshelf":bookshelf.objects.count()}
        return {"content": content}


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
        return Catalog.objects.filter(parent=obj).order_by("cat_type","cat_name")

    def item_title(self, item):
        return item.cat_name

    def item_description(self, item):
        return None

    def item_guid(self, item):
        return "%s%s"%(self.guid_prefix,item.id)

    def item_link(self, item):
        return reverse("opds:cat_tree", kwargs={"cat_id":item.id})

    def item_extra_kwargs(self, item):
        return {"content": item.path}

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
