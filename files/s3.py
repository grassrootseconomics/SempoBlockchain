# third party imports
import boto3

# platform imports
from files.sync import FileSyncer

class S3(FileSyncer):

    def source_is_newer(self, filepath):
        return True

    def _getfunc(self, item):
        reader = None
        try:
            response = self.session.Object(bucket_name = self.source_path, key = item)
            reader = response.get()['Body']
        # TODO: docs don't mention this as exception, is "errorfactory instance" - dunno how to catch, so we will have to catch all for now
        except Exception as e:
            raise KeyError(e)
        return reader

    def __init__(self, source_path, destination_path):
        super(S3, self).__init__(source_path, destination_path, self._getfunc)
        self.session = boto3.resource('s3')
