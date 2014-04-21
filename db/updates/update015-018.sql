update dbver set ver="0.18";
create index idx_path on books(path);
create index idx_cat0 on catalogs(cat_name,path);
create index idx_books_catid on books(cat_id);
commit;

