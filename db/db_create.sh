#!/bin/bash

run_path=`dirname $0`
script_db=$run_path'/db.sql'
script_tables=$run_path'/tables.sql'
script_genres=$run_path'/genres.sql'

mysql mysql < $script_db
mysql sopds < $script_tables
mysql sopds < $script_genres
