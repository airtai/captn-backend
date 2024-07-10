from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import patch

import pytest


@pytest.fixture()
@contextmanager
def mock_get_conv_uuid() -> Iterator[Any]:
    with patch(
        "captn.captn_agents.backend.teams._gbb_google_sheets_team.get_conv_uuid",
        return_value="abcd-efgh-ijkl",
    ) as mock_get_conv_uuid:
        yield mock_get_conv_uuid
