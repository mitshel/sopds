update dbver set ver="0.15";
update authors set first_name="" where author_id=1;

drop table if exists bookshelf;
create table bookshelf(
user VARCHAR(32) not NULL,
book_id INT not NULL,
readtime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
INDEX(user,readtime));
commit;

DROP PROCEDURE IF EXISTS sp_newinfo;

DELIMITER //

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

