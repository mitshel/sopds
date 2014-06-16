# -*- coding: utf-8 -*-

import os
import sys
import mysql.connector
from mysql.connector import errorcode

##########################################################################
# Наименования таблиц БД
#
DB_PREFIX=""
TBL_BOOKS=DB_PREFIX+"books"
TBL_CATALOGS=DB_PREFIX+"catalogs"
TBL_AUTHORS=DB_PREFIX+"authors"
TBL_BAUTHORS=DB_PREFIX+"bauthors"
TBL_GENRES=DB_PREFIX+"genres"
TBL_BGENRES=DB_PREFIX+"bgenres"
TBL_SERIES=DB_PREFIX+"series"
TBL_BSERIES=DB_PREFIX+"bseries"
TBL_BOOKSHELF=DB_PREFIX+"bookshelf"

##########################################################################
# типы каталогов (cat_type)
#
CAT_NORMAL=0
CAT_ZIP=1
CAT_GZ=2

##########################################################################
# Как будем искать дубликаты
#
CMP_NONE=0
CMP_NORMAL=1
CMP_STRONG=2
CMP_CLEAR=3
CMP_TITLE_FTYPE_FSIZE=2
CMP_TITLE_AUTHORS=1

##########################################################################
# разные константы
#
unknown_genre='Неизвестный жанр'


###########################################################################
# Класс доступа к  MYSQL
#

class opdsDatabase:
  def __init__(self,iname,iuser,ipass,ihost,iroot_lib):
    self.db_name=iname
    self.db_user=iuser
    self.db_pass=ipass
    self.db_host=ihost
    self.errcode=0
    self.err=""
    self.isopen=False
    self.next_page=False
    self.root_lib=iroot_lib

  def openDB(self):
    if not self.isopen:
      try:
         # buffered=true сделано для того чтобы избежать выборки fetchall при поиске книг и тэгов
         self.cnx = mysql.connector.connect(user=self.db_user, password=self.db_pass, host=self.db_host, database=self.db_name, buffered=True)
      except mysql.connector.Error as err:
         if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            self.err="Something is wrong with your user name or password"
            self.errcode=1
         elif err.errno == errorcode.ER_BAD_DB_ERROR:
            self.err="Database does not exists"
            self.errcode=2
         else:
            self.err=err
            self.errcode=3
      else:
         self.isopen=True
    else:
      self.errcode=4
      self.err="Error open database. Database Already open."

  def closeDB(self):
    if self.isopen:
      self.cnx.close()
      self.isopen=False
    else:
      self.errcode=5
      self.err="Attempt to close not opened database."

  def printDBerr(self):
    if self.errcode==0:
       print("No Database Error found.")
    else:
       print("Error Code =",self.errcode,". Error Message:",self.err)

  def clearDBerr(self):
    self.err=""
    self.errcode=0

  def findbook(self, name, path, setavail=0):
    # Здесь специально не делается проверка avail, т.к. если удаление было логическим, а книга была восстановлена в своем старом месте
    # то произойдет восстановление записи об этой книги а не добавится новая
    sql_findbook=("select book_id from "+TBL_BOOKS+" where filename=%s and path=%s")
    data_findbook=(name,path)
    cursor=self.cnx.cursor()
    cursor.execute(sql_findbook,data_findbook)
    row=cursor.fetchone()
    cursor.close()
    if row==None:
       book_id=0
    else:
       book_id=row[0]
       if setavail:
          sql='update '+TBL_BOOKS+' set avail=2 where book_id=%s'%(book_id)
          cursor=self.cnx.cursor()
          cursor.execute(sql)
          cursor.close()
    return book_id

#  def finddouble(self,title,format,file_size):
#    sql_findbook=("select book_id from "+TBL_BOOKS+" where title=%s and format=%s and filesize=%s and avail!=0 and doublicat=0")
#    data_findbook=(title,format,file_size)
#    cursor=self.cnx.cursor()
#    cursor.execute(sql_findbook,data_findbook)
#    row=cursor.fetchone()
#    if row==None:
#       book_id=0
#    else:
#       book_id=row[0]
#    cursor.close()
#    return book_id

  def findbookshelf(self,user,book_id):
    sql=("select book_id from "+TBL_BOOKSHELF+" where user=%s and book_id=%s")
    data=(user,book_id)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    row=cursor.fetchone()
    if row==None:
       book_id=0
    else:
       book_id=row[0]
    cursor.close()
    return book_id

  def addbookshelf(self,user,book_id):
    if self.findbookshelf(user,book_id)==0:
       sql=("insert into "+TBL_BOOKSHELF+"(user,book_id) VALUES(%s, %s)")
       data=(user,book_id)
       cursor=self.cnx.cursor()
       cursor.execute(sql,data)
       self.cnx.commit()
       book_id=cursor.lastrowid
       cursor.close()
       return book_id

  def addbook(self, name, path, cat_id, exten, title, annotation, docdate, lang, size=0, archive=0, doublicates=0):
    format=exten[1:]
    format=format.lower()
