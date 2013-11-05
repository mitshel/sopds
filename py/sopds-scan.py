#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sopdsdb
import sopdscfg

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

opdsdb=sopdsdb.opdsDatabase(sopdscfg.DB_NAME,sopdscfg.DB_USER,sopdscfg.DB_PASS,sopdscfg.DB_HOST)
opdsdb.openDB()
opdsdb.printDBerr()

extensions_set={x for x in sopdscfg.EXT_LIST}
if VERBOSE:
   print(extensions_set)

for full_path, dirs, files in os.walk(sopdscfg.ROOT_LIB):
  for name in files:
    (n,e)=os.path.splitext(name)
    if e.lower() in extensions_set:
       head=full_path
       cat_id=opdsdb.addcattree(full_path, sopdscfg.ROOT_LIB)
       book_id=opdsdb.addbook(name,full_path,cat_id,e)
       if VERBOSE:
          print("Added book: ",full_path," - ",name)

opdsdb.closeDB()

