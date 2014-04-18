#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sopdsdb
import sopdsparse
import time
import datetime
import sopdscfg
import base64
import zipf
import logging
from optparse import OptionParser
from sys import argv

#############################################################################
#
# Вспомогательные функции
#
def create_cover(book_id,fb2,opdsdb):
    ictype=fb2.cover_image.getattr('content-type')
    coverid=fb2.cover_image.getattr('id')
    fn=''
    if ictype==None:
       ictype=''
    else:
       ictype=ictype.lower()
       if ictype=='image/jpeg' or ictype=='image/jpg':
          fn=str(book_id)+'.jpg'
       else:
          if ictype=='image/png':
             fn=str(book_id)+'.png'
          else:
             if coverid!=None:
                (f,e)=os.path.splitext(coverid)
             else: 
                e='.img'
             fn=str(book_id)+e
         
       fp=os.path.join(sopdscfg.COVER_PATH,fn)
       if len(fb2.cover_image.cover_data)>0:
          img=open(fp,'wb')
          s=fb2.cover_image.cover_data
          dstr=base64.b64decode(s)
          img.write(dstr)
          img.close()
    opdsdb.addcover(book_id,fn,ictype)

def processfile(db,fb2,name,full_path,file,archive=0,file_size=0,cat_id=0):
    global books_added
    global books_skipped
    global books_in_archives

    (n,e)=os.path.splitext(name)
    if e.lower() in extensions_set:
       rel_path=os.path.relpath(full_path,cfg.ROOT_LIB)

       logging.debug("Attempt to add book "+rel_path+"/"+name)

       fb2.reset()
       if db.findbook(name,rel_path,1)==0:
          if archive==0:
             cat_id=db.addcattree(rel_path,archive)
          title=''
          lang=''
          annotation=''
          docdate=''

          if e.lower()=='.fb2' and cfg.FB2PARSE:
             if isinstance(file, str):
                f=open(file,'rb')
             else:
                f=file
             fb2.parse(f,cfg.FB2HSIZE)
             f.close()

             if len(fb2.lang.getvalue())>0:
                lang=fb2.lang.getvalue()[0].strip(' \'\"')
             if len(fb2.book_title.getvalue())>0:
                title=fb2.book_title.getvalue()[0].strip(' \'\"\&-.#\\\`')
             if len(fb2.annotation.getvalue())>0:
                annotation=('\n'.join(fb2.annotation.getvalue()))[:10000]
             if len(fb2.docdate.getvalue())>0:
                docdate=fb2.docdate.getvalue()[0].strip();
             
             if fb2.parse_error!=0:
                logging.warning(rel_path+' - '+name+' fb2 parse warning ['+fb2.parse_errormsg+']')

          if title=='':
             title=n

          book_id=opdsdb.addbook(name,rel_path,cat_id,e,title,annotation,docdate,lang,file_size,archive,cfg.DUBLICATES_FIND)
          books_added+=1
          
          if e.lower()=='.fb2' and cfg.FB2PARSE and cfg.COVER_EXTRACT:
             try:
               create_cover(book_id,fb2,opdsdb)
             except:
               logging.error('Error extract cover from file '+name) 
          
          if archive==1:
             books_in_archives+=1
          logging.debug('Added ok.')

          idx=0
          for l in fb2.author_last.getvalue():
              last_name=l.strip(' \'\"\&-.#\\\`')
              first_name=fb2.author_first.getvalue()[idx].strip(' \'\"\&-.#\\\`')
              author_id=opdsdb.addauthor(first_name,last_name)
              opdsdb.addbauthor(book_id,author_id)
              idx+=1

          for l in fb2.genre.getvalue():
              opdsdb.addbgenre(book_id,opdsdb.addgenre(l.lower().strip(' \'\"')))

          for l in fb2.series.getattrs('name'):
              opdsdb.addbseries(book_id,opdsdb.addseries(l.strip()))

          if not cfg.SINGLE_COMMIT: opdsdb.commit()

       else:
          books_skipped+=1
          logging.debug('Already in DB.')

def processzip(db,fb2,name,full_path,file):
    global arch_scanned
    global arch_skipped
    global bad_archives

    rel_file=os.path.relpath(file,cfg.ROOT_LIB)
    if cfg.ZIPRESCAN or db.zipisscanned(rel_file,1)==0:
       cat_id=db.addcattree(rel_file,1)
       try:
          z = zipf.ZipFile(file, 'r', allowZip64=True)
          filelist = z.namelist()
          for n in filelist:
              try:
                  logging.debug('Start process ZIP file = '+file+' book file = '+n)
                  file_size=z.getinfo(n).file_size
                  processfile(db,fb2,n,file,z.open(n),1,file_size,cat_id=cat_id)
              except:
                  logging.error('Error processing ZIP file = '+file+' book file = '+n)
          z.close()
          arch_scanned+=1
       except:
          logging.error('Error while read ZIP archive. File '+file+' corrupt.')
          bad_archives+=1
    else:
       arch_skipped+=1
       logging.debug('Skip ZIP archive '+rel_file+'. Already scanned.')

