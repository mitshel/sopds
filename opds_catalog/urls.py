
from django.conf.urls import url
from opds_catalog.feeds import BooksEntries, MainEntries

urlpatterns = [
    url(r'^catalogs/',MainEntries(), name='catalogs'),
    url(r'^authors/',MainEntries(), name='authors'),
    url(r'^titles/',BooksEntries(), name='titles'),
    url(r'^genres/',MainEntries(), name='genres'),
    url(r'^series/',MainEntries(), name='series'),
    url(r'^bookshelf/',MainEntries(), name='bookshelf'),
    url(r'^',MainEntries(), name='main'),
    #url(r'^(?P<url>.*)/$', Feed, {'feed_dict': feeds}),
]
