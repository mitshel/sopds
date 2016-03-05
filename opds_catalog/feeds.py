from django.utils.feedgenerator import Atom1Feed
from django.contrib.syndication.views import Feed
from opds_catalog.models import Book

class BooksEntries(Feed):
    title = "Мои книги"
    link = "/opds/books/"
    description = "Simple OPDS"

    feed_type = Atom1Feed

    def items(self):
        return Book.objects.all()[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.annotation

#    def subtitle(self, item):
#        return item.annotation

    def item_link(self, item):
        return item.filename


feeds = {'books':BooksEntries}