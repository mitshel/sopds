# -*- coding: utf-8 -*-

import os
import sys
import codecs
import logging

##########################################################################
# Глобальные переменные
#
VERSION="0.18"
PY_PATH=os.path.dirname(os.path.abspath(__file__))
(ROOT_PATH,tmp)=os.path.split(PY_PATH)
CFG_FILENAME='sopds.conf'
CFG_PATH_DEFAULT=ROOT_PATH+os.path.sep+'conf'+os.path.sep+CFG_FILENAME
CFG_PATH=CFG_PATH_DEFAULT
COVER_PATH=os.path.join(ROOT_PATH,'covers')
NOCOVER_IMG='nocover.jpg'
LOG_PATH=os.path.join(ROOT_PATH,'logs')

loglevels={'debug':logging.DEBUG,'info':logging.INFO,'warning':logging.WARNING,'error':logging.ERROR,'critical':logging.CRITICAL,'none':logging.NOTSET}

###########################################################################
# Считываем конфигурацию из конфигурационного файла
# используем модуль configparser
import configparser

class ConfigParser_new(configparser.ConfigParser):

   def getdefault(self,section,value,default_value):
     try:
       result=self.get(section,value)
     except:
       result=default_value
     return result

   def getdefault_bool(self,section,value,default_value):
     try:
       result=self.getboolean(section,value)
     except:
       result=default_value
     return result

   def getdefault_int(self,section,value,default_value):
     try:
       strval=self.get(section,value)
       if strval.isdigit(): result=int(strval)
       else: result=default_value
     except:
       result=default_value
     return result



class cfgreader:
   def __init__(self,configfile=CFG_PATH):
       self.CONFIGFILE=configfile
       self.parse()

   def parse(self):
       config=ConfigParser_new()
       config.readfp(codecs.open(self.CONFIGFILE,"r","utf-8"))
       CFG_S_GLOBAL='global'

       self.CGI_PATH=config.getdefault(CFG_S_GLOBAL,'cgi_path','sopds.cgi')
       self.CGI_PATH=os.path.normpath(self.CGI_PATH)
       self.SEARCHXML_PATH=os.path.join(os.path.dirname(self.CGI_PATH),'opds-opensearch.xml')

       self.COVER_PATH=config.getdefault(CFG_S_GLOBAL,'cover_path','../covers')
       self.COVER_PATH=os.path.normpath(self.COVER_PATH)

       self.FB2TOEPUB_PATH=config.getdefault(CFG_S_GLOBAL,'fb2toepub',None)
       self.FB2TOEPUB=self.FB2TOEPUB_PATH!=None and os.path.isfile(self.FB2TOEPUB_PATH)

       self.FB2TOMOBI_PATH=config.getdefault(CFG_S_GLOBAL,'fb2tomobi',None)
       self.FB2TOMOBI=self.FB2TOMOBI_PATH!=None and os.path.isfile(self.FB2TOMOBI_PATH)

       self.TEMP_DIR=config.getdefault(CFG_S_GLOBAL,'temp_dir','/tmp')
       self.TEMP_DIR=os.path.normpath(self.TEMP_DIR)
       
       logfile=config.getdefault(CFG_S_GLOBAL,'logfile','sopds.log')
       self.LOGFILE=os.path.join(LOG_PATH,logfile)
       loglevel=config.getdefault(CFG_S_GLOBAL,'loglevel','info')
       if loglevel.lower() in loglevels:
           self.LOGLEVEL=loglevels[loglevel.lower()]
       else:
           self.LOGLEVEL=logging.NOTSET
   
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
       self.ZIPFILE_PATCH=config.getdefault_bool(CFG_S_GLOBAL,'zipfile_patch',False)
       self.SINGLE_COMMIT=config.getdefault_bool(CFG_S_GLOBAL,'single_commit',False)
       self.TITLE_AS_FN=config.getdefault_bool(CFG_S_GLOBAL,'title_as_filename',False)
       self.ALPHA=config.getdefault_bool(CFG_S_GLOBAL,'alphabet_menu',True)
       self.FB2HSIZE=config.getdefault_int(CFG_S_GLOBAL,'fb2hsize',0)
       self.MAXITEMS=config.getdefault_int(CFG_S_GLOBAL,'maxitems',50)
       self.SPLITAUTHORS=config.getdefault_int(CFG_S_GLOBAL,'splitauthors',0)
       self.SPLITTITLES=config.getdefault_int(CFG_S_GLOBAL,'splittitles',0)       
       self.COVER_SHOW=config.getdefault_int(CFG_S_GLOBAL,'cover_show',0)
       self.NEW_PERIOD=config.getdefault_int(CFG_S_GLOBAL,'new_period',7)
       zip_codepage=config.getdefault(CFG_S_GLOBAL,'zip_codepage','cp866')
       self.BOOK_SHELF=config.getdefault_bool(CFG_S_GLOBAL,'book_shelf',True)

       if self.COVER_EXTRACT: self.FB2SIZE=0
       self.EXT_LIST=self.FORMATS.lower().split()

       if zip_codepage.lower() in {'cp437','cp866','cp1251','utf-8'}: self.ZIP_CODEPAGE=zip_codepage.lower()
       else: self.ZIP_CODEPAGE='cp437'

       CFG_S_SITE='site'
       self.SITE_ID=config.get(CFG_S_SITE,'id')
       self.SITE_TITLE=config.get(CFG_S_SITE,'title')
       self.SITE_ICON=config.get(CFG_S_SITE,'icon')
       self.SITE_AUTOR=config.get(CFG_S_SITE,'autor')
       self.SITE_URL=config.get(CFG_S_SITE,'url')
       self.SITE_EMAIL=config.get(CFG_S_SITE,'email')
       self.SITE_MAINTITLE=config.get(CFG_S_SITE,'main_title')

       CFG_S_DAEMON='daemon'
       self.SCAN_ON_START=config.getdefault_bool(CFG_S_DAEMON,'scan_on_start',True)
       self.PID_FILE=config.getdefault(CFG_S_DAEMON,'pid_file',r'/tmp/sopds.pid')
       self.DAY_OF_WEEK=config.getdefault_int(CFG_S_DAEMON,'scan_day_of_week',0)
       self.SCAN_INTERVAL=config.getdefault_int(CFG_S_DAEMON,'scan_interval',0)
       self.SCAN_TIME=config.getdefault(CFG_S_DAEMON,'scan_time','00:00')
       try:
          (scan_hour,scan_min)=self.SCAN_TIME.split(':')
          scan_hour=scan_hour.strip()
          scan_min=scan_min.strip()
          if scan_hour.isdigit():
             self.SCAN_HOUR=int(scan_hour)
          else:
             self.SCAN_HOUR=0
          if scan_min.isdigit():
             self.SCAN_MIN=int(scan_min)
          else:
             self.SCAN_MIN=0
       except:
          (self.SCAN_HOUR,self.SCAN_MIN)=(0,0)
       if self.SCAN_INTERVAL>0:
          self.SCAN_TIMES=list(range(self.SCAN_HOUR*60+self.SCAN_MIN,1440,self.SCAN_INTERVAL))
       else:
          self.SCAN_TIMES=[self.SCAN_HOUR*60+self.SCAN_MIN]
