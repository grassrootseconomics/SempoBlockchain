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
            response = self.session.get_object(
                    Bucket=self.source_path,
                    Key=item
                    )
            reader = response['Body']
        # TODO: docs don't mention this as exception, is "errorfactory instance" - dunno how to catch, so we will have to catch all for now
        except Exception as e:
            raise KeyError(e)
        return reader

    def __init__(self, source_path, destination_path, key=None, secret=None):
        super(S3, self).__init__(source_path, destination_path, self._getfunc)
        session = boto3.Session(
            aws_access_key_id       = key,
            aws_secret_access_key   = secret,
        )
        self.session = session.client('s3')
