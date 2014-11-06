#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sopdscfg
import sopdscli
import os
import zipf

if (__name__=="__main__"):
   cfg=sopdscfg.cfgreader()
   zipf.ZIP_CODEPAGE=cfg.ZIP_CODEPAGE

   user = None
   if 'REMOTE_USER' in os.environ:
      user = os.environ['REMOTE_USER']

   sopds = sopdscli.opdsClient(cfg)
   sopds.resetParams()
   sopds.parseParams(os.environ)
   sopds.setUser(user)
   sopds.make_response()
   sopds.write_response_headers()
   sopds.write_response()

