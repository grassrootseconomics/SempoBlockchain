#!/usr/bin/env bash

echo ~~~~Resetting postgres
db_server=postgres://${DB_USER:-postgres}:${DB_PASSWORD:-password}@localhost:5432
app_db=$db_server/${APP_DB:-sempo_blockchain_local}
eth_worker_db=$db_server/${APP_DB:-eth_worker}

psql $app_db -c 'DROP SCHEMA public CASCADE'
psql $app_db -c 'CREATE SCHEMA public'

psql $eth_worker_db -c 'DROP SCHEMA public CASCADE'
psql $eth_worker_db -c 'CREATE SCHEMA public'


cd ../app || exit
python manage.py db upgrade

cd ../eth_worker/ || exit
alembic upgrade heads