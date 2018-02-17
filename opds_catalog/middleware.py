import base64
from django.http import HttpResponse
from django.contrib import auth
from django.utils import translation
from django.middleware.cache import FetchFromCacheMiddleware as DjangoFetchFromCacheMiddleware
from django.utils.deprecation import MiddlewareMixin

from constance import config


class BasicAuthMiddleware(object):
    header = "HTTP_AUTHORIZATION"

    def unauthed(self):
        response = HttpResponse("""<html><title>Auth required</title><body>
                                <h1>Authorization Required</h1></body></html>""", content_type="text/html")
        response['WWW-Authenticate'] = 'Basic realm="OPDS"'
        response.status_code = 401
        return response

    def process_request(self,request):
        if not config.SOPDS_AUTH:
            return
            
        # AuthenticationMiddleware is required so that request.user exists.
        #if not hasattr(request, 'user'):
        #    raise ImproperlyConfigured(
        #        "The Django remote user auth middleware requires the"
        #        " authentication middleware to be installed.  Edit your"
        #        " MIDDLEWARE setting to insert"
        #        " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
        #        " before the BasicAuthMiddleware class.")
        try:
            authentication = request.META[self.header]
        except KeyError:
            return self.unauthed()  
                    
        (auth_meth, auth_data) = authentication.split(' ',1)
        if 'basic' != auth_meth.lower():
            return self.unauthed()
        auth_data = base64.b64decode(auth_data.strip()).decode('utf-8')
        username, password = auth_data.split(':',1)            

        user = auth.authenticate(username=username, password=password)
        if user and user.is_active:
            request.user = user
            auth.login(request, user)
            return None

        return self.unauthed()


class SOPDSLocaleMiddleware(MiddlewareMixin):

    def process_request(self, request):
            request.LANG = config.SOPDS_LANGUAGE
            translation.activate(request.LANG)
            request.LANGUAGE_CODE = request.LANG

class FetchFromCacheMiddleware(DjangoFetchFromCacheMiddleware):

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        else:
            return super(FetchFromCacheMiddleware, self).process_request(request)