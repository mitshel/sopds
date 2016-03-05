from django.utils.translation import ugettext as _
from django.utils.feedgenerator import Atom1Feed
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from opds_catalog.models import Book
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

    def add_item_elements(self, handler, item):
        super(opdsFeed, self).add_item_elements(handler, item)
        handler.addQuickElement('content', item['content'], {'type': 'text'})


class MainEntries(Feed):
    feed_type = opdsFeed
    title = settings.TITLE
    subtitle = settings.SUBTITLE
    link = "/opds/"

    def items(self):
        return (
               {'title':_('By catalogs'), 'link':'opds:catalogs'},
               {'title':_('By authors'), 'link':'opds:authors'},
               {'title':_('By titles'), 'link':'opds:titles'},
               {'title':_('By genres'), 'link':'opds:genres'},
               {'title':_('By series'), 'link':'opds:series'},
               {'title':_('Book shelf'), 'link':'opds:bookshelf'},
        )

    def item_link(self, item):
        return reverse(item['link'])

    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return None

    def item_extra_kwargs(self, item):
        return {"content":item["title"]}

class BooksEntries(Feed):
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
