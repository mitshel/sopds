
from django.conf.urls import url
from sopds_web_backend import views

app_name='opds_web_backend'

urlpatterns = [
    url(r'^search/books/$',views.SearchBooksView, name='searchbooks'),
    url(r'^search/authors/$',views.SearchAuthorsView, name='searchauthors'),
    url(r'^search/series/$',views.SearchSeriesView, name='searchseries'),
    url(r'^catalog/$',views.CatalogsView, name='catalog'),
    url(r'^book/$',views.BooksView, name='book'),
    url(r'^author/$',views.AuthorsView, name='author'),
    url(r'^genre/$',views.GenresView, name='genre'),
    url(r'^series/$',views.SeriesView, name='series'),
    url(r'^login/$',views.LoginView, name='login'),
    url(r'^logout/$',views.LogoutView, name='logout'),
    url(r'^bs/delete/$',views.BSDelView, name='bsdel'),
    url(r'^bs/clear/$', views.BSClearView, name='bsclear'),
    url(r'^$',views.hello, name='main'),
]

#handler403 = 'views.handler403'
