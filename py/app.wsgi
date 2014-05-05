import sys
from urllib import parse

def app(environ, start_response):
    " ... "
    message1 = "You use Python %s" % sys.version[:3]
    d = parse.parse_qs(environ['QUERY_STRING'])
    if 'id' in d:
        id = d.get('id')[0]
    else:
        id = 'Bad request'
    start_response("200 OK", [("Content-Type", "text/html")])
    return [message1.encode(), id.encode()]

application = app
