import unittest

import pytest
from requests.models import Response

from captn.google_ads.client import (
    ALREADY_AUTHENTICATED,
    AUTHENTICATION_ERROR,
    execute_query,
)


def test_execute_query_when_authentication_error_occurs_raises_value_error() -> None:
    with unittest.mock.patch(
        "captn.google_ads.client.get_login_url",
    ) as mock_get_login_url:
        with unittest.mock.patch(
            "requests_get",
        ) as mock_requests_get:
            mock_get_login_url.return_value = {"login_url": ALREADY_AUTHENTICATED}

            response = Response()
            response.status_code = 500
            response._content = b'{"detail":"Please try to execute the command again."}'
            mock_requests_get.return_value = response

            with pytest.raises(ValueError) as exc_info:
                execute_query(user_id=-1, conv_id=-1)

            assert exc_info.value.args[0] == AUTHENTICATION_ERROR
