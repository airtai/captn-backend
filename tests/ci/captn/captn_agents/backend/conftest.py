import random
import unittest
from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest

from captn.google_ads.client import ALREADY_AUTHENTICATED

from .fixtures.google_sheets_team import ads_values, campaigns_values, keywords_values


@contextmanager
@pytest.fixture()
def mock_get_login_url() -> Iterator[Any]:
    with unittest.mock.patch(
        "captn.google_ads.client.get_login_url",
        return_value={"login_url": ALREADY_AUTHENTICATED},
    ) as mock_get_login_url:
        yield mock_get_login_url


@contextmanager
@pytest.fixture()
def mock_requests_get() -> Iterator[Any]:
    with unittest.mock.patch(
        "captn.google_ads.client.requests_get",
        return_value=MagicMock(),
    ) as mock_requests_get:
        mock_requests_get.return_value.ok = True
        mock_requests_get.return_value.json.side_effect = [
            f"Created resource/{random.randint(100, 1000)}"  # nosec: [B311]
            for _ in range(200)
        ]
        yield mock_requests_get


@pytest.fixture()
def mock_get_sheet_data() -> Iterator[Any]:
    with unittest.mock.patch(
        "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools._get_sheet_data",
        side_effect=[
            campaigns_values,
            ads_values,
            keywords_values,
        ],
    ) as mock_get_sheet_data:
        yield mock_get_sheet_data
