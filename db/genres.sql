use sopds;
SET NAMES 'utf8';
SET CHARACTER SET utf8;
drop table if exists genres;
drop table if exists bgenres;
commit;

create table genres(
genre_id INT not null AUTO_INCREMENT,
genre VARCHAR(32),
section VARCHAR(32),
subsection VARCHAR(32),
PRIMARY KEY(genre_id),
KEY(genre));
commit;

create table bgenres(
genre_id INT not NULL,
book_id INT not NULL,
PRIMARY KEY(book_id,genre_id),
