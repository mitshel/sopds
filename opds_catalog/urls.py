
from django.conf.urls import url
from opds_catalog.feeds import feeds, BooksEntries
from django.contrib.syndication.views import Feed

urlpatterns = [
    url(r'^books/$',BooksEntries())
    #url(r'^(?P<url>.*)/$', Feed, {'feed_dict': feeds}),
]