#    if doublicates!=0:
#       doublicat=self.finddouble(title,format,size)
#    else:
    doublicat=0
    sql_addbook=("insert into "+TBL_BOOKS+"(filename,path,cat_id,filesize,format,title,annotation,docdate,lang,cat_type,doublicat,avail) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 2)")
    data_addbook=(name,path,cat_id,size,format,title,annotation,docdate,lang,archive,doublicat)
    cursor=self.cnx.cursor()
    cursor.execute(sql_addbook,data_addbook)
    book_id=cursor.lastrowid
    cursor.close()
    return book_id

#  def addcover(self,book_id,fn,cover_type):
#    sql=("update "+TBL_BOOKS+" set cover=%s, cover_type=%s where book_id=%s")
#    data=(fn,cover_type,book_id)
#    cursor=self.cnx.cursor()
#    cursor.execute(sql,data)
#    cursor.close()
    
  def findauthor(self,first_name,last_name):
    sql_findauthor=("select author_id from "+TBL_AUTHORS+" where last_name=%s and first_name=%s LIMIT 1")
    data_findauthor=(last_name,first_name)
    cursor=self.cnx.cursor()
    cursor.execute(sql_findauthor,data_findauthor)
    row=cursor.fetchone()
    if row==None:
       author_id=0
    else:
       author_id=row[0]
    cursor.close()
    return author_id

  def findbauthor(self, book_id, author_id):
    sql_findbauthor=("select book_id from "+TBL_BAUTHORS+" where book_id=%s and author_id=%s")
    data_findbauthor=(book_id,author_id)
    cursor=self.cnx.cursor()
    cursor.execute(sql_findbauthor,data_findbauthor)
    row=cursor.fetchone()
    result=(row!=None)
    cursor.close()
    return result

  def addauthor(self, first_name, last_name):
    author_id=self.findauthor(first_name,last_name)
    if author_id!=0:
       return author_id
    sql_addauthor=("insert into "+TBL_AUTHORS+"(first_name,last_name) VALUES(%s,%s)")
    data_addauthor=(first_name,last_name)
    cursor=self.cnx.cursor()
    cursor.execute(sql_addauthor,data_addauthor)
    author_id=cursor.lastrowid
    cursor.close()
    return author_id

  def addbauthor(self, book_id, author_id):
       sql_addbauthor=("insert into "+TBL_BAUTHORS+"(book_id,author_id) VALUES(%s,%s)")
       data_addbauthor=(book_id,author_id)
       cursor=self.cnx.cursor()
       try:
         cursor.execute(sql_addbauthor,data_addbauthor)
       except:
         pass
       finally:
         cursor.close()

  def findgenre(self,genre):
    sql=("select genre_id from "+TBL_GENRES+" where genre='"+genre+"'")
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    row=cursor.fetchone()
    if row==None:
       genre_id=0
    else:
       genre_id=row[0]
    cursor.close()
    return genre_id

  def findbgenre(self, book_id, genre_id):
    sql=("select book_id from "+TBL_BGENRES+" where book_id=%s and genre_id=%s")
    data=(book_id,genre_id)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    row=cursor.fetchone()
    result=(row!=None)
    cursor.close()
    return result

  def addgenre(self, genre):
    genre_id=self.findgenre(genre)
    if genre_id!=0:
       return genre_id
    sql=("insert into "+TBL_GENRES+"(genre,section,subsection) VALUES(%s,%s,%s)")
    data=(genre,unknown_genre,genre)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    genre_id=cursor.lastrowid
    cursor.close()
    return genre_id

  def addbgenre(self, book_id, genre_id):
       sql=("insert into "+TBL_BGENRES+"(book_id,genre_id) VALUES(%s,%s)")
       data=(book_id,genre_id)
       cursor=self.cnx.cursor()
       try:
         cursor.execute(sql,data)
       except:
         pass
       finally:
         cursor.close()

  def findseries(self,ser):
    sql=("select ser_id from "+TBL_SERIES+" where ser=%s")
    data=(ser,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    row=cursor.fetchone()
    if row==None:
       ser_id=0
    else:
       ser_id=row[0]
    cursor.close()
    return ser_id

  def findbseries(self, book_id, ser_id):
    sql=("select book_id from "+TBL_BSERIES+" where book_id=%s and ser_id=%s")
    data=(book_id,ser_id)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    row=cursor.fetchone()
    result=(row!=None)
    cursor.close()
    return result

  def addseries(self, ser):
    ser_id=self.findseries(ser)
    if ser_id!=0:
       return ser_id
    sql=("insert into "+TBL_SERIES+"(ser) VALUES(%s)")
    data=(ser,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    ser_id=cursor.lastrowid
    cursor.close()
    return ser_id

  def addbseries(self, book_id, ser_id, ser_no):
       sql=("insert into "+TBL_BSERIES+"(book_id,ser_id,ser_no) VALUES(%s,%s,%s)")
       data=(book_id,ser_id,ser_no)
       cursor=self.cnx.cursor()
       try:
         cursor.execute(sql,data)
       except:
         pass
       finally:
         cursor.close()

  def findcat(self, catalog):
    (head,tail)=os.path.split(catalog)
    sql_findcat=("select cat_id from "+TBL_CATALOGS+" where cat_name=%s and path=%s")
    data_findcat=(tail,catalog)
    cursor=self.cnx.cursor()
    cursor.execute(sql_findcat,data_findcat)
    row=cursor.fetchone()
    if row==None:
       cat_id=0
    else:
       cat_id=row[0]
    cursor.close()
    return cat_id

  def addcattree(self, catalog, archive=0):
    cat_id=self.findcat(catalog)
    if cat_id!=0:
       return cat_id 
    if catalog=="":
       return 0
    (head,tail)=os.path.split(catalog)
    parent_id=self.addcattree(head)
    sql_addcat=("insert into "+TBL_CATALOGS+"(parent_id,cat_name,path,cat_type) VALUES(%s, %s, %s, %s)")
    data_addcat=(parent_id,tail,catalog,archive)
    cursor=self.cnx.cursor()
    cursor.execute(sql_addcat,data_addcat)
    cat_id=cursor.lastrowid
    cursor.close()
    return cat_id

  def getcatinparent(self,parent_id,limit=0,page=0):
    if limit==0:
       limitstr=""
    else:
       limitstr="limit "+str(limit*page)+","+str(limit)
    sql_findcats=("select cat_id,cat_name from "+TBL_CATALOGS+" where parent_id="+str(parent_id)+" order by cat_name "+limitstr)
    cursor=self.cnx.cursor()
    cursor.execute(sql_findcats)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getbooksincat(self,cat_id,limit=0,page=0):
    if limit==0:
       limitstr=""
    else:
       limitstr="limit "+str(limit*page)+","+str(limit)
    sql_findbooks=("select book_id,filename, path, registerdate from "+TBL_BOOKS+" where cat_id="+str(cat_id)+" and avail!=0 order by filename "+limitstr)
    cursor=self.cnx.cursor()
    cursor.execute(sql_findbooks)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getitemsincat(self,cat_id,limit=0,page=0):
    if limit==0:
       limitstr=""
    else:
       limitstr="limit "+str(limit*page)+","+str(limit)
    sql_finditems=("select SQL_CALC_FOUND_ROWS 1,cat_id,cat_name,path,now(),cat_name as title,'' as docdate,'' as annotation,'cat' as format, 0 as filesize, '' as cover, '' as cover_type from "+TBL_CATALOGS+" where parent_id="+str(cat_id)+" union all "
    "select 2,book_id,filename,path,registerdate,title,annotation,docdate,format,filesize,cover,cover_type from "+TBL_BOOKS+" where cat_id="+str(cat_id)+" and avail!=0 order by 1,6 "+limitstr)
    cursor=self.cnx.cursor()
    cursor.execute(sql_finditems)
    rows=cursor.fetchall()
    
    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getbook(self,book_id):
    sql_getbook=("select filename, path, registerdate, format, title, annotation, docdate,cat_type, cover, cover_type, filesize from "+TBL_BOOKS+" where book_id="+str(book_id)+" and avail!=0")
    cursor=self.cnx.cursor()
    cursor.execute(sql_getbook)
    row=cursor.fetchone()
    cursor.close
    return row

  def getauthors(self,book_id):
    sql=("select a.author_id,first_name,last_name from "+TBL_AUTHORS+" a, "+TBL_BAUTHORS+" b where b.author_id=a.author_id and b.book_id="+str(book_id))
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getauthor_name(self, author_id):
    sql=("select first_name,last_name from "+TBL_AUTHORS+" where author_id=%s")
    data=(author_id,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    row=cursor.fetchone()
    cursor.close
    return row

  def getser_name(self, ser_id):
    sql=("select ser from "+TBL_SERIES+" where ser_id=%s")
    data=(ser_id,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    row=cursor.fetchone()
    cursor.close
    return row

  def getgenres(self,book_id):
    sql=("select section, subsection from "+TBL_GENRES+" a, "+TBL_BGENRES+" b where b.genre_id=a.genre_id and b.book_id="+str(book_id))
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getseries(self,book_id):
    sql=("select a.ser, b.ser_no from "+TBL_SERIES+" a, "+TBL_BSERIES+" b where b.ser_id=a.ser_id and b.book_id="+str(book_id))
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getauthor_2letters(self,letters,alpha=0,new_period=0):
    lc=len(letters)+1
    having=''
    if lc==1:
       if   alpha==1: having=" having INSTR('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ',letters)>0 and letters!=''"
       elif alpha==2: having=" having INSTR('0123456789',letters)>0 and letters!=''"
       elif alpha==3: having=" having INSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ',letters)>0 and letters!=''"
       elif alpha==4: having=" having INSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ0123456789',letters)=0 and letters!=''"
    if new_period==0: period=''
    else: period="and author_id in (select b.author_id from bauthors b left join books c on b.book_id=c.book_id where registerdate>now()-INTERVAL %s DAY group by b.author_id)"%new_period
    sql="select UPPER(substring(CONCAT(last_name,' ',first_name),1,"+str(lc)+")) as letters, count(*) as cnt from "+TBL_AUTHORS+" where CONCAT(last_name,' ',first_name) like %s "+period+" group by 1"+having+" order by 1"
    data=(letters+'%',)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def gettitle_2letters(self,letters,doublicates=True,alpha=0,new_period=0):
    if doublicates: dstr=""
    else: dstr=" and doublicat=0 "
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY)"%new_period
    lc=len(letters)+1
    having=''
    if lc==1:
       if   alpha==1: having=" having INSTR('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ',letters)>0 and letters!=''"
       elif alpha==2: having=" having INSTR('0123456789',letters)>0 and letters!=''"
       elif alpha==3: having=" having INSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ',letters)>0 and letters!=''"
       elif alpha==4: having=" having INSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ0123456789',letters)=0 and letters!=''"

    sql="select UPPER(substring(title,1,"+str(lc)+")) as letters, count(*) as cnt from "+TBL_BOOKS+" where title like %s and avail!=0 "+dstr+period+" group by 1"+having+" order by 1"
    data=(letters+'%',)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getseries_2letters(self,letters,alpha=0,new_period=0):
    lc=len(letters)+1
    having=''
    if lc==1:
       if   alpha==1: having=" having INSTR('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ',letters)>0 and letters!=''"
       elif alpha==2: having=" having INSTR('0123456789',letters)>0 and letters!=''"
       elif alpha==3: having=" having INSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ',letters)>0 and letters!=''"
       elif alpha==4: having=" having INSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ0123456789',letters)=0 and letters!=''"
    if new_period==0: period=''
    else: period="and ser_id in (select b.ser_id from bseries b left join books c on b.book_id=c.book_id where registerdate>now()-INTERVAL %s DAY group by b.ser_id)"%new_period

    sql="select UPPER(substring(ser,1,"+str(lc)+")) as letters, count(*) as cnt from "+TBL_SERIES+" where ser like %s "+period+" group by 1"+having+" order by 1"
    data=(letters+'%',)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()
    cursor.close
    return rows


  def getbooksfortitle(self,letters,limit=0,page=0,doublicates=True,new_period=0):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    if doublicates: dstr=''
    else: dstr=' and doublicat=0'
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY)"%new_period
    sql="select SQL_CALC_FOUND_ROWS book_id,filename,path,registerdate,title,annotation,docdate,format,filesize,cover,cover_type from "+TBL_BOOKS+" where title like %s and avail!=0"+dstr+period+" order by title "+limitstr
    data=(letters+'%',)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getdoublecount(self,id):
    sql='select count(*) from '+TBL_BOOKS+' where doublicat=%s'
    data=(id,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)

    row=cursor.fetchone()
    if row==None:
       dcount=0
    else:
       dcount=row[0]
    cursor.close()
    return dcount

  def getdoubles(self,id,limit=0,page=0):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    sql="select SQL_CALC_FOUND_ROWS book_id,filename,path,registerdate,title,annotation,docdate,format,filesize,cover,cover_type from "+TBL_BOOKS+" where doublicat=%s and avail!=0 order by docdate "+limitstr
    data=(id,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getauthorsbyl(self,letters,limit=0,page=0,doublicates=True,new_period=0):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    if doublicates: dstr=''
    else: dstr=' and c.doublicat=0 '
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY) and a.author_id in (select b.author_id from bauthors b left join books c on b.book_id=c.book_id where registerdate>now()-INTERVAL %s DAY group by b.author_id)"%(new_period,new_period)

    sql="select SQL_CALC_FOUND_ROWS a.author_id, a.first_name, a.last_name, count(*) as cnt from "+TBL_AUTHORS+" a, "+TBL_BAUTHORS+" b, "+TBL_BOOKS+" c where a.author_id=b.author_id and b.book_id=c.book_id and CONCAT(a.last_name,' ',a.first_name) like %s and c.avail!=0 "+dstr+period+" group by 1,2,3 order by 3,2 "+limitstr
    data=(letters+'%',)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getbooksforautor(self,author_id,limit=0,page=0,doublicates=True,new_period=0):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    if doublicates: dstr=''
    else: dstr=' and a.doublicat=0 '
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY)"%new_period
    sql="select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.annotation,a.docdate,a.format,a.filesize,a.cover,a.cover_type from "+TBL_BOOKS+" a, "+TBL_BAUTHORS+" b where a.book_id=b.book_id and b.author_id="+str(author_id)+" and a.avail!=0 "+dstr+period+" order by a.title "+limitstr
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getbooksforautorser(self,author_id,ser_id,limit=0,page=0,doublicates=True):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    if doublicates: dstr=''
    else: dstr=' and a.doublicat=0 '
    if ser_id!=0:
       sql=("select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.annotation,a.docdate,a.format,a.filesize,a.cover,a.cover_type "
       "from "+TBL_BOOKS+" a "
       "left join "+TBL_BAUTHORS+" b on a.book_id=b.book_id "
       "left join "+TBL_BSERIES +" c on a.book_id=c.book_id "
       "where author_id=%s and ser_id=%s and a.avail!=0 "+dstr+" order by c.ser_no, a.title "+limitstr)
       data=(author_id,ser_id)
    else:
       sql=("select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.annotation,a.docdate,a.format,a.filesize,a.cover,a.cover_type "
       "from "+TBL_BOOKS+" a "
       "left join "+TBL_BAUTHORS+" b on a.book_id=b.book_id "
       "left outer join "+TBL_BSERIES +" c on a.book_id=c.book_id "
       "where author_id=%s and ser_id is NULL and a.avail!=0 "+dstr+" order by a.title "+limitstr)
       data=(author_id,)
       
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getseriesforauthor(self,author_id,limit=0,page=0,doublicates=True):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    if doublicates: dstr=''
    else: dstr=' and doublicat=0 '

    sql=("select SQL_CALC_FOUND_ROWS a.ser_id, a.ser, count(*) from "+TBL_SERIES+" a "
    "left join "+TBL_BSERIES+" b on a.ser_id=b.ser_id "
    "left join "+TBL_BAUTHORS+" c on b.book_id=c.book_id "
    "left join "+TBL_BOOKS+" d on b.book_id=d.book_id "
    "where author_id=%s and avail!=0 "+dstr+" group by 1,2 order by a.ser "+limitstr)
    data=(author_id,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows
    
  def getseriesbyl(self,letters,limit=0,page=0,doublicates=True,new_period=0):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    if doublicates: dstr=''
    else: dstr=' and c.doublicat=0 '
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY) and a.ser_id in (select b.ser_id from bseries b left join books c on b.book_id=c.book_id where registerdate>now()-INTERVAL %s DAY group by b.ser_id)"%(new_period,new_period)
    sql="select SQL_CALC_FOUND_ROWS a.ser_id, a.ser, count(*) as cnt from "+TBL_SERIES+" a, "+TBL_BSERIES+" b, "+TBL_BOOKS+" c where a.ser_id=b.ser_id and b.book_id=c.book_id and a.ser like %s and c.avail!=0 "+dstr+period+" group by 1,2 order by 2 "+limitstr
    data=(letters+'%',)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getbooksforser(self,ser_id,limit=0,page=0,doublicates=True,new_period=0):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    if doublicates: dstr=''
    else: dstr=' and a.doublicat=0 '
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY)"%new_period
    sql="select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.annotation,a.docdate,a.format,a.filesize,a.cover,a.cover_type from "+TBL_BOOKS+" a, "+TBL_BSERIES+" b where a.book_id=b.book_id and b.ser_id="+str(ser_id)+" and a.avail!=0 "+dstr+period+" order by b.ser_no, a.title "+limitstr
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows


  def getlastbooks(self,limit=0):
    if limit==0:
       limitstr=""
    else:
       limitstr="limit "+str(limit)
    sql="select book_id,filename,path,registerdate,title,annotation,docdate,format,filesize,cover,cover_type from "+TBL_BOOKS+" where avail!=0 order by registerdate desc "+limitstr
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getgenres_sections(self,doublicates=True,new_period=0):
    if doublicates: dstr=''
    else: dstr=' and c.doublicat=0 '
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY)"%new_period
    if new_period==0:
       sql="select min(a.genre_id), a.section, count(*) as cnt from "+TBL_GENRES+" a, "+TBL_BGENRES+" b where a.genre_id=b.genre_id group by a.section order by a.section"
    else:
       sql="select min(a.genre_id), a.section, count(*) as cnt from "+TBL_GENRES+" a, "+TBL_BGENRES+" b, "+TBL_BOOKS+" c where a.genre_id=b.genre_id and b.book_id=c.book_id and c.avail!=0 "+dstr+period+" group by a.section order by a.section"
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getgenres_subsections(self,section_id,doublicates=True,new_period=0):
    if doublicates: dstr=''
    else: dstr=' and c.doublicat=0 '
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY)"%new_period
    if new_period==0:
       sql="select a.genre_id, a.subsection, count(*) as cnt from "+TBL_GENRES+" a, "+TBL_BGENRES+" b where a.genre_id=b.genre_id and section in (select section from "+TBL_GENRES+" where genre_id="+str(section_id)+") group by a.subsection order by a.subsection"
    else:
       sql="select a.genre_id, a.subsection, count(*) as cnt from "+TBL_GENRES+" a, "+TBL_BGENRES+" b, "+TBL_BOOKS+" c  where a.genre_id=b.genre_id and b.book_id=c.book_id and c.avail!=0 "+dstr+period+" and section in (select section from "+TBL_GENRES+" where genre_id="+str(section_id)+") group by a.subsection order by a.subsection"

    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getbooksforgenre(self,genre_id,limit=0,page=0,doublicates=True,alpha=0,new_period=0):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    if doublicates: dstr=''
    else: dstr=' and a.doublicat=0 '
    if new_period==0: period=''
    else: period=" and (registerdate>now()-INTERVAL %s DAY)"%new_period
    having=''
    if   alpha==1: having=" and INSTR('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ',UPPER(substr(a.title,1,1)))>0"
    elif alpha==2: having=" and INSTR('0123456789',UPPER(substr(a.title,1,1)))>0"
    elif alpha==3: having=" and INSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZ',UPPER(substr(a.title,1,1)))>0"
    elif alpha==4: having=" and INSTR('ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ0123456789',UPPER(substr(a.title,1,1)))=0"

    sql="select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.annotation,a.docdate,a.format,a.filesize,a.cover,a.cover_type from "+TBL_BOOKS+" a, "+TBL_BGENRES+" b where a.book_id=b.book_id and b.genre_id="+str(genre_id)+" and a.avail!=0 "+dstr+period+having+" order by a.lang, a.title "+limitstr
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getbooksforuser(self,user,limit=0,page=0):
    if limit==0: limitstr=""
    else: limitstr="limit "+str(limit*page)+","+str(limit)
    sql="select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.annotation,a.docdate,a.format,a.filesize,a.cover,a.cover_type from "+TBL_BOOKS+" a, "+TBL_BOOKSHELF+" b where a.book_id=b.book_id and b.user=%s and a.avail!=0 order by readtime desc "+limitstr
    data=(user,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    rows=cursor.fetchall()

    cursor.execute("SELECT FOUND_ROWS()")
    found_rows=cursor.fetchone()
    if found_rows[0]>limit*page+limit:
       self.next_page=True
    else:
       self.next_page=False

    cursor.close
    return rows

  def getdbinfo(self,doublicates=True,book_shelf=False, user=None):
    if doublicates: dstr=''
    else: dstr='and doublicat=0'
    if book_shelf and user!=None: bs=" union all select 6 s, count(book_id) from "+TBL_BOOKSHELF+" where user='"+user+"' "
    else: bs=""

    sql="select 1 s, count(avail) from %s where avail!=0 %s union all select 2 s, count(author_id) from %s union all select 3 s, count(cat_id) from %s union all select 4 s, count(genre_id) from %s union all select 5 s, count(ser_id) from %s %s order by s"%(TBL_BOOKS,dstr,TBL_AUTHORS,TBL_CATALOGS,TBL_GENRES,TBL_SERIES,bs)
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getnewinfo(self,doublicates=True,new_period=0):
    if doublicates: dstr=''
    else: dstr='and doublicat=0'

    if new_period==0: period=''
    else: period='and registerdate>now()-INTERVAL %s DAY'%new_period

    sql="select 1 s, count(avail) from %s where avail!=0 %s %s"%(TBL_BOOKS,dstr,period)
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()

    cursor.close
    return rows
  
  def zipisscanned(self,zipname,setavail=0):
    sql='select cat_id from '+TBL_BOOKS+' where path="'+zipname+'" limit 1'
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    row=cursor.fetchone()
    cursor.close
    if row==None:
       cat_id=0
    else:
       cat_id=row[0]
       if setavail:
          sql='update '+TBL_BOOKS+' set avail=2 where cat_id=%s'%(cat_id)
          cursor=self.cnx.cursor()
          cursor.execute(sql)
          cursor.close()
    return cat_id

# Книги где avail=0 уже известно что удалены
# Книги где avail=2 это только что прверенные существующие книги
# Устанавливаем avail=1 для книг которые не удалены. Во время проверки если они не удалены им присвоится значение 2
# Книги с avail=0 проверятся не будут и будут убраны из всех выдач и всех обработок.
# 
# три позиции (0,1,2) сделаны для того чтобы сделать возможным корректную работу cgi-скрипта во время сканирования библиотеки
#
  def avail_check_prepare(self):
    sql='update '+TBL_BOOKS+' set avail=1 where avail!=0'
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    self.cnx.commit()
    cursor.close

  def books_del_logical(self):
    sql='update '+TBL_BOOKS+' set avail=0 where avail=1'
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    cursor.execute("SELECT ROW_COUNT()")
    row_count=cursor.fetchone()[0]
    self.cnx.commit()
    cursor.close
    return row_count

  def books_del_phisical(self):
    cursor=self.cnx.cursor()
    sql='delete from '+TBL_BAUTHORS+' where book_id in (select book_id from '+TBL_BOOKS+' where avail<=1)'
    cursor.execute(sql)
    sql='delete from '+TBL_BGENRES+' where book_id in (select book_id from '+TBL_BOOKS+' where avail<=1)'
    cursor.execute(sql)

    sql='delete from '+TBL_BOOKS+' where avail<=1'
    cursor.execute(sql)
    cursor.execute("SELECT ROW_COUNT()")
    row_count=cursor.fetchone()[0]
    self.cnx.commit()
    cursor.close
    return row_count

#  def update_double(self):
#    sql='call sp_update_dbl()'
#    cursor=self.cnx.cursor()
#    cursor.execute(sql)
#    self.cnx.commit()
#    cursor.close

  def mark_double(self, cmp_type=CMP_NORMAL):
    sql='call sp_mark_dbl(%s)'
    data=(cmp_type,)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    self.cnx.commit()
    cursor.close

  def commit(self):
    self.cnx.commit()

  def __del__(self):
    self.closeDB()

