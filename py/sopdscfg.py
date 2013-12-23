# -*- coding: utf-8 -*-

import os
import sys
import codecs

##########################################################################
# Глобальные переменные
#
PY_PATH=os.path.dirname(os.path.abspath(__file__))
(ROOT_PATH,tmp)=os.path.split(PY_PATH)
CFG_FILENAME='sopds.conf'
CFG_PATH_DEFAULT=ROOT_PATH+os.path.sep+'conf'+os.path.sep+CFG_FILENAME
CFG_PATH=CFG_PATH_DEFAULT
COVER_PATH=os.path.join(ROOT_PATH,'covers')

###########################################################################
# Считываем конфигурацию из конфигурационного файла
# используем модуль configparser
import configparser

class cfgreader:
   def __init__(self,configfile=CFG_PATH):
       config=configparser.ConfigParser()
       #config.read(CFG_PATH)
       self.CONFIGFILE=configfile
       config.readfp(codecs.open(self.CONFIGFILE,"r","utf-8"))

       CFG_S_GLOBAL='global'
       self.NAME=config.get(CFG_S_GLOBAL,'name')
       self.ROOT_URL=config.get(CFG_S_GLOBAL,'root_url')
       self.DB_NAME=config.get(CFG_S_GLOBAL,'db_name')
       self.DB_USER=config.get(CFG_S_GLOBAL,'db_user')
       self.DB_PASS=config.get(CFG_S_GLOBAL,'db_pass')
       self.DB_HOST=config.get(CFG_S_GLOBAL,'db_host')
       self.DB_CHARSET=config.get(CFG_S_GLOBAL,'db_charset')
       self.ROOT_LIB=os.path.abspath(config.get(CFG_S_GLOBAL,'root_lib'))
       self.FORMATS=config.get(CFG_S_GLOBAL,'formats')
       self.DUBLICATES=config.getboolean(CFG_S_GLOBAL,'dublicates')
       self.FB2PARSE=config.getboolean(CFG_S_GLOBAL,'fb2parse')
       self.ZIPSCAN=config.getboolean(CFG_S_GLOBAL,'zipscan')
       self.ZIPRESCAN=config.getboolean(CFG_S_GLOBAL,'ziprescan')
       self.COVER_ENABLE=config.getboolean(CFG_S_GLOBAL,'cover_enable')
       fb2hsize=config.get(CFG_S_GLOBAL,'fb2hsize')
       maxitems=config.get(CFG_S_GLOBAL,'maxitems')
       splitauthors=config.get(CFG_S_GLOBAL,'splitauthors')

       if maxitems.isdigit():
          self.MAXITEMS=int(maxitems)
       else:
          self.MAXITEMS=50

       if fb2hsize.isdigit():
          self.FB2HSIZE=int(fb2hsize)
       else:
          self.FB2HSIZE=0

       if self.COVER_ENABLE:
          self.FB2SIZE=0

       if splitauthors.isdigit():
          self.SPLITAUTHORS=int(splitauthors)
       else:
          self.SPLITAUTHORS=0

       self.EXT_LIST=self.FORMATS.lower().split()

       CFG_S_SITE='site'
       self.SITE_ID=config.get(CFG_S_SITE,'id')
       self.SITE_TITLE=config.get(CFG_S_SITE,'title')
       self.SITE_ICON=config.get(CFG_S_SITE,'icon')
       self.SITE_AUTOR=config.get(CFG_S_SITE,'autor')
       self.SITE_URL=config.get(CFG_S_SITE,'url')
       self.SITE_EMAIL=config.get(CFG_S_SITE,'email')
       self.SITE_MAINTITLE=config.get(CFG_S_SITE,'main_title')

