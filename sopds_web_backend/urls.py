
from django.conf.urls import url
from sopds_web_backend import views

urlpatterns = [
    url(r'^search/books/',views.SearchBooksView, name='searchbooks'),
#    url(r'^search/books/(?P<searchtype>[bmasgued])/(?P<searchterms>.+)/(?P<page>\d+)/',views.SearchBooksView, name='searchbooks'),
#    url(r'^search/books/(?P<searchtype>[bmasgued])/(?P<searchterms>.+)/',views.SearchBooksView, name='searchbooks'),    
#    url(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/(?P<searchterms0>.+)/(?P<page>\d+)/',views.SearchBooksView, name='searchbooks'),
#    url(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/(?P<searchterms0>.+)/',views.SearchBooksView, name='searchbooks'),
#    url(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/',views.SelectSeriesView, name='searchbooks'), 
#    url(r'^search/books/u/0/',views.SearchBooksView, name='bookshelf'),
                 
    url(r'^search/authors/(?P<searchtype>[bme])/(?P<searchterms>.+)/(?P<page>\d+)/',views.SearchAuthorsViews, name='searchauthors'),
    url(r'^search/authors/(?P<searchtype>[bme])/(?P<searchterms>.+)/',views.SearchAuthorsViews, name='searchauthors'),       
       
    url(r'^search/series/(?P<searchtype>[bmae])/(?P<searchterms>.+)/(?P<page>\d+)/',views.SelectSeriesView, name='searchseries'),
    url(r'^search/series/(?P<searchtype>[bmae])/(?P<searchterms>.+)/',views.SelectSeriesView, name='searchseries'), 
        
#    url(r'^search/(?P<searchterms>.+)/',feeds.SearchTypesFeed(), name='searchtypes'),      
    url(r'^',views.hello, name='main'),         
]
