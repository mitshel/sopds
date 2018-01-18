from django.conf.urls import url
from sopds_web_backend import views

urlpatterns = [
    url(r'^search/books/$',views.SearchBooksView, name='searchbooks'),
    url(r'^search/authors/$',views.SearchAuthorsView, name='searchauthors'),
    url(r'^search/series/$',views.SearchSeriesView, name='searchseries'),
    url(r'^catalog/$',views.CatalogsView, name='catalog'),
    url(r'^book/$',views.BooksView, name='book'),
    url(r'^book/read/(?P<book_id>[0-9]+)/$',views.BookReaderView, name='read'),
    url(r'^author/$',views.AuthorsView, name='author'),
    url(r'^genre/$',views.GenresView, name='genre'),
    url(r'^series/$',views.SeriesView, name='series'),
    url(r'^login/$',views.LoginView, name='login'),
    url(r'^logout/$',views.LogoutView, name='logout'),
    url(r'^bs/delete/$',views.BSDelView, name='bsdel'),
    url(r'^bs/clear/$', views.BSClearView, name='bsclear'),
    url(r'^bs/setpos/(?P<book_id>[0-9]+)/$', views.BSSetPos, name='setpos'),
    url(r'^bs/getpos/(?P<book_id>[0-9]+)/$', views.BSGetPos, name='getpos'),
    url(r'^$',views.hello, name='main'),
]
