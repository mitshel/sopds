#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

    scanner=opdsScanner(cfg,VERBOSE)
    scanner.log_options()
    scanner.scan_all()
    scanner.log_stats()

