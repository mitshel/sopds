#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
from urllib import parse
from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIRequestHandler
import sopdscli
import sopdscfg
import zipf

sopds = None
cfg   = None

#class opdsHandler(WSGIRequestHandler):
#      def get_stderr(self):
#          se = open(cfg.HTTPD_LOGFILE, 'a+')
#          return se.fileno()

def authorized_user(auth_list, auth_data):
    user=None
    alist=auth_list.split()
    for ainfo in alist:
        acode='Basic %s'%base64.encodestring(ainfo.strip().encode()).decode().strip()
        if acode==auth_data.strip():
           (user,pw)=ainfo.split(':')
    return user
        
def app(environ, start_response):
   sopds.resetParams()
   user=None
   if 'HTTP_AUTHORIZATION' in environ:
      adata=environ['HTTP_AUTHORIZATION']
      user=authorized_user(cfg.ACCOUNTS,adata)

   if (user!=None) or not cfg.AUTH:
      qs   = None
      if 'QUERY_STRING' in environ:
         qs = parse.parse_qs(environ['QUERY_STRING'])
      sopds.resetParams()
      sopds.parseParams(qs)
      sopds.setUser(user)
      sopds.make_response()
   else:
       sopds.set_response_status('401 Unauthorized')
       sopds.add_response_header([('WWW-Authenticate', 'Basic realm=\"%s\"'%cfg.SITE_TITLE)])
       sopds.add_response_header([('Content-type', 'text/html')])

   start_response(sopds.response_status, sopds.response_headers)
   return sopds.response_body

def start_server(config):
    global sopds
    global cfg

    cfg=config
    zipf.ZIP_CODEPAGE=cfg.ZIP_CODEPAGE
    sopds = sopdscli.opdsClient(cfg,sopdscli.modeINT)

    try:
       httpd = make_server(cfg.BIND_ADDRESS, cfg.PORT, app)
       print('Started Simple OPDS server on port ' , cfg.PORT)
       httpd.serve_forever()
    except KeyboardInterrupt:
       print('^C received, shutting down the web server')
       httpd.socket.close()


if __name__ == "__main__":
    config=sopdscfg.cfgreader()
    start_server(config)
