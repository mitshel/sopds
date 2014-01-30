#!/bin/bash

script_dbcrea='dbcrea.sql'
script_genre='genre.sql'
run_path=`dirname $0`
script_dbcrea=$run_path'/dbcrea.sql'
script_genres=$run_path'/genres.sql'
script_sp=$run_path'/sp_update_dbl.sql'

mysql mysql < $script_dbcrea
mysql sopds < $script_genres
mysql sopds < $script_sp
