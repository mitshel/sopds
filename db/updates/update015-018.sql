update dbver set ver="0.18";
create index idx_path on books(path);
commit;

