import sys

from celery import Celery

sys.path.append('..')
import config

celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')
