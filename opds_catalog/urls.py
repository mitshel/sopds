
from django.conf.urls import url
from opds_catalog import feeds, dl

app_name='opds_catalog'

urlpatterns = [
    url(r'^catalogs/$',feeds.CatalogsFeed(), name='catalogs'),
    url(r'^catalogs/(?P<cat_id>[0-9]+)/$',feeds.CatalogsFeed(), name='cat_tree'),
    url(r'^catalogs/(?P<cat_id>[0-9]+)/(?P<page>[0-9]+)/$',feeds.CatalogsFeed(), name='cat_page'),
    
    url(r'^books/$',feeds.LangFeed(), name='lang_books'),
    url(r'^books/0/$',feeds.BooksFeed(), name='nolang_books'), 
    url(r'^books/(?P<lang_code>[0-9])/$',feeds.BooksFeed(), name='char_books'),
    url(r'^books/(?P<lang_code>[0-9])/(?P<chars>.+)/$',feeds.BooksFeed(), name='chars_books'),
    
    url(r'^authors/$',feeds.LangFeed(), name='lang_authors'),
    url(r'^authors/0/$',feeds.AuthorsFeed(), name='nolang_authors'),
    url(r'^authors/(?P<lang_code>[0-9])/$',feeds.AuthorsFeed(), name='char_authors'),
    url(r'^authors/(?P<lang_code>[0-9])/(?P<chars>.+)/$',feeds.AuthorsFeed(), name='chars_authors'),
    
    url(r'^series/$',feeds.LangFeed(), name='lang_series'),
    url(r'^series/0/$',feeds.SeriesFeed(), name='nolang_series'),
    url(r'^series/(?P<lang_code>[0-9])/$',feeds.SeriesFeed(), name='char_series'),
    url(r'^series/(?P<lang_code>[0-9])/(?P<chars>.+)/$',feeds.SeriesFeed(), name='chars_series'),
         
    url(r'^genres/$',feeds.GenresFeed(), name='genres'),
    url(r'^genres/(?P<section>\d+)/$',feeds.GenresFeed(), name='genres'),
    
    url(r'^search/$',feeds.OpenSearch, name='opensearch'),
    #url(r'search/{searchTerms}/$',feeds.OpenSearch, name='search_template'),
   
    url(r'^search/books/(?P<searchtype>[bmasgued])/(?P<searchterms>.+)/(?P<page>\d+)/$',feeds.SearchBooksFeed(), name='searchbooks'),
    url(r'^search/books/(?P<searchtype>[bmasgued])/(?P<searchterms>.+)/$',feeds.SearchBooksFeed(), name='searchbooks'),
    url(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/(?P<searchterms0>.+)/(?P<page>\d+)/$',feeds.SearchBooksFeed(), name='searchbooks'),
    url(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/(?P<searchterms0>.+)/$',feeds.SearchBooksFeed(), name='searchbooks'),
    url(r'^search/books/(?P<searchtype>as)/(?P<searchterms>.+)/$',feeds.SelectSeriesFeed(), name='searchbooks'),
    url(r'^search/books/u/0/$',feeds.SearchBooksFeed(), name='bookshelf'),
                 
    url(r'^search/authors/(?P<searchtype>[bme])/(?P<searchterms>.+)/(?P<page>\d+)/$',feeds.SearchAuthorsFeed(), name='searchauthors'),
    url(r'^search/authors/(?P<searchtype>[bme])/(?P<searchterms>.+)/$',feeds.SearchAuthorsFeed(), name='searchauthors'),
       
    url(r'^search/series/(?P<searchtype>[bmae])/(?P<searchterms>.+)/(?P<page>\d+)/$',feeds.SearchSeriesFeed(), name='searchseries'),
    url(r'^search/series/(?P<searchtype>[bmae])/(?P<searchterms>.+)/$',feeds.SearchSeriesFeed(), name='searchseries'),

    url(r'^search/(?P<searchterms>.+)/$',feeds.SearchTypesFeed(), name='searchtypes'),
    
    url(r'^convert/(?P<book_id>[0-9]+)/(?P<convert_type>.+)/$',dl.ConvertFB2, name='convert'),
    url(r'^download/(?P<book_id>[0-9]+)/(?P<zip_flag>[0-1])/$',dl.Download, name='download'),
    url(r'^cover/(?P<book_id>[0-9]+)/$',dl.Cover, name='cover'),
    url(r'^thumb/(?P<book_id>[0-9]+)/$',dl.Thumbnail, name='thumb'),
    url(r'^thumb/$',dl.Cover, name='covertmpl'),
        
    url(r'^$',feeds.MainFeed(), name='main'),
]

