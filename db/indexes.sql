# Скрипт для обновления БД версии 0.10 до версии 0.10.1
# Начиная с версии 0.10.1 выполнять этот скрипт не нужно
# т.к. все необходимые индексы будут созданы скриптом db_create.sh

create index idx_bauthors_aid on bauthors (author_id);
create index idx_bgenres_gid on bgenres (genre_id);
