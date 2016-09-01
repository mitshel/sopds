
from django.conf.urls import url
from sopds_web_backend import views

urlpatterns = [
    url(r'^',views.hello, name='main'),
]
