# -*- coding: utf-8 -*-

import os
import time
import datetime
import base64
import opds_catalog.zipf as zipfile
import logging

from opds_catalog import fb2parse, settings, opdsdb


class opdsScanner:
    def __init__(self, logger=None):
        self.fb2parser=None
        self.init_parser()

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
        if settings.ROOT_LIB!=None:       self.logger.debug('root_lib = '+settings.ROOT_LIB)
        if settings.FB2TOEPUB!=None: self.logger.debug('fb2toepub = '+settings.FB2TOEPUB)
        if settings.FB2TOMOBI!=None: self.logger.debug('fb2tomobi = '+settings.FB2TOMOBI)
        if settings.TEMP_DIR!=None:       self.logger.debug('temp_dir = '+settings.TEMP_DIR)

    def log_stats(self):
        self.t2=datetime.timedelta(seconds=time.time())
        self.logger.info('Books added      : '+str(self.books_added))
        self.logger.info('Books skipped    : '+str(self.books_skipped))
        self.logger.info('Bad books        : '+str(self.bad_books))
        if settings.DELETE_LOGICAL:
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

        opdsdb.avail_check_prepare()

        for full_path, dirs, files in os.walk(settings.ROOT_LIB, followlinks=True):
            for name in files:
                file=os.path.join(full_path,name)
                (n,e)=os.path.splitext(name)
                if (e.lower() == '.zip'):
                    if settings.ZIPSCAN:
                        self.processzip(name,full_path,file)
                else:
                    file_size=os.path.getsize(file)
                    self.processfile(name,full_path,file,None,0,file_size)
                    
        opdsdb.commit()
        
        if settings.DELETE_LOGICAL:
           self.books_deleted=opdsdb.books_del_logical()
        else:
           self.books_deleted=opdsdb.books_del_phisical()
        self.log_stats()

    def processzip(self,name,full_path,file):
        rel_file=os.path.relpath(file,settings.ROOT_LIB)
        if settings.ZIPRESCAN or (not opdsdb.zipisscanned(rel_file,1)):
            zip_process_error = 0
            try:
                z = zipfile.ZipFile(file, 'r', allowZip64=True)
                filelist = z.namelist()
                cat = opdsdb.addcattree(rel_file, 1)
                for n in filelist:
                    try:
                        self.logger.debug('Start process ZIP file = '+file+' book file = '+n)
                        file_size=z.getinfo(n).file_size
                        self.processfile(n,file,z.open(n),cat,1,file_size)
                    except zipfile.BadZipFile:
                        self.logger.warning('Error processing ZIP file = '+file+' book file = '+n)
                        zip_process_error = 1
                z.close()
                self.arch_scanned+=1
            except zipfile.BadZipFile:
                self.logger.warning('Error while read ZIP archive. File '+file+' corrupt.')
                zip_process_error = 1
            self.bad_archives+=zip_process_error
        else:
            self.arch_skipped+=1
            self.logger.debug('Skip ZIP archive '+rel_file+'. Already scanned.')

    def processfile(self,name,full_path,file,cat,archive=0,file_size=0):
        (n,e)=os.path.splitext(name)
        if e.lower() in settings.BOOK_EXTENSIONS:
            rel_path=os.path.relpath(full_path,settings.ROOT_LIB)
            self.logger.debug("Attempt to add book "+rel_path+"/"+name)
            #self.logger.debug("   full_path = "+full_path)
            #self.logger.debug("   settings.ROOT_LIB = "+settings.ROOT_LIB)
            #self.logger.debug("   rel_path = "+rel_path)

            self.fb2parser.reset()
            if opdsdb.findbook(name,rel_path,1)==None:
                if archive==0:
                    cat=opdsdb.addcattree(rel_path,archive)
                title=''
                lang=''
                annotation=''
                docdate=''
                book_is_valid = True

                if e.lower()=='.fb2' and settings.FB2PARSE:
                    if isinstance(file, str):
                        f=open(file,'rb')
                    else:
                        f=file
                    self.fb2parser.parse(f,settings.FB2HSIZE)
                    f.close()

                    if len(self.fb2parser.lang.getvalue())>0:
                        lang=self.fb2parser.lang.getvalue()[0].strip(' \'\"')
                    if len(self.fb2parser.book_title.getvalue())>0:
                        title=self.fb2parser.book_title.getvalue()[0].strip(' »«\'\"\&\n-.#\\\`')
                    if len(self.fb2parser.annotation.getvalue())>0:
                        annotation=('\n'.join(self.fb2parser.annotation.getvalue()))[:10000]
                    if len(self.fb2parser.docdate.getvalue())>0:
                        docdate=self.fb2parser.docdate.getvalue()[0].strip();

                    if self.fb2parser.parse_error!=0:
                        errormsg=''
                        self.logger.warning(rel_path+' - '+name+' fb2 parse error ['+errormsg+']')
                        book_is_valid = False
                        self.bad_books+=1

                if book_is_valid:
                   if title=='': title=n

                   book=opdsdb.addbook(name,rel_path,cat,e,title,annotation,docdate,lang,file_size,archive)
                   self.books_added+=1

                   if archive==1:
                      self.books_in_archives+=1
                   self.logger.debug("Book "+rel_path+"/"+name+" Added ok.")

                   idx=0
                   for l in self.fb2parser.author_last.getvalue():
                       last_name=l.strip(' \n\'\"\&-.#\\\`')
                       first_name=self.fb2parser.author_first.getvalue()[idx].strip(' \n\'\"\&-.#\\\`')
                       author=opdsdb.addauthor(first_name,last_name)
                       opdsdb.addbauthor(book,author)
                       idx+=1
                   for l in self.fb2parser.genre.getvalue():
                       opdsdb.addbgenre(book,opdsdb.addgenre(l.lower().strip(' \n\'\"')))
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
                          
                if not settings.SINGLE_COMMIT: 
                    opdsdb.commit()

            else:
               self.books_skipped+=1
               self.logger.debug("Book "+rel_path+"/"+name+" Already in DB.")
