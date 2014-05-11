#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from urllib import parse

PY_PATH=os.path.dirname(os.path.abspath(__file__))
sys.path.append(PY_PATH)

import sopdscli
import sopdscfg
import zipf

cfg=sopdscfg.cfgreader()
zipf.ZIP_CODEPAGE=cfg.ZIP_CODEPAGE
sopds = sopdscli.opdsClient(cfg,sopdscli.modeWSGI)

def app(environ, start_response):
   user = None
   qs   = None
   if 'REMOTE_USER' in environ:
      user = environ['REMOTE_USER']
   if 'QUERY_STRING' in environ:
      qs = parse.parse_qs(environ['QUERY_STRING'])

   sopds.resetParams()
   sopds.parseParams(qs)
   sopds.setUser(user)
   sopds.make_response()
   start_response(sopds.response_status, sopds.response_headers)
   return sopds.response_body

application = app
