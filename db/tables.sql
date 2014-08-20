SET NAMES 'utf8';
SET CHARACTER SET utf8;

drop table if exists books;
create table books (
book_id INT not null AUTO_INCREMENT,
filename VARCHAR(256),
path VARCHAR(1024),
filesize INT not null DEFAULT 0,
format VARCHAR(8),
cat_id INT not null,
cat_type INT not null DEFAULT 0,
registerdate TIMESTAMP not null DEFAULT CURRENT_TIMESTAMP,
docdate VARCHAR(20),
favorite INT not null DEFAULT 0,
lang  VARCHAR(16),
title VARCHAR(256),
annotation VARCHAR(10000),
cover VARCHAR(32),
cover_type VARCHAR(32),
doublicat INT not null DEFAULT 0,
avail INT not null DEFAULT 0,
PRIMARY KEY(book_id),
KEY(filename),
KEY(title,format,filesize),
INDEX(path),
INDEX(cat_id),
INDEX(avail,doublicat),
INDEX(registerdate));
commit;

drop table if exists catalogs;
create table catalogs (
cat_id INT not null AUTO_INCREMENT,
parent_id INT null,
cat_name VARCHAR(64),
path VARCHAR(1024),
cat_type INT not null DEFAULT 0,
PRIMARY KEY(cat_id),
KEY(cat_name,path(256)));
commit;

drop table if exists authors;
create table authors (
author_id INT not null AUTO_INCREMENT,
first_name VARCHAR(64),
last_name VARCHAR(64),
PRIMARY KEY(author_id),
KEY(last_name,first_name));
commit;

drop table if exists bauthors;
create table bauthors (
author_id INT not NULL,
book_id INT not NULL,
PRIMARY KEY(book_id,author_id),
INDEX(author_id));
commit;

drop table if exists genres;
create table genres(
genre_id INT not null AUTO_INCREMENT,
genre VARCHAR(32),
section VARCHAR(64),
subsection VARCHAR(100),
PRIMARY KEY(genre_id),
KEY(genre));
commit;

drop table if exists bgenres;
create table bgenres(
genre_id INT not NULL,
book_id INT not NULL,
PRIMARY KEY(book_id,genre_id),
INDEX(genre_id));
commit;

drop table if exists series;
create table series(
ser_id INT not null AUTO_INCREMENT,
ser VARCHAR(64),
PRIMARY KEY(ser_id),
KEY(ser));
commit;

drop table if exists bseries;
create table bseries(
ser_id INT not NULL,
book_id INT not NULL,
ser_no TINYINT UNSIGNED NOT NULL DEFAULT 0,
PRIMARY KEY(book_id,ser_id),
INDEX(ser_id));
commit;

drop table if exists bookshelf;
create table bookshelf(
user VARCHAR(32) not NULL,
book_id INT not NULL,
readtime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
INDEX(user,readtime));
commit;

drop table if exists dbver;
create table dbver(
ver varchar(5));
commit;

insert into dbver(ver) values("0.21");
commit;
insert into authors(author_id,last_name,first_name) values(1,"Неизвестный Автор","");
commit;

DROP PROCEDURE IF EXISTS sp_update_dbl;
DROP PROCEDURE IF EXISTS sp_newinfo;
DROP FUNCTION IF EXISTS BOOK_CMPSTR;
DROP PROCEDURE IF EXISTS sp_mark_dbl;
DELIMITER //

CREATE FUNCTION BOOK_CMPSTR(id INT, cmp_type INT)
RETURNS VARCHAR(512)
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE T VARCHAR(256);
  DECLARE fmt VARCHAR(8) DEFAULT '';
  DECLARE fsize INT DEFAULT 0;
  DECLARE AUTHORS VARCHAR(256) DEFAULT '';
  DECLARE RESULT VARCHAR(512);
  SELECT GROUP_CONCAT(DISTINCT author_id order by author_id SEPARATOR ':') into AUTHORS from bauthors where book_id=id;
  IF AUTHORS=NULL THEN
     SET AUTHORS='';
  END IF;

  SELECT UPPER(trim(REPLACE(title,' ',''))),format,filesize INTO T,fmt,fsize FROM books WHERE book_id=id;
  IF T=NULL THEN
     SET T='';
  END IF;

  IF cmp_type=1 THEN
     SET RESULT=CONCAT_WS(':',T,AUTHORS);
  ELSEIF cmp_type=2 THEN
     SET RESULT=CONCAT_WS(':',T,fsize,fmt);
  ELSE
     SET RESULT='';
  END IF;

  RETURN RESULT; 
END //

CREATE PROCEDURE sp_mark_dbl(cmp_type INT)
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE idx,prev,current,orig_id INT;
  DECLARE ids VARCHAR(512);
  DECLARE cur CURSOR for select GROUP_CONCAT(DISTINCT book_id order by filesize DESC SEPARATOR ':') as ids 
                      from books where avail<>0 group by BOOK_CMPSTR(book_id,cmp_type) having SUM(IF(doublicat=0,1,0))<>1;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  IF cmp_type=1 or cmp_type=2 THEN
     OPEN cur;

     WHILE done=0 DO
       FETCH cur INTO ids;
       IF done=0 THEN
          set idx=0;
          set prev=-1;
          set current=0;
          set orig_id=0;
          WHILE prev<>current DO
              set prev=current;
              set idx=idx+1;
              SELECT CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(ids,':',idx),':',-1) as UNSIGNED) into current;
              IF prev<>current THEN
                 UPDATE books SET doublicat=orig_id where book_id=current;
                 if orig_id=0 THEN SET orig_id=current; END IF;
              END IF;
          END WHILE;
       END IF;
     END WHILE;  
     CLOSE cur;
  END IF;

  IF cmp_type=3 THEN
     UPDATE books SET doublicat=0;
  END IF;

END //

CREATE PROCEDURE sp_newinfo(period INT)
BEGIN
  DECLARE min_book_id INT;

  select MIN(book_id) into min_book_id from books where registerdate>now()-INTERVAL period DAY;
  select 1 s, count(*) from books where book_id>=min_book_id and avail!=0 and doublicat=0
  union all
  select 2 s, count(*) from (select author_id from bauthors where book_id>=min_book_id group by author_id) a
  union all
  select 3 s, count(*) from (select genre_id from bgenres where book_id>=min_book_id group by genre_id) a
  union all
  select 4 s, count(*) from (select ser_id from bseries where book_id>=min_book_id group by ser_id) a
  order by s;

END //


DELIMITER ;
commit;

