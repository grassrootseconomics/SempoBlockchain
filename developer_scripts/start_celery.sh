#!/usr/bin/env bash
cd ../eth_worker || exit
celery -A eth_manager worker --loglevel=INFO --concurrency=8 --pool=eventlet -Q processor,celery