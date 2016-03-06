
from django.conf.urls import url
from opds_catalog import feeds

urlpatterns = [
    url(r'^catalogs/',feeds.CatalogsFeed(), name='catalogs'),
    url(r'^authors/',feeds.MainFeed(), name='authors'),
    url(r'^titles/',feeds.BooksFeed(), name='titles'),
    url(r'^genres/',feeds.MainFeed(), name='genres'),
    url(r'^series/',feeds.MainFeed(), name='series'),
    url(r'^bookshelf/',feeds.MainFeed(), name='bookshelf'),
    url(r'^',feeds.MainFeed(), name='main'),
    #url(r'^(?P<url>.*)/$', Feed, {'feed_dict': feeds}),
]
