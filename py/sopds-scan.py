#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sopdsdb
import sopdscfg
import sopdsparse

##########################################################################
# Считываем параметры командной строки
# пример возможных параметров
# sopds-scan.py <--scanfull | --scanlast | --scan | -s> [ [-c <configfile>]
#
# -s, --scan, --scanfull  - Полное пересканирование всех файлов библиотеки
# --scanlast              - Обрабатываются только файлы с датой поздней, чем дата последнего сканирования
# -v, --verbose           - Включить вывод отладочной информации
# -c <configfile>         - Указывается путь к файлу конфигурации

from optparse import OptionParser
from sys import argv

parser=OptionParser(conflict_handler="resolve", version="sopds-scan.py. Version 0.01a", add_help_option=True, usage='sopds-scan.py [options]', description='sopds-scan.py: Simple OPDS Scanner - programm for scan your books directory and store data to MYSQL database.')
parser.add_option('-s','--scan','--scanfull', action='store_true', dest='scanfull', default=True, help='Full rescan all stored files.')
parser.add_option('-l','--scanlast', action='store_false', dest='scanfull', default=True, help='Scan files from date after last scan.')
parser.add_option('-v','--verbose', action='store_true', dest='verbose', default=False, help='Enable verbose output')
(options,arguments)=parser.parse_args()

SCAN_FULL=options.scanfull
VERBOSE=options.verbose

if VERBOSE:
        print('Options set: scanfull =',SCAN_FULL,', verbose =',VERBOSE,', configfile =',sopdscfg.CFG_PATH)
        print('Config file read: DB_NAME =',sopdscfg.DB_NAME,', DB_USER =',sopdscfg.DB_USER,', DB_PASS =',sopdscfg.DB_PASS,', DB_HOST =',sopdscfg.DB_HOST,', ROOT_LIB =',sopdscfg.ROOT_LIB,', FORMATS =',sopdscfg.FORMATS,', DUBLICATES =',sopdscfg.DUBLICATES,', MAXITEMS=',sopdscfg.MAXITEMS)



###########################################################################
# Основной код программы
#

opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST,sopdscfg.ROOT_LIB)
opdsdb.openDB()
opdsdb.printDBerr()
fb2=sopdsparse.fb2parser()

extensions_set={x for x in sopdscfg.EXT_LIST}
if VERBOSE:
   print(extensions_set)


for full_path, dirs, files in os.walk(sopdscfg.ROOT_LIB):
  for name in files:
    (n,e)=os.path.splitext(name)
    if e.lower() in extensions_set:
       rel_path=os.path.relpath(full_path,sopdscfg.ROOT_LIB)

       if VERBOSE:
          print("Attempt to add book: ",rel_path," - ",name,"...",end=" ")

       if opdsdb.findbook(name,rel_path)==0:
          cat_id=opdsdb.addcattree(rel_path)
          title=''
          genre=''
          lang=''
          if e.lower()=='.fb2' and sopdscfg.FB2PARSE:
             f=open(os.path.join(full_path,name),'rb')
             fb2.parse(f)
             f.close()
             if len(fb2.genre.getvalue())>0:
                genre=fb2.genre.getvalue()[0].strip(' \'\"')
             if len(fb2.lang.getvalue())>0:
                lang=fb2.lang.getvalue()[0].strip(' \'\"')
             if len(fb2.book_title.getvalue())>0:
                title=fb2.book_title.getvalue()[0].strip(' \'\"')
             if VERBOSE:
                if fb2.parse_error!=0:
                   print('with fb2 parse warning...',end=" ")

          book_id=opdsdb.addbook(name,rel_path,cat_id,e,title,genre,lang)
          if VERBOSE:
             print("Added ok.")

          idx=0
          for l in fb2.author_last.getvalue():
              last_name=l.strip(' \'\"')
              first_name=fb2.author_first.getvalue()[idx].strip(' \'\"')
              author_id=opdsdb.addauthor(first_name,last_name)
              opdsdb.addbauthor(book_id,author_id)
              idx+=1
       else:
          if VERBOSE:
             print("Already in DB.")


opdsdb.closeDB()
