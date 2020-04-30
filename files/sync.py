# standard imports
import os
import logging

logg = logging.getLogger(__file__)

class FileSyncer:

    blocksize = 1024

    # TODO: currently noop, should check whether files are changed at source
    def source_is_newer(self, filepath: str) -> bool:
        pass

    def sync(self, files: list) -> list:
        updated_files = []
        if not os.path.exists(self.destination_path):
            os.mkdir(self.destination_path)
        for f in files:
            if self.source_is_newer(f):
                fo = open(self.destination_path + '/' + f, 'wb')
                r = self.getfunc(f)
                while 1:
                    data = r.read(self.blocksize)
                    if not data:
                        break
                    fo.write(data)
                r.close()
                fo.close()
                updated_files.append(f)

        return updated_files
    
    def __init__(self, source_path, destination_path, getfunc):
        self.source_path = source_path
        self.destination_path = destination_path
        self.getfunc = getfunc
