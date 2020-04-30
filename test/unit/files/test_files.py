# standard imports
import os
import uuid

# third party imports
import pytest

# platform imports
import config
from files.sync import FileSyncer
from files.s3 import S3


def test_files():
    uu = str(uuid.uuid4())
    randomfilename = '/tmp/' + uu + '/foo'
    fs = S3('sarafu-tests', randomfilename)
    fs = FileSyncer('.', '/tmp/' + randomfilename + '/foo', None)
    fs.sync([])

@pytest.mark.skipif(getattr(config, 'AWS_SES_KEY_ID', None)==None, reason='aws not set up, skipping s3 test')
def test_s3():
    uu = str(uuid.uuid4())
    randomfilename = '/tmp/' + uu + '/foo'
    fs = S3('sarafu-tests', randomfilename)
    remote_files = ['foo.txt', 'bar.txt']
    r = fs.sync(remote_files)
    for f in remote_files:
        assert(f in r)
