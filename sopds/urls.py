"""sopds URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import re_path, include
from django.contrib import admin
from django.views.generic import RedirectView
from django.urls import reverse_lazy

# from django.contrib.auth import logout

urlpatterns = [
    re_path(r'^opds/', include('opds_catalog.urls', namespace='opds')),
    re_path(r'^web/', include('sopds_web_backend.urls', namespace='web')),
    re_path(r'^admin/', admin.site.urls),
    #re_path(r'^logout/$', logout, {'next_page':'/web/'},name='logout'),
    #re_path(r'^', include('sopds_web_backend.urls', namespace='web', app_name='opds_web_backend')),
    re_path(r'^$', RedirectView.as_view(url=reverse_lazy("web:main"))),
]
