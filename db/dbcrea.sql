drop database sopds;
commit;
create database sopds;
alter database sopds CHARSET utf8;
grant select,insert,update,delete on sopds.* to 'sopds'@'localhost' identified by 'sopds';
use sopds;

create table books (
book_id INT not null AUTO_INCREMENT,
filename VARCHAR(256),
path VARCHAR(1024),
filesize INT not null DEFAULT 0,
format VARCHAR(8),
cat_id INT not null,
cat_type INT not null DEFAULT 0,
cat_tree VARCHAR(512),
registerdate TIMESTAMP not null DEFAULT CURRENT_TIMESTAMP,
favorite INT not null DEFAULT 0,
genre VARCHAR(32),
lang  VARCHAR(16),
title VARCHAR(256),
cover VARCHAR(32),
cover_type VARCHAR(32),
doublicat INT not null DEFAULT 0,
PRIMARY KEY(book_id),
KEY(filename),
KEY(cat_tree),
KEY(genre),
KEY(title));

create table catalogs (
cat_id INT not null AUTO_INCREMENT,
parent_id INT null,
cat_name VARCHAR(64),
path VARCHAR(1024),
cat_type INT not null DEFAULT 0,
PRIMARY KEY(cat_id),
KEY(cat_name,path));

create table tags (
tag_id INT not null AUTO_INCREMENT,
tag_type INT not null DEFAULT 0,
tag VARCHAR(64),
PRIMARY KEY(tag_id),
KEY(tag));

create table btags (
tag_id INT not null,
book_id INT not null,
PRIMARY KEY(book_id,tag_id));

create table authors (
author_id INT not null AUTO_INCREMENT,
first_name VARCHAR(64),
last_name VARCHAR(64),
PRIMARY KEY(author_id),
KEY(last_name,first_name));

create table bauthors (
author_id INT not NULL,
book_id INT not NULL,
PRIMARY KEY(book_id,author_id));

insert into authors(author_id,last_name) values(1,"Неизвестный Автор");

commit;




