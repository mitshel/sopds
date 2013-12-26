#!/usr/bin/python3
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
TBL_TAGS=DB_PREFIX+"tags"
TBL_BTAGS=DB_PREFIX+"btags"
TBL_CATALOGS=DB_PREFIX+"catalogs"
TBL_AUTHORS=DB_PREFIX+"authors"
TBL_BAUTHORS=DB_PREFIX+"bauthors"

##########################################################################
# типы каталогов (cat_type)
#
CAT_NORMAL=0
CAT_ZIP=1
CAT_GZ=2

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

  def findtag(self,tag):
    sql_findtag=("select tag_id from "+TBL_TAGS+" where tag='"+tag+"'")
    cursor=self.cnx.cursor()
    cursor.execute(sql_findtag)
    row=cursor.fetchone()
    if row==None:
       tag_id=0
    else:
       tag_id=row[0]
    cursor.close()
    return tag_id

  def findbook(self, name, path):
    sql_findbook=("select book_id from "+TBL_BOOKS+" where filename=%s and path=%s")
    data_findbook=(name,path)
    cursor=self.cnx.cursor()
    cursor.execute(sql_findbook,data_findbook)
    row=cursor.fetchone()
    if row==None:
       book_id=0
    else:
       book_id=row[0]
    cursor.close()
    return book_id

  def findbtag(self, book_id, tag_id):
    sql_findbtag=("select book_id from "+TBL_BTAGS+" where book_id=%s and tag_id=%s")
    data_findbtag=(book_id,tag_id)
    cursor=self.cnx.cursor()
    cursor.execute(sql_findbtag,data_findbtag)
    row=cursor.fetchone()
    result=(row!=None)
    cursor.close()
    return result
 
  def addbook(self, name, path, cat_id, exten, title, genre, lang, size=0, archive=0):
    book_id=self.findbook(name,path)
    if book_id!=0:
       return book_id
    format=exten[1:]
    sql_addbook=("insert into "+TBL_BOOKS+"(filename,path,cat_id,filesize,format,title,genre,lang,cat_type) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)")
    data_addbook=(name,path,cat_id,size,format,title,genre,lang,archive)
    cursor=self.cnx.cursor()
    cursor.execute(sql_addbook,data_addbook)
    book_id=cursor.lastrowid
    self.cnx.commit()
    cursor.close()
    return book_id

  def addcover(self,book_id,fn,cover_type):
    sql=("update "+TBL_BOOKS+" set cover=%s, cover_type=%s where book_id=%s")
    data=(fn,cover_type,book_id)
    cursor=self.cnx.cursor()
    cursor.execute(sql,data)
    self.cnx.commit()
    cursor.close()
    
  def addtag(self, tag, tag_type=0):
    tag_id=self.findtag(tag)
    if tag_id!=0:
       return tag_id
    sql_addtag=("insert into "+TBL_TAGS+"(tag,tag_type) VALUES(%s,%s)")
    data_addtag=(tag,tag_type)
    cursor=self.cnx.cursor()
    cursor.execute(sql_addtag,data_addtag)
    tag_id=cursor.lastrowid
    self.cnx.commit()
    cursor.close()
    return tag_id

  def addbtag(self, book_id, tag_id):
    if not self.findbtag(book_id,tag_id):
       sql_addbtag=("insert into "+TBL_BTAGS+"(book_id,tag_id) VALUES(%s,%s)")
       data_addbtag=(book_id,tag_id)
       cursor=self.cnx.cursor()
       cursor.execute(sql_addbtag,data_addbtag)
       self.cnx.commit()
       cursor.close()

  def findauthor(self,first_name,last_name):
    sql_findauthor=("select author_id from "+TBL_AUTHORS+" where LOWER(first_name)=%s and LOWER(last_name)=%s")
    data_findauthor=(first_name.lower(),last_name.lower())
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
    self.cnx.commit()
    cursor.close()
    return author_id

  def addbauthor(self, book_id, author_id):
    if not self.findbauthor(book_id,author_id):
       sql_addbauthor=("insert into "+TBL_BAUTHORS+"(book_id,author_id) VALUES(%s,%s)")
       data_addbauthor=(book_id,author_id)
       cursor=self.cnx.cursor()
       cursor.execute(sql_addbauthor,data_addbauthor)
       self.cnx.commit()
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
    self.cnx.commit()
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
    sql_findbooks=("select book_id,filename, path, registerdate from "+TBL_BOOKS+" where cat_id="+str(cat_id)+" order by filename "+limitstr)
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
    sql_finditems=("select SQL_CALC_FOUND_ROWS 1,cat_id,cat_name,path,now(),cat_name as title, '' as genre from "+TBL_CATALOGS+" where parent_id="+str(cat_id)+" union all "
    "select 2,book_id,filename,path,registerdate,title,genre from "+TBL_BOOKS+" where cat_id="+str(cat_id)+" order by 1,6 "+limitstr)
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
    sql_getbook=("select filename, path, registerdate, format, title, cat_type, cover, cover_type from "+TBL_BOOKS+" where book_id="+str(book_id))
    cursor=self.cnx.cursor()
    cursor.execute(sql_getbook)
    row=cursor.fetchone()
    cursor.close
    return row

  def getauthors(self,book_id):
    sql=("select first_name,last_name from "+TBL_AUTHORS+" a, "+TBL_BAUTHORS+" b where b.author_id=a.author_id and b.book_id="+str(book_id))
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

