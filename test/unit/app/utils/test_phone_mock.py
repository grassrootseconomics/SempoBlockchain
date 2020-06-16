import pytest

from server.utils.phone import send_message

def test_fs_message(test_client):
    send_message('+12345678', 'foo')
