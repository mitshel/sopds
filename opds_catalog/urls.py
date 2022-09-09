
from django.conf.urls import re_path
from opds_catalog import feeds, dl

app_name='opds_catalog'

urlpatterns = [
    re_path(r'^catalogs/$',feeds.CatalogsFeed(), name='catalogs'),
    re_path(r'^catalogs/(?P<cat_id>[0-9]+)/$',feeds.CatalogsFeed(), name='cat_tree'),
    re_path(r'^catalogs/(?P<cat_id>[0-9]+)/(?P<page>[0-9]+)/$',feeds.CatalogsFeed(), name='cat_page'),
    
    re_path(r'^books/$',feeds.LangFeed(), name='lang_books'),
    re_path(r'^books/0/$',feeds.BooksFeed(), name='nolang_books'),
    re_path(r'^books/(?P<lang_code>[0-9])/$',feeds.BooksFeed(), name='char_books'),
    re_path(r'^books/(?P<lang_code>[0-9])/(?P<chars>.+)/$',feeds.BooksFeed(), name='chars_books'),
    
    re_path(r'^authors/$',feeds.LangFeed(), name='lang_authors'),
    re_path(r'^authors/0/$',feeds.AuthorsFeed(), name='nolang_authors'),
    re_path(r'^authors/(?P<lang_code>[0-9])/$',feeds.AuthorsFeed(), name='char_authors'),
    re_path(r'^authors/(?P<lang_code>[0-9])/(?P<chars>.+)/$',feeds.AuthorsFeed(), name='chars_authors'),
    
    re_path(r'^series/$',feeds.LangFeed(), name='lang_series'),
    re_path(r'^series/0/$',feeds.SeriesFeed(), name='nolang_series'),
    re_path(r'^series/(?P<lang_code>[0-9])/$',feeds.SeriesFeed(), name='char_series'),
    re_path(r'^series/(?P<lang_code>[0-9])/(?P<chars>.+)/$',feeds.SeriesFeed(), name='chars_series'),
         
    re_path(r'^genres/$',feeds.GenresFeed(), name='genres'),
    re_path(r'^genres/(?P<section>\d+)/$',feeds.GenresFeed(), name='genres'),
    
    re_path(r'^search/$',feeds.OpenSearch, name='opensearch'),
    #re_path(r'search/{searchTerms}/$',feeds.OpenSearch, name='search_template'),
   
    re_path(r'^search/books/(?P<searchtype>[bmasgued])/(?P<searchterms>.+)/(?P<page>\d+)/$',feeds.SearchBooksFeed(), name='searchbooks'),
    re_path(r'^search/books/(?P<searchtype>[bmasgued])/(?P<searchterms>.+)/$',feeds.SearchBooksFeed(), name='searchbooks'),
    re_path(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/(?P<searchterms0>.+)/(?P<page>\d+)/$',feeds.SearchBooksFeed(), name='searchbooks'),
    re_path(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/(?P<searchterms0>.+)/$',feeds.SearchBooksFeed(), name='searchbooks'),
    re_path(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/$',feeds.SelectSeriesFeed(), name='searchbooks'),
    re_path(r'^search/books/u/0/$',feeds.SearchBooksFeed(), name='bookshelf'),
                 
    re_path(r'^search/authors/(?P<searchtype>[bme])/(?P<searchterms>.+)/(?P<page>\d+)/$',feeds.SearchAuthorsFeed(), name='searchauthors'),
    re_path(r'^search/authors/(?P<searchtype>[bme])/(?P<searchterms>.+)/$',feeds.SearchAuthorsFeed(), name='searchauthors'),
       
    re_path(r'^search/series/(?P<searchtype>[bmae])/(?P<searchterms>.+)/(?P<page>\d+)/$',feeds.SearchSeriesFeed(), name='searchseries'),
    re_path(r'^search/series/(?P<searchtype>[bmae])/(?P<searchterms>.+)/$',feeds.SearchSeriesFeed(), name='searchseries'),

    re_path(r'^search/(?P<searchterms>.+)/$',feeds.SearchTypesFeed(), name='searchtypes'),
    
    re_path(r'^convert/(?P<book_id>[0-9]+)/(?P<convert_type>.+)/$',dl.ConvertFB2, name='convert'),
    re_path(r'^download/(?P<book_id>[0-9]+)/(?P<zip_flag>[0-1])/$',dl.Download, name='download'),
    re_path(r'^cover/(?P<book_id>[0-9]+)/$',dl.Cover, name='cover'),
    re_path(r'^thumb/(?P<book_id>[0-9]+)/$',dl.Thumbnail, name='thumb'),
    re_path(r'^thumb/$',dl.Cover, name='covertmpl'),
        
    re_path(r'^$',feeds.MainFeed(), name='main'),
]

