from celery.schedules import crontab
from bonuses.utils import celery_app
from bonuses import bonus_tasks


celery_app.conf.beat_schedule = {
    'manage-scheduled-bonus-issuance': {
        'task': 'bonuses.bonus_tasks.auto_disburse_daily_bonus',
        'schedule': crontab(minute=50, hour=23)
    },
}
