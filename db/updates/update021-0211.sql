update dbver set ver="0.211";
alter table genres modify section VARCHAR(64), modify subsection VARCHAR(100);
\. ../genresupd.sql
commit;