#############################################################################
# Инициализируем переменные для сбора статистики
#
t1=datetime.timedelta(seconds=time.time())
books_added   = 0
books_skipped = 0
books_deleted = 0
arch_scanned = 0
arch_skipped = 0
bad_archives = 0
books_in_archives = 0

###########################################################################
# Разбираем опции командной строки и конфиг файла
#
parser=OptionParser(conflict_handler="resolve", version="sopds-scan.py. Version "+sopdscfg.VERSION, add_help_option=True, usage='sopds-scan.py [options]', description='sopds-scan.py: Simple OPDS Scanner - programm for scan your e-books directory and store data to MYSQL database.')
parser.add_option('-v','--verbose', action='store_true', dest='verbose', default=False, help='Enable verbose output')
parser.add_option('-c','--config',dest='configfile',default='',help='Config file pargh')
(options,arguments)=parser.parse_args()
VERBOSE=options.verbose
CFG_FILE=options.configfile

if CFG_FILE=='': cfg=sopdscfg.cfgreader()
else: cfg=sopdscfg.cfgreader(CFG_FILE)

zipf.ZIP_CODEPAGE=cfg.ZIP_CODEPAGE


###########################################################################
# Инициализруем logger
#
if cfg.LOGLEVEL!=logging.NOTSET:
    # Создаем обработчик для записи логов в файл
    fh = logging.FileHandler(cfg.LOGFILE)
    fh.setLevel(cfg.LOGLEVEL)

if VERBOSE:
   # Создадим обработчик для вывода логов на экран с максимальным уровнем вывода
   ch = logging.StreamHandler()
   ch.setLevel(logging.DEBUG)

logformat='%(asctime)s %(levelname)-8s %(message)s'
if VERBOSE:
   logging.basicConfig(format = logformat, level = logging.DEBUG, handlers=(fh,ch))
else:
   logging.basicConfig(format = logformat, level = logging.INFO, handlers=(fh,))

logging.info(' ***** Starting sopds-scan...')
logging.debug('OPTIONS SET')
if cfg.CONFIGFILE!=None:     logging.debug('configfile = '+cfg.CONFIGFILE)
if cfg.ROOT_LIB!=None:       logging.debug('root_lib = '+cfg.ROOT_LIB)
if cfg.FB2TOEPUB_PATH!=None: logging.debug('fb2toepub = '+cfg.FB2TOEPUB_PATH)
if cfg.FB2TOMOBI_PATH!=None: logging.debug('fb2tomobi = '+cfg.FB2TOMOBI_PATH)
if cfg.TEMP_DIR!=None:       logging.debug('temp_dir = '+cfg.TEMP_DIR)

###########################################################################
# Основной код программы
#
opdsdb=sopdsdb.opdsDatabase(cfg.DB_NAME,cfg.DB_USER,cfg.DB_PASS,cfg.DB_HOST,cfg.ROOT_LIB)
opdsdb.openDB()
opdsdb.avail_check_prepare()

if cfg.COVER_EXTRACT:
   if not os.path.isdir(sopdscfg.COVER_PATH):
      os.mkdir(sopdscfg.COVER_PATH)

fb2parser=sopdsparse.fb2parser(cfg.COVER_EXTRACT)

extensions_set={x for x in cfg.EXT_LIST}

for full_path, dirs, files in os.walk(cfg.ROOT_LIB):
  for name in files:
    file=os.path.join(full_path,name)
    (n,e)=os.path.splitext(name)
    if (e.lower() == '.zip'):
       if cfg.ZIPSCAN:
          processzip(opdsdb,fb2parser,name,full_path,file)
    else:
       file_size=os.path.getsize(file)
       processfile(opdsdb,fb2parser,name,full_path,file,0,file_size)

opdsdb.commit()
if cfg.DELETE_LOGICAL:
   books_deleted=opdsdb.books_del_logical()
else:
   books_deleted=opdsdb.books_del_phisical()
opdsdb.update_double()
opdsdb.closeDB()


###########################################################################
# Вывод статистической информации по окончании программы сканирования
#
t2=datetime.timedelta(seconds=time.time())
logging.info('Books added      : '+str(books_added))
logging.info('Books skipped    : '+str(books_skipped))
if cfg.DELETE_LOGICAL:
   logging.info('Books deleted    : '+str(books_deleted))
else:
   logging.info('Books DB entries deleted : '+str(books_deleted))
logging.info('Books in archives: '+str(books_in_archives))
logging.info('Archives scanned : '+str(arch_scanned))
logging.info('Archives skipped : '+str(arch_skipped))
logging.info('Bad archives     : '+str(bad_archives))

t=t2-t1
seconds=t.seconds%60
minutes=((t.seconds-seconds)//60)%60
hours=t.seconds//3600
logging.info('Time estimated:'+str(hours)+' hours, '+str(minutes)+' minutes, '+str(seconds)+' seconds.')

