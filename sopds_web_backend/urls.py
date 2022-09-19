
from django.urls import re_path
from sopds_web_backend import views

app_name = 'opds_web_backend'

urlpatterns = [
    re_path(r'^search/books/$',views.SearchBooksView, name='searchbooks'),
    re_path(r'^search/authors/$',views.SearchAuthorsView, name='searchauthors'),
    re_path(r'^search/series/$',views.SearchSeriesView, name='searchseries'),
    re_path(r'^catalog/$',views.CatalogsView, name='catalog'),
    re_path(r'^book/$',views.BooksView, name='book'),
    re_path(r'^book/read/(?P<book_id>[0-9]+)/$',views.BookReaderView, name='read'),
    re_path(r'^author/$',views.AuthorsView, name='author'),
    re_path(r'^genre/$',views.GenresView, name='genre'),
    re_path(r'^series/$',views.SeriesView, name='series'),
    re_path(r'^theme/$',views.ThemeView, name='theme'),
    re_path(r'^login/$',views.LoginView, name='login'),
    re_path(r'^logout/$',views.LogoutView, name='logout'),
    re_path(r'^bs/add/$',views.BSAddView, name='bsadd'),
    re_path(r'^bs/delete/$',views.BSDelView, name='bsdel'),
    re_path(r'^bs/clear/$', views.BSClearView, name='bsclear'),
    re_path(r'^bs/setpos/(?P<book_id>[0-9]+)/$', views.BSSetPos, name='setpos'),
    re_path(r'^bs/getpos/(?P<book_id>[0-9]+)/$', views.BSGetPos, name='getpos'),
    re_path(r'^$',views.hello, name='main'),
]

#handler403 = 'views.handler403'
