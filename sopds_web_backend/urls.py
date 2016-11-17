
from django.conf.urls import url
from sopds_web_backend import views

urlpatterns = [
    url(r'^search/books/',views.SearchBooksView, name='searchbooks'),
    url(r'^search/authors/',views.SearchAuthorsView, name='searchauthors'),                        
    url(r'^search/series/',views.SelectSeriesView, name='searchseries'),       
    url(r'^catalog/',views.CatalogsView, name='catalog'),  
    url(r'^book/',views.BooksView, name='book'), 
    url(r'^author/',views.AuthorsView, name='author'), 
    url(r'^genre/',views.GenresView, name='genre'),        
    url(r'^series/',views.SeriesView, name='series'),   
    url(r'^login/',views.LoginView, name='login'),    
    url(r'^logout/',views.LoginView, name='logout'),   
    url(r'^',views.hello, name='main'),         
]
