import pytest
import logging

logg = logging.getLogger()

def test_sms_list(test_client):
    response = test_client.get(
            '/api/v2/sms/',
            headers=dict(
                Accept='text/plain',
                ),
            )
    logg.debug(response.data.decode('utf-8'))
