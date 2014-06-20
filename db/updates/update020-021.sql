update dbver set ver="0.21";
DROP PROCEDURE IF EXISTS sp_update_dbl;
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

DELIMITER ;
commit;



