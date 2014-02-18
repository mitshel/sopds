create database if not exists sopds default charset=utf8;
grant select,insert,update,delete,execute on sopds.* to 'sopds'@'localhost' identified by 'sopds';
commit;