#  def getauthor_letters(self):
#    sql="select UPPER(substring(last_name,1,1)) as letter, count(*) as cnt from "+TBL_AUTHORS+" group by 1 order by 1"
#    cursor=self.cnx.cursor()
#    cursor.execute(sql)
#    rows=cursor.fetchall()
#    cursor.close
#    return rows

  def getauthor_2letters(self,letters):
    lc=len(letters)+1
    sql="select UPPER(substring(trim(CONCAT(last_name,' ',first_name)),1,"+str(lc)+")) as letters, count(*) as cnt from "+TBL_AUTHORS+" where UPPER(substring(trim(CONCAT(last_name,' ',first_name)),1,"+str(lc-1)+"))='"+letters+"' group by 1 order by 1"
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

#  def gettitle_letters(self):
#    sql="select UPPER(substring(title,1,1)) as letter, count(*) as cnt from "+TBL_BOOKS+" group by 1 order by 1"
#    cursor=self.cnx.cursor()
#    cursor.execute(sql)
#    rows=cursor.fetchall()
#    cursor.close
#    return rows

  def gettitle_2letters(self,letters):
    lc=len(letters)+1
    sql="select UPPER(substring(trim(title),1,"+str(lc)+")) as letteris, count(*) as cnt from "+TBL_BOOKS+" where UPPER(substring(trim(title),1,"+str(lc-1)+"))='"+letters+"' group by 1 order by 1"
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getbooksfortitle(self,letters,limit=0,page=0):
    if limit==0:
       limitstr=""
    else:
       limitstr="limit "+str(limit*page)+","+str(limit)
    sql="select SQL_CALC_FOUND_ROWS book_id,filename,path,registerdate,title,genre,cover,cover_type from "+TBL_BOOKS+" where title like '"+letters+"%' order by title "+limitstr
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

  def getauthorsbyl(self,letters,limit=0,page=0):
    if limit==0:
       limitstr=""
    else:
       limitstr="limit "+str(limit*page)+","+str(limit)
    sql="select SQL_CALC_FOUND_ROWS a.author_id, a.first_name, a.last_name, count(*) as cnt from "+TBL_AUTHORS+" a, "+TBL_BAUTHORS+" b, "+TBL_BOOKS+" c where a.author_id=b.author_id and b.book_id=c.book_id and UPPER(a.last_name) like '"+letters+"%' group by 1,2,3 order by 3,2 "+limitstr
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

  def getbooksforautor(self,author_id,limit=0,page=0):
    if limit==0:
       limitstr=""
    else:
       limitstr="limit "+str(limit*page)+","+str(limit)
    sql="select SQL_CALC_FOUND_ROWS a.book_id,a.filename,a.path,a.registerdate,a.title,a.genre,a.cover,a.cover_type from "+TBL_BOOKS+" a, "+TBL_BAUTHORS+" b where a.book_id=b.book_id and b.author_id="+str(author_id)+" order by a.title "+limitstr
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
    sql="select book_id,filename,path,registerdate,title from "+TBL_BOOKS+" order by registerdate desc "+limitstr
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getgenres(self):
    sql="select lower(genre), count(*) from "+TBL_BOOKS+" group by 1 order by 1"
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    cursor.close
    return rows

  def getdbinfo(self):
    sql="select count(*) from %s union select count(*) from %s union select count(*) from %s"%(TBL_BOOKS,TBL_AUTHORS,TBL_CATALOGS)
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    rows=cursor.fetchall()
    return rows
  
  def zipisscanned(self,zipname):
    sql='select cat_id from '+TBL_CATALOGS+' where path="'+zipname+'" limit 1'
    cursor=self.cnx.cursor()
    cursor.execute(sql)
    row=cursor.fetchone()
    if row==None:
       cat_id=0
    else:
       cat_id=row[0]
    return cat_id

  def __del__(self):
    self.closeDB()

