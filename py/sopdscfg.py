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
NOCOVER_IMG='nocover.jpg'

###########################################################################
# Считываем конфигурацию из конфигурационного файла
# используем модуль configparser
import configparser

class ConfigParser_new(configparser.ConfigParser):
   def get_default(self,section,value,default_value):
     try:
       result=self.get(section,value)
     except:
       result=default_value
     return result

   def getboolean_default(self,section,value,default_value):
     try:
       result=self.getboolean(section,value)
     except:
       result=default_value
     return result


class cfgreader:
   def __init__(self,configfile=CFG_PATH):
#       config=configparser.ConfigParser()
       config=ConfigParser_new()
       self.CONFIGFILE=configfile
       config.readfp(codecs.open(self.CONFIGFILE,"r","utf-8"))
       CFG_S_GLOBAL='global'

       self.CGI_PATH=config.get_default(CFG_S_GLOBAL,'cgi_path','sopds.cgi')
       self.CGI_PATH=os.path.normpath(self.CGI_PATH)

       self.COVER_PATH=config.get_default(CFG_S_GLOBAL,'cover_path','../covers')
       self.COVER_PATH=os.path.normpath(self.COVER_PATH)

       self.FB2TOEPUB_PATH=config.get_default(CFG_S_GLOBAL,'fb2toepub',None)
       self.FB2TOEPUB=self.FB2TOEPUB_PATH!=None and os.path.isfile(self.FB2TOEPUB_PATH)

       self.TEMP_DIR=config.get_default(CFG_S_GLOBAL,'temp_dir','/tmp')
       self.TEMP_DIR=os.path.normpath(self.TEMP_DIR)
   
       self.DB_NAME=config.get(CFG_S_GLOBAL,'db_name')
       self.DB_USER=config.get(CFG_S_GLOBAL,'db_user')
       self.DB_PASS=config.get(CFG_S_GLOBAL,'db_pass')
       self.DB_HOST=config.get(CFG_S_GLOBAL,'db_host')
       self.DB_CHARSET=config.get(CFG_S_GLOBAL,'db_charset')
       self.ROOT_LIB=os.path.abspath(config.get(CFG_S_GLOBAL,'root_lib'))
       self.FORMATS=config.get(CFG_S_GLOBAL,'formats')
       self.DUBLICATES_FIND=config.getboolean(CFG_S_GLOBAL,'dublicates_find')
       self.DUBLICATES_SHOW=config.getboolean(CFG_S_GLOBAL,'dublicates_show')
       self.FB2PARSE=config.getboolean(CFG_S_GLOBAL,'fb2parse')
       self.ZIPSCAN=config.getboolean(CFG_S_GLOBAL,'zipscan')
       self.ZIPRESCAN=config.getboolean(CFG_S_GLOBAL,'ziprescan')
       self.COVER_EXTRACT=config.getboolean(CFG_S_GLOBAL,'cover_extract')
       self.DELETE_LOGICAL=config.getboolean(CFG_S_GLOBAL,'delete_logical')
       self.ZIPFILE_PATCH=config.getboolean_default(CFG_S_GLOBAL,'zipfile_patch',False)
       fb2hsize=config.get(CFG_S_GLOBAL,'fb2hsize')
       maxitems=config.get(CFG_S_GLOBAL,'maxitems')
       splitauthors=config.get(CFG_S_GLOBAL,'splitauthors')
       splittitles=config.get(CFG_S_GLOBAL,'splittitles')
       cover_show=config.get(CFG_S_GLOBAL,'cover_show')
       zip_codepage=config.get_default(CFG_S_GLOBAL,'zip_codepage','cp866')

       if maxitems.isdigit():
          self.MAXITEMS=int(maxitems)
       else:
          self.MAXITEMS=50

       if fb2hsize.isdigit():
          self.FB2HSIZE=int(fb2hsize)
       else:
          self.FB2HSIZE=0

       if self.COVER_EXTRACT:
          self.FB2SIZE=0

       if splitauthors.isdigit():
          self.SPLITAUTHORS=int(splitauthors)
       else:
          self.SPLITAUTHORS=0

       if splittitles.isdigit():
          self.SPLITTITLES=int(splittitles)
       else:
          self.SPLITTITLES=0

       if cover_show.isdigit():
          self.COVER_SHOW=int(cover_show)
       else:
          self.COVER_SHOW=0

       self.EXT_LIST=self.FORMATS.lower().split()

       if zip_codepage.lower() in {'cp437','cp866','cp1251','utf-8'}:
          self.ZIP_CODEPAGE=zip_codepage.lower()
       else:
          self.ZIP_CODEPAGE='cp437'

       CFG_S_SITE='site'
       self.SITE_ID=config.get(CFG_S_SITE,'id')
       self.SITE_TITLE=config.get(CFG_S_SITE,'title')
       self.SITE_ICON=config.get(CFG_S_SITE,'icon')
       self.SITE_AUTOR=config.get(CFG_S_SITE,'autor')
       self.SITE_URL=config.get(CFG_S_SITE,'url')
       self.SITE_EMAIL=config.get(CFG_S_SITE,'email')
       self.SITE_MAINTITLE=config.get(CFG_S_SITE,'main_title')

