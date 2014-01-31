grant execute on sopds.* to 'sopds'@'localhost' identified by 'sopds';
DROP PROCEDURE IF EXISTS sp_update_dbl;
DELIMITER //

CREATE PROCEDURE sp_update_dbl()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE id, dbl INT;
  DECLARE dbl_sav, id_sav INT;
  DECLARE cur CURSOR FOR select book_id, doublicat from books 
                         where doublicat!=0 and avail!=0 and doublicat not in 
                         (select book_id from books where doublicat=0 and avail=2) order by doublicat, book_id;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  OPEN cur;

  SET dbl_sav=0;
  SET id_sav=0;  
  WHILE done=0 DO
    FETCH cur INTO id, dbl;
    IF dbl_sav!=dbl THEN
       UPDATE books SET doublicat=0 WHERE book_id=id;
       SET dbl_sav=dbl;
       SET id_sav=id;
    ELSE
       UPDATE books SET doublicat=id_sav where book_id=id;
    END IF;
  END WHILE;

  CLOSE cur;
END //

DELIMITER ;

commit;

