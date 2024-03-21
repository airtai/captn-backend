import unittest
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from openai_agent.application import _get_openai_response

TEST_CONTENT = "This is a test content"


async def mock_chat_completion(*args: Any, **kwargs: Any) -> MagicMock:
    mock_completion = MagicMock()
    mock_completion.id = "1"
    mock_completion.choices = [
        MagicMock(
            finish_reason="function_call",
            index=0,
            message=MagicMock(
                content=TEST_CONTENT,
                role="assistant",
                function_call=None,
                tool_calls=None,
            ),
            content_filter_results={},
        )
    ]
    return mock_completion


message = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Who are you"},
]


@pytest.mark.asyncio
async def test_openai_function_calling() -> None:
    with unittest.mock.patch(
        "openai_agent.application.aclient.chat.completions.create",
        side_effect=mock_chat_completion,  # type: ignore
    ) as mock_create:
        actual = await _get_openai_response(
            user_id=1, chat_id=1, message=message, background_tasks=Mock()
        )

        expected = {"content": TEST_CONTENT}

        assert mock_create.call_count == 1
        assert actual == expected
