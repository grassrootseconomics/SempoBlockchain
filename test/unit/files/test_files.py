# standard imports
import uuid

# platform imports
from files.sync import FileSyncer


# TODO: add test for files received

def test_files():
    randomfilename = str(uuid.uuid4())
    fs = FileSyncer('.', '/tmp/' + randomfilename + '/foo', None)
    fs.sync([])

