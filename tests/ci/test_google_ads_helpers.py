import unittest
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from prisma.engine.errors import EngineConnectionError

from captn.captn_agents import helpers


@pytest.mark.asyncio
async def test_retry_context_manager() -> None:
    mock_cm = MagicMock()
    mock_cm_instance = mock_cm.return_value
    mock_cm_instance.__aenter__ = AsyncMock()
    mock_cm_instance.__aexit__ = AsyncMock()

    mock_cm_instance.__aenter__.side_effect = [ValueError("Always fails")] * 4 + [1]

    mock_cm = helpers.retry_context_manager(num_retries=6)(mock_cm)

    async with mock_cm() as ret_val:
        pass

    assert ret_val == 1, ret_val
    assert (
        mock_cm_instance.__aenter__.call_count == 5
    ), mock_cm_instance.__aenter__.call_count
    assert (
        mock_cm_instance.__aexit__.call_count == 1
    ), mock_cm_instance.__aexit__.call_count


@pytest.mark.asyncio
async def test_get_db_connection_retry() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.helpers.Prisma",
    ) as mock_prisma:
        mock_prisma_instance = AsyncMock()
        mock_prisma.return_value = mock_prisma_instance

        side_effects = [
            EngineConnectionError("Goodle Ads API exception"),
            EngineConnectionError("Goodle Ads API exception"),
            "return value",
        ]

        def side_effect(*args: Any, **kwargs: Any) -> Any:
            value = side_effects.pop(0)
            if isinstance(value, Exception):
                raise value
            return value

        mock_prisma_instance.connect.side_effect = side_effect

        async with helpers.get_db_connection():
            pass

        assert mock_prisma_instance.connect.call_count == 3
        assert mock_prisma_instance.disconnect.call_count == 1
