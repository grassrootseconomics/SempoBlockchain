# standard imports
import logging

# platform imports
import config
from files.s3 import S3


logg = logging.getLogger(__file__)

def init():
    locale_syncer = S3('sarafu-resources', config.SYSTEM_LOCALE_PATH, key=config.AWS_SES_KEY_ID, secret=config.AWS_SES_SECRET)
    r = locale_syncer.sync([
        'general_sms.en.yml',
        'general_sms.sw.yml',
        'ussd.en.yml',
        'ussd.sw.yml',
        ])

    for f in r:
        logg.info('synced locale file: {}'.format(f))

if __name__ == "__main__":
    init()
