"""Sync all internal and external resources before start.

TODO: move file fetching from config.py in here
"""

# standard imports
import logging

# platform imports
import config
from files.gitlab import Gitlab

logg = logging.getLogger(__file__)


def init():
    """Initializes the system

    Raises
    ------
    Exception
        Any exception raised should result in immediate termination
    """

    locale_syncer = Gitlab(source_path=config.GITLAB_FILEPATH, destination_path=config.SYSTEM_LOCALE_PATH)

    r = locale_syncer.sync([
        'general_sms.en.yml',
        'general_sms.sw.yml',
        'ussd.en.yml',
        'ussd.sw.yml',
        ])

    for f in r:
        logg.info('synced locale file: {}'.format(f))


# In certain cases, for example a docker invocation script,
# init may be called directly from the command line
if __name__ == "__main__":
    init()
