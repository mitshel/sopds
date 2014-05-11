#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sopdscfg
import sopdscli
import os
import zipf
from urllib import parse

if (__name__=="__main__"):
   cfg=sopdscfg.cfgreader()
   zipf.ZIP_CODEPAGE=cfg.ZIP_CODEPAGE

   user = None
   qs   = None
   if 'REMOTE_USER' in os.environ:
      user = os.environ['REMOTE_USER']
   if 'QUERY_STRING' in os.environ:
      qs = parse.parse_qs(os.environ['QUERY_STRING'])

   sopds = sopdscli.opdsClient(cfg)
   sopds.resetParams()
   sopds.parseParams(qs)
   sopds.setUser(user)
   sopds.make_response()
   sopds.write_response_headers()
   sopds.write_response()

