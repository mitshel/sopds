
from django.conf.urls import url
from opds_catalog import feeds, views, dl

urlpatterns = [
    url(r'^catalogs/$',feeds.CatalogsFeed(), name='catalogs'),
    url(r'^catalogs/(?P<cat_id>[0-9]+)/$',feeds.CatalogsFeed(), name='cat_tree'),
    url(r'^authors/',feeds.MainFeed(), name='authors'),
    url(r'^titles/',feeds.BooksFeed(), name='titles'),
    url(r'^genres/',feeds.MainFeed(), name='genres'),
    url(r'^series/',feeds.MainFeed(), name='series'),
    url(r'^bookshelf/',feeds.MainFeed(), name='bookshelf'),
    url(r'^download/(?P<book_id>[0-9]+)/(?P<zip>[0-1])/$',dl.Download, name='download'),
    url(r'^cover/(?P<book_id>[0-9]+)/$',dl.Cover, name='cover'),
    url(r'^',feeds.MainFeed(), name='main'),
]
