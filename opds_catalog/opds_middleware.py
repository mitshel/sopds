from django.http import HttpResponse
from opds_catalog import settings
from django.contrib import auth

class BasicAuthMiddleware(object):

    def unauthed(self):
        response = HttpResponse("""<html><title>Auth required</title><body>
                                <h1>Authorization Required</h1></body></html>""", content_type="text/html")
        response['WWW-Authenticate'] = 'Basic realm="OPDS"'
        response.status_code = 401
        return response

    def process_request(self,request):
        import base64

        if not settings.AUTH:
            return

        if not 'HTTP_AUTHORIZATION' in request.META:
            return self.unauthed()

        authentication = request.META['HTTP_AUTHORIZATION']
        (auth_meth, auth_data) = authentication.split(' ',1)
        if 'basic' != auth_meth.lower():
            return self.unauthed()
        auth_data = base64.b64decode(auth_data.strip()).decode('utf-8')
        username, password = auth_data.split(':',1)

        user = auth.authenticate(username=username, password=password)
#        if (user is not None) and user.is_active:
        if user:
            request.user = user
            auth.login(request, user)
            return

        return self.unauthed()
