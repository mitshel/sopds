#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sopdscfg
from sopdscan import opdsScanner
from optparse import OptionParser
from sys import argv

if (__name__=="__main__"):
    parser=OptionParser(conflict_handler="resolve", version="sopds-scan.py. Version "+sopdscfg.VERSION, add_help_option=True, usage='sopds-scan.py [options]',description='sopds-scan.py: Simple OPDS Scanner - programm for scan your e-books directory and store data to MYSQL database.')
    parser.add_option('-v','--verbose', action='store_true', dest='verbose', default=False, help='Enable verbose output')
    parser.add_option('-c','--config',dest='configfile',default='',help='Config file pargh')
    (options,arguments)=parser.parse_args()
    VERBOSE=options.verbose
    CFG_FILE=options.configfile

    if CFG_FILE=='': cfg=sopdscfg.cfgreader()
    else: cfg=sopdscfg.cfgreader(CFG_FILE)

    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    formatter=logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')

    if cfg.LOGLEVEL!=logging.NOTSET:
       # Создаем обработчик для записи логов в файл
       fh = logging.FileHandler(cfg.LOGFILE)
       fh.setLevel(cfg.LOGLEVEL)
       fh.setFormatter(formatter)
       logger.addHandler(fh)

    if VERBOSE:
       # Создадим обработчик для вывода логов на экран с максимальным уровнем вывода
       ch = logging.StreamHandler()
       ch.setLevel(logging.DEBUG)
       ch.setFormatter(formatter)
       logger.addHandler(ch)

    scanner=opdsScanner(cfg,logger)
    scanner.scan_all()

