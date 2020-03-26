from bonuses.utils import celery_app
from bonuses.bonus_processor import BonusProcessor


@celery_app.task()
def auto_disburse_daily_bonus():
    bonus_processor = BonusProcessor(issuable_amount=1000)
    return bonus_processor.auto_disburse_amount()
