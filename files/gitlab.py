"""
Use git repository to retrieve files.
"""

# standard imports
import base64
import io
import logging
import requests

from urllib.parse import quote

# platform imports
import config
from files.sync import FileSyncer

logg = logging.getLogger(__name__)


class Gitlab(FileSyncer):
    """
    Provides access to files stored on a git repository.
    This class takes a destination path that defines where to write the files from Gitlab.
    """

    def __init__(self, destination_path, source_path):
        super(Gitlab, self).__init__(source_path, destination_path, getfunc=self.get_files)
        self.destination_path = destination_path

    def source_is_newer(self, filepath):
        return True

    def get_files(self, filename: str):
        """
        This function issues a get request for the file from the Gitlab Files API and returns a string containing the file's
        data. It then collects the file content and the last commit id for the files repo.
        :param filename: The name of the file to retrieve from the repo
        :return: string
        """
        reader = None

        # encode filename
        url_encoded_filename = quote(f'/{filename}', safe='').replace('.', '%2E')
        logg.debug(f'Gitlab file sync callback get {filename} from {config.GITLAB_BRANCH}')
        try:
            # build gitlab API url of the format
            # https://gitlab.example.com/api/v4/projects/13083/repository/files/app%2Fmodels%2Fkey%2Erb?ref=master
            url = f'{config.GITLAB_SCHEME}://{config.GITLAB_HOST}{config.GITLAB_URL_PATH}{config.GITLAB_PROJECT_ID}{self.source_path}{url_encoded_filename}?ref={config.GITLAB_BRANCH}'
            response = requests.get(url=url,
                                    headers={
                                        'PRIVATE-TOKEN': config.GITLAB_PRIVATE_TOKEN,
                                        'Accept': 'application/json'
                                    },
                                    timeout=10)
            result_json = response.json()
            # get content
            base64_encoded_content = result_json['content']
            # decode base64 encoded
            reader = io.BytesIO(base64.b64decode(base64_encoded_content))
        except Exception as exception:
            raise Exception(exception)
        return reader
