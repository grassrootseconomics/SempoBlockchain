#!/usr/bin/env bash

cd src
echo upgrading database
python manage.py db upgrade

ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi

echo upgrading dataset
python manage.py update_data

echo updating resource files
python init.py

ret=$?
if [ "$ret" -ne 0 ]; then
  exit $ret
fi

if [ "$CONTAINER_MODE" = 'TEST' ]; then
   #todo(COVERAGE): fix so that eth_worker is included
   coverage run invoke_tests.py
   ret=$?
   if [ "$ret" -ne 0 ]; then
     exit $ret
   fi
   bash <(curl -s https://codecov.io/bash) -cF python
elif [ "$CONTAINER_MODE" = 'SEED' ]; then
  echo seeding database
  # python seed.py
  # python dev_data.py
  uwsgi --socket 0.0.0.0:9000 --protocol http  --processes 4 --enable-threads --module=server.wsgi:app --stats :3031 --stats-http
else
  uwsgi --socket 0.0.0.0:9000 --protocol http  --processes 4 --enable-threads --module=server.wsgi:app --stats :3031 --stats-http
fi

