# -*- coding: utf-8 -*-

import os
import time
import datetime
import logging
import re

from django.db import transaction

from opds_catalog import fb2parse, opdsdb
from opds_catalog import inpx_parser
#from opds_catalog import settings
import opds_catalog.zipf as zipfile

from constance import config

class opdsScanner:
    def __init__(self, logger=None):
        self.fb2parser=None
        self.init_parser()
        self.strip_symbols = ' »«\'\"\&\n-.#\\\`'

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('')
            self.logger.setLevel(logging.CRITICAL)
        self.init_stats()

    def init_stats(self):
        self.t1=datetime.timedelta(seconds=time.time())
        self.t2=self.t1
        self.t3=self.t1
        self.books_added = 0
        self.books_skipped = 0
        self.books_deleted = 0
        self.arch_scanned = 0
        self.arch_skipped = 0
        self.bad_archives = 0
        self.bad_books = 0
        self.books_in_archives = 0

    def init_parser(self):
        self.fb2parser=fb2parse.fb2parser(False)

    def log_options(self):
        self.logger.info(' ***** Starting sopds-scan...')
        self.logger.debug('OPTIONS SET')
        if config.SOPDS_ROOT_LIB!=None:       self.logger.debug('root_lib = '+config.SOPDS_ROOT_LIB)
        if config.SOPDS_FB2TOEPUB!=None: self.logger.debug('fb2toepub = '+config.SOPDS_FB2TOEPUB)
        if config.SOPDS_FB2TOMOBI!=None: self.logger.debug('fb2tomobi = '+config.SOPDS_FB2TOMOBI)
        if config.SOPDS_TEMP_DIR!=None:       self.logger.debug('temp_dir = '+config.SOPDS_TEMP_DIR)

    def log_stats(self):
        self.t2=datetime.timedelta(seconds=time.time())
        self.logger.info('Books added      : '+str(self.books_added))
        self.logger.info('Books skipped    : '+str(self.books_skipped))
        self.logger.info('Bad books        : '+str(self.bad_books))
        if config.SOPDS_DELETE_LOGICAL:
            self.logger.info('Books deleted    : '+str(self.books_deleted))
        else:
            self.logger.info('Books DB entries deleted : '+str(self.books_deleted))
        self.logger.info('Books in archives: '+str(self.books_in_archives))
        self.logger.info('Archives scanned : '+str(self.arch_scanned))
        self.logger.info('Archives skipped : '+str(self.arch_skipped))
        self.logger.info('Bad archives     : '+str(self.bad_archives))

        t=self.t2-self.t1
        seconds=t.seconds%60
        minutes=((t.seconds-seconds)//60)%60
        hours=t.seconds//3600
        self.logger.info('Time estimated:'+str(hours)+' hours, '+str(minutes)+' minutes, '+str(seconds)+' seconds.')

    def scan_all(self):
        self.init_stats()
        self.log_options()
        self.inp_cat = None
        self.zip_file = None
        self.rel_path = None     
                    
        opdsdb.avail_check_prepare()
            
        for full_path, dirs, files in os.walk(config.SOPDS_ROOT_LIB, followlinks=True):
            # Если разрешена обработка inpx, то при нахождении inpx обрабатываем его и прекращаем обработку текущего каталога
            if config.SOPDS_INPX_ENABLE:
                inpx_files = [inpx for inpx in files if re.match('.*(.inpx|.INPX)$', inpx)]
                # Пропускаем обработку файлов в текущем каталоге, если найдены inpx
                if inpx_files:
                    for inpx_file in inpx_files:
                        file = os.path.join(full_path, inpx_file)
                        self.processinpx(inpx_file, full_path, file)                       
                    continue
                
            for name in files:
                file=os.path.join(full_path,name)
                (n,e)=os.path.splitext(name)
                if (e.lower() == '.zip'):
                    if config.SOPDS_ZIPSCAN:
                        self.processzip(name,full_path,file)
                else:
                    file_size=os.path.getsize(file)
                    self.processfile(name,full_path,file,None,0,file_size)                   

        #if config.SOPDS_DELETE_LOGICAL:
        #    self.books_deleted=opdsdb.books_del_logical()
        #else:
        #    self.books_deleted=opdsdb.books_del_phisical()
            
        self.books_deleted=opdsdb.books_del_phisical()
        
        self.log_stats()

    def inpskip_callback(self, inpx, inp_name, inp_size):
        
        self.zip_file = os.path.join(inpx,"%s%s"%(inp_name,'.zip'))
        self.rel_path=os.path.relpath(self.zip_file,config.SOPDS_ROOT_LIB)            
        
        if opdsdb.arc_skip(self.rel_path,inp_size):
            self.logger.info('Skip ZIP for INP archive '+self.zip_file+'. Not changed.')
            result = 1               
        else:    
            self.logger.info('Start process ZIP for INP archive = '+self.zip_file) 
            self.inp_cat = opdsdb.addcattree(self.rel_path, opdsdb.CAT_INP, inp_size)
            result = 0
         
        return result
                
    def inpx_callback(self, inpx, inp, meta_data):          
                 
        name = "%s.%s"%(meta_data[inpx_parser.sFile],meta_data[inpx_parser.sExt])
        
        lang=meta_data[inpx_parser.sLang].strip(self.strip_symbols)
        title=meta_data[inpx_parser.sTitle].strip(self.strip_symbols)
        annotation=''
        docdate=meta_data[inpx_parser.sDate].strip(self.strip_symbols)
        
        
        book=opdsdb.addbook(name,self.rel_path,self.inp_cat,meta_data[inpx_parser.sExt],title,annotation,docdate,lang,meta_data[inpx_parser.sSize],opdsdb.CAT_INP)
        self.books_added+=1
        self.books_in_archives+=1
        self.logger.debug("Book "+self.rel_path+"/"+name+" Added ok.")    
        
        for a in meta_data[inpx_parser.sAuthor]:
            author=opdsdb.addauthor(a.replace(',',' '))
            opdsdb.addbauthor(book,author)

        for g in meta_data[inpx_parser.sGenre]:
            opdsdb.addbgenre(book,opdsdb.addgenre(g.lower().strip(self.strip_symbols)))
            
        for s in meta_data[inpx_parser.sSeries]:
            ser=opdsdb.addseries(s.strip())
            opdsdb.addbseries(book,ser,0)                         
                   
    def processinpx(self,name,full_path,file):
        rel_file=os.path.relpath(file,config.SOPDS_ROOT_LIB)
        inpx_size = os.path.getsize(file)
        if config.SOPDS_INPX_SKIP_UNCHANGED and opdsdb.inpx_skip(rel_file,inpx_size):
            self.logger.info('Skip INPX file = '+file+'. Not changed.')
        else:    
            self.logger.info('Start process INPX file = '+file)
            opdsdb.addcattree(rel_file, opdsdb.CAT_INPX, inpx_size)
            inpx = inpx_parser.Inpx(file, self.inpx_callback, self.inpskip_callback)       
            inpx.INPX_TEST_ZIP = config.SOPDS_INPX_TEST_ZIP  
            inpx.INPX_TEST_FILES = config.SOPDS_INPX_TEST_FILES 
            inpx.parse()

    def processzip(self,name,full_path,file):
        rel_file=os.path.relpath(file,config.SOPDS_ROOT_LIB)
        zsize = os.path.getsize(file)
        if opdsdb.arc_skip(rel_file,zsize):
            self.arch_skipped+=1
            self.logger.debug('Skip ZIP archive '+rel_file+'. Already scanned.')
        else:                   
            zip_process_error = 0
            try:
                z = zipfile.ZipFile(file, 'r', allowZip64=True)
                filelist = z.namelist()
                cat = opdsdb.addcattree(rel_file, opdsdb.CAT_ZIP, zsize)
                for n in filelist:
                    try:
                        self.logger.debug('Start process ZIP file = '+file+' book file = '+n)
                        file_size=z.getinfo(n).file_size
                        self.processfile(n,file,z.open(n),cat,opdsdb.CAT_ZIP,file_size)
                    except zipfile.BadZipFile:
                        self.logger.warning('Error processing ZIP file = '+file+' book file = '+n)
                        zip_process_error = 1
                z.close()
                self.arch_scanned+=1
            except zipfile.BadZipFile:
                self.logger.warning('Error while read ZIP archive. File '+file+' corrupt.')
                zip_process_error = 1
            self.bad_archives+=zip_process_error



    def processfile(self,name,full_path,file,cat,archive=0,file_size=0):
        (n,e)=os.path.splitext(name)
        if e.lower() in config.SOPDS_BOOK_EXTENSIONS.split():
            rel_path=os.path.relpath(full_path,config.SOPDS_ROOT_LIB)
            self.logger.debug("Attempt to add book "+rel_path+"/"+name)
            self.fb2parser.reset()
            if opdsdb.findbook(name,rel_path,1)==None:
                if archive==0:
                    cat=opdsdb.addcattree(rel_path,archive)
                title=''
                lang=''
                annotation=''
                docdate=''
                book_is_valid = True

                if e.lower()=='.fb2' and config.SOPDS_FB2PARSE:
                    if isinstance(file, str):
                        f=open(file,'rb')
                    else:
                        f=file
                    self.fb2parser.parse(f)
                    f.close()

                    if len(self.fb2parser.lang.getvalue())>0:
                        lang=self.fb2parser.lang.getvalue()[0].strip(self.strip_symbols)
                    if len(self.fb2parser.book_title.getvalue())>0:
                        title=self.fb2parser.book_title.getvalue()[0].strip(self.strip_symbols)
                    if len(self.fb2parser.annotation.getvalue())>0:
                        annotation=('\n'.join(self.fb2parser.annotation.getvalue()))
                    if len(self.fb2parser.docdate.getvalue())>0:
                        docdate=self.fb2parser.docdate.getvalue()[0].strip();

                    if self.fb2parser.parse_error!=0:
                        errormsg=''
                        self.logger.warning(rel_path+' - '+name+' fb2 parse error ['+errormsg+']')
                        book_is_valid = False
                        self.bad_books+=1

                if book_is_valid:
                    if title=='': title=n

                    book=opdsdb.addbook(name,rel_path,cat,e[1:],title,annotation,docdate,lang,file_size,archive)
                    self.books_added+=1

                    if archive!=0:
                        self.books_in_archives+=1
                    self.logger.debug("Book "+rel_path+"/"+name+" Added ok.")

                    idx=0
                    for l in self.fb2parser.author_last.getvalue():
                        last_name=l.strip(self.strip_symbols)
                        first_name=self.fb2parser.author_first.getvalue()[idx].strip(self.strip_symbols)
                        #author=opdsdb.addauthor(first_name,last_name)
                        author=opdsdb.addauthor("%s %s"%(last_name,first_name))
                        opdsdb.addbauthor(book,author)
                        idx+=1
                    for l in self.fb2parser.genre.getvalue():
                        opdsdb.addbgenre(book,opdsdb.addgenre(l.lower().strip(self.strip_symbols)))
                    for l in self.fb2parser.series.attrss:
                        ser_name=l.get('name')
                        if ser_name:
                            ser=opdsdb.addseries(ser_name.strip())
                            sser_no=l.get('number','0').strip()
                            if sser_no.isdigit():
                                ser_no=int(sser_no)
                            else:
                                ser_no=0
                            opdsdb.addbseries(book,ser,ser_no)
            else:
                self.books_skipped+=1
                self.logger.debug("Book "+rel_path+"/"+name+" Already in DB.")
