#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

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
   if 'REMOTE_USER' in environ:
      user = environ['REMOTE_USER']

   sopds.resetParams()
   sopds.parseParams(environ)
   sopds.setUser(user)
   sopds.make_response()
   start_response(sopds.get_response_status(), sopds.get_response_headers())
   return sopds.get_response_body()

application = app
