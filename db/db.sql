create database if not exists sopds default charset=utf8;
grant all on sopds.* to 'sopds'@'localhost' identified by 'sopds';
commit;
