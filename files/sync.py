"""External file retrieval
"""

# standard imports
import os
import logging

# platform imports
import config

file_sync_logger = logging.getLogger(__file__)


def source_newer(last_commit_id):
    if last_commit_id != config.GITLAB_LAST_COMMIT_ID:
        return True
    return False


class FileSyncer:
    """

    """
    def __init__(self, destination_path, get_files_func):
        self.destination_path = destination_path
        self.get_files_func = get_files_func

    def sync(self, files: list) -> list:
        """

        :param files: a list of files to be loaded from external resource
        :return:
        """

        updated_files = []
        os.makedirs(self.destination_path, 0o777, exist_ok=True)
        for file in files:
            file_stream = open(self.destination_path + '/' + file, 'wb')
            content, last_commit_id = self.get_files_func(file)
            if source_newer(last_commit_id):
                file_stream.write(content)
                file_stream.close()
                updated_files.append(file)
            break

        return updated_files
