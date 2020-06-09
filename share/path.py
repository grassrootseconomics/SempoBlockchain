# standard import
import os
import logging

logg = logging.getLogger()


def reverse_split(path):
    """Returns the given path as array elements, omitting empty parts

    Parameters
    ----------
    path : string
        a path string 

    Returns
    -------
    path_parts : list
        resulting elements
    """

    path_parts = []

    (head, tail) = os.path.split(path.strip('/'))
    while not (tail == '' and head == ''):
        path_parts.append(tail)
        (head, tail) = os.path.split(head)
    path_parts.reverse()
    return path_parts
