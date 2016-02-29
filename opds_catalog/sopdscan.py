import os
import time
import datetime
import base64
import zipfile
import logging

from opds_catalog import fb2parse, settings, opdsdb


class opdsScanner:
    def __init__(self):
        self.fb2parser=None
        self.init_parser()

    def init_stats(self):
        self.t1=datetime.timedelta(seconds=time.time())
        self.t2=self.t1
        self.t3=self.t1
        self.books_added   = 0
        self.books_skipped = 0
        self.books_deleted = 0
        self.arch_scanned = 0
        self.arch_skipped = 0
        self.bad_archives = 0
        self.books_in_archives = 0

    def init_parser(self):
        self.fb2parser=fb2parse.fb2parser(False)

    def log_options(self):
        pass

    def log_stats(self):
        pass

    def log_stats_dbl(self):
        pass

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
                    self.processfile(name,full_path,file,0,file_size)

        if settings.DELETE_LOGICAL:
           self.books_deleted=opdsdb.books_del_logical()
        else:
           self.books_deleted=opdsdb.books_del_phisical()
        self.log_stats()

#        if settings.DUBLICATES_FIND!=0:
#           self.logger.info('Starting mark_double proc with DUBLICATES_FIND param = %s'%self.cfg.DUBLICATES_FIND)
#           self.opdsdb.mark_double(self.cfg.DUBLICATES_FIND)
#           self.log_stats_dbl()

#        self.opdsdb.closeDB()
#        self.opdsdb=None

    def processzip(self,name,full_path,file):
        rel_file=os.path.relpath(file,settings.ROOT_LIB)
        if settings.ZIPRESCAN or opdsdb.zipisscanned(rel_file,1)==None:
            cat_id=opdsdb.addcattree(rel_file,1)
            try:
                z = zipfile.ZipFile(file, 'r', allowZip64=True)
                filelist = z.namelist()
                for n in filelist:
                    try:
                        print('Start process ZIP file = '+file+' book file = '+n)
                        file_size=z.getinfo(n).file_size
                        self.processfile(n,file,z.open(n),1,file_size,cat_id=cat_id)
                    except:
                        print('Error processing ZIP file = '+file+' book file = '+n)
                z.close()
                self.arch_scanned+=1
            except:
                print('Error while read ZIP archive. File '+file+' corrupt.')
                self.bad_archives+=1
        else:
            self.arch_skipped+=1
            print('Skip ZIP archive '+rel_file+'. Already scanned.')

    def processfile(self,name,full_path,file,archive=0,file_size=0,cat_id=0):
        (n,e)=os.path.splitext(name)
        if e.lower() in settings.BOOK_EXTENSIONS:
            rel_path=os.path.relpath(full_path,settings.ROOT_LIB)
            print("Attempt to add book "+rel_path+"/"+name)
            self.fb2parser.reset()
            if opdsdb.findbook(name,rel_path,1)==None:
               if archive==0:
                  catalog=opdsdb.addcattree(rel_path,archive)
               title=''
               lang=''
               annotation=''
               docdate=''

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
                     title=self.fb2parser.book_title.getvalue()[0].strip(' \'\"\&-.#\\\`')
                  if len(self.fb2parser.annotation.getvalue())>0:
                     annotation=('\n'.join(self.fb2parser.annotation.getvalue()))[:10000]
                  if len(self.fb2parser.docdate.getvalue())>0:
                     docdate=self.fb2parser.docdate.getvalue()[0].strip();

                  if self.fb2parser.parse_error!=0:
#                     errormsg=error.message(self.fb2parser.parse_errormsg.code)
                     errormsg=''
                     print(rel_path+' - '+name+' fb2 parse error ['+errormsg+']')

               if title=='': title=n

               book_id=self.opdsdb.addbook(name,rel_path,cat_id,e,title,annotation,docdate,lang,file_size,archive,settings.DUBLICATES_FIND)
               self.books_added+=1

               if archive==1:
                  self.books_in_archives+=1
               print("Book "+rel_path+"/"+name+" Added ok.")

               idx=0
               for l in self.fb2parser.author_last.getvalue():
                   last_name=l.strip(' \'\"\&-.#\\\`')
                   first_name=self.fb2parser.author_first.getvalue()[idx].strip(' \'\"\&-.#\\\`')
                   author_id=self.opdsdb.addauthor(first_name,last_name)
                   self.opdsdb.addbauthor(book_id,author_id)
                   idx+=1
               for l in self.fb2parser.genre.getvalue():
                   self.opdsdb.addbgenre(book_id,self.opdsdb.addgenre(l.lower().strip(' \'\"')))
               for l in self.fb2parser.series.attrss:
                   ser_name=l.get('name')
                   if ser_name:
                      ser_id=self.opdsdb.addseries(ser_name.strip())
                      sser_no=l.get('number','0').strip()
                      if sser_no.isdigit():
                         ser_no=int(sser_no)
                      else:
                         ser_no=0
                      self.opdsdb.addbseries(book_id,ser_id,ser_no)

            else:
               self.books_skipped+=1
               print("Book "+rel_path+"/"+name+" Already in DB.")
