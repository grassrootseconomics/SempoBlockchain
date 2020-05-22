# standard import
import os
import logging

logg = logging.getLogger()


def reverse_split(path):
    path_parts = []

    (head, tail) = os.path.split(path.strip('/'))
    while not (tail == '' and head == ''):
        logg.debug('{}: {} {}'.format(path, head, tail))
        path_parts.append(tail)
        (head, tail) = os.path.split(head)
    logg.debug('parts {}'.format(path_parts))
    path_parts.reverse()
    return path_parts
