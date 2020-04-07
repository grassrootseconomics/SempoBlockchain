#!/usr/bin/env bash

#echo cheese

celery -A eth_manager beat --loglevel=WARNING

#-A worker worker --loglevel=INFO --concurrency=500 --pool=eventlet