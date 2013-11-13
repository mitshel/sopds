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

###########################################################################
# Считываем конфигурацию из конфигурационного файла
# используем модуль configparser

import configparser
config=configparser.ConfigParser()
#config.read(CFG_PATH)
config.readfp(codecs.open(CFG_PATH,"r","utf-8"))

CFG_S_GLOBAL='global'
NAME=config.get(CFG_S_GLOBAL,'name')
ROOT_URL=config.get(CFG_S_GLOBAL,'root_url')
DB_NAME=config.get(CFG_S_GLOBAL,'db_name')
DB_USER=config.get(CFG_S_GLOBAL,'db_user')
DB_PASS=config.get(CFG_S_GLOBAL,'db_pass')
DB_HOST=config.get(CFG_S_GLOBAL,'db_host')
DB_CHARSET=config.get(CFG_S_GLOBAL,'db_charset')
ROOT_LIB=os.path.abspath(config.get(CFG_S_GLOBAL,'root_lib'))
FORMATS=config.get(CFG_S_GLOBAL,'formats')
DUBLICATES=config.getboolean(CFG_S_GLOBAL,'dublicates')
FB2PARSE=config.getboolean(CFG_S_GLOBAL,'fb2parse')
ZIPSCAN=config.getboolean(CFG_S_GLOBAL,'zipscan')
ZIPRESCAN=config.getboolean(CFG_S_GLOBAL,'ziprescan')
fb2hsize=config.get(CFG_S_GLOBAL,'fb2hsize')
maxitems=config.get(CFG_S_GLOBAL,'maxitems')
splitauthors=config.get(CFG_S_GLOBAL,'splitauthors')
if maxitems.isdigit():
   MAXITEMS=int(maxitems)
else:
   MAXITEMS=50
if fb2hsize.isdigit():
   FB2HSIZE=int(fb2hsize)
else:
   FB2HSIZE=0
if splitauthors.isdigit():
   SPLITAUTHORS=int(splitauthors)
else:
   SPLITAUTHORS=0

EXT_LIST=FORMATS.lower().split()

CFG_S_SITE='site'
SITE_ID=config.get(CFG_S_SITE,'id')
SITE_TITLE=config.get(CFG_S_SITE,'title')
SITE_ICON=config.get(CFG_S_SITE,'icon')
SITE_AUTOR=config.get(CFG_S_SITE,'autor')
SITE_URL=config.get(CFG_S_SITE,'url')
SITE_EMAIL=config.get(CFG_S_SITE,'email')
SITE_MAINTITLE=config.get(CFG_S_SITE,'main_title')

