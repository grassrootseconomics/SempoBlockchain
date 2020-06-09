"""
Use git repository to retrieve files.
"""

# standard imports
import base64
import logging
import requests

# platform imports
import config
from files.sync import FileSyncer

github_files_logger = logging.getLogger(__name__)


def get_files(filename):
    from urllib.parse import quote
    content, last_commit_id = None, None
    url_encoded_filename = quote(filename, safe='').replace('.', '%2E')
    github_files_logger.debug(f'Gitlab file sync callback get {filename} from {config.GITLAB_BRANCH}')
    try:
        file_fetcher_url = f'{config.GITLAB_FILE_FETCHER_BASE_URL}{url_encoded_filename}?ref={config.GITLAB_BRANCH}'
        response = requests.get(url=file_fetcher_url,
                                headers={
                                    'PRIVATE-TOKEN': config.GITLAB_PRIVATE_TOKEN,
                                    'Accept': 'application/json'
                                },
                                timeout=10)
        result_json = response.json()
        # decode base64 encoded
        base64_encoded_content = result_json['content']
        content = base64.b64decode(base64_encoded_content)
        last_commit_id = result_json['last_commit_id']
    except Exception as exception:
        raise Exception(exception)
    return content, last_commit_id


class Gitlab(FileSyncer):
    """
    Provides access to files stored on a git repository.
    """

    def __init__(self, destination_path):
        super(Gitlab, self).__init__(destination_path, get_files_func=get_files)
        self.destination_path = destination_path
