# platform imports
import config
from files.s3 import S3

def init():
    locale_syncer = S3('sarafu-resources', config.SYSTEM_LOCALE_PATH)
    locale_syncer.sync([
        'general_sms.en.yml',
        'general_sms.sw.yml',
        'ussd.en.yml',
        'ussd.sw.yml',
        ])
