#!/usr/bin/python3

from http.server import HTTPServer, BaseHTTPRequestHandler
import base64
import cgi

PORT_NUMBER = 8080
acct='user:pass'

class opdsHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTH(self):
        authcode='Basic %s'%base64.encodestring(acct.encode()).decode().strip()
        result=False
        if self.headers.get('Authorization') == None:
            self.do_AUTHHEAD()
#            self.wfile.write('no auth header received'.encode())
            pass
        elif self.headers.get('Authorization') == authcode:
            result=True
#            self.do_HEAD()
#            self.wfile.write(self.headers.get('Authorization').encode())
#            self.wfile.write('authenticated!'.encode())
            pass
        else:
            self.do_AUTHHEAD()
#            self.wfile.write(self.headers.get('Authorization').encode())
#            self.wfile.write('not authenticated'.encode())
            pass
        return result


    def do_GET(self):
        ''' Present frontpage with user authentication. '''
        if self.do_AUTH():
           self.do_HEAD()
           self.wfile.write('authenticated!'.encode())
        return
			
try:
    server_address = ('',PORT_NUMBER)
    server = HTTPServer(server_address, opdsHandler)
    print('Started httpserver on port ' , PORT_NUMBER)
	
    #Wait forever for incoming http requests
    server.serve_forever()

except KeyboardInterrupt:
    print('^C received, shutting down the web server')
    server.socket.close()
