import unittest
from typing import Any
from unittest.mock import MagicMock

import pytest

from captn.captn_agents.model import SmartSuggestions
from openai_agent.smart_suggestion_generator import (
    _format_conversation,
    generate_smart_suggestions,
)

test_smart_suggestions = {"suggestions": [""], "type": "oneOf"}
TEST_CONTENT = SmartSuggestions(**test_smart_suggestions).model_dump()


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
    with (
        unittest.mock.patch(
            "openai_agent.smart_suggestion_generator.aclient.chat.completions.create",
            side_effect=mock_chat_completion,
        ) as mock_create,
        unittest.mock.patch(
            "openai_agent.smart_suggestion_generator._send_to_client"
        ) as mock_send_to_client,
    ):
        await generate_smart_suggestions(message=message, chat_id=1)

        assert mock_create.call_count == 1
        mock_send_to_client.assert_called_once_with(TEST_CONTENT, 1)


def test_format_conversation() -> None:
    messages = [
        {
            "role": "assistant",
            "content": """Welcome aboard! I'm Captn, your digital marketing companion.
            Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing.
            Before we set sail, could you steer our course by sharing the business goal you'd like to improve?""",
        },
        {"role": "user", "content": "I want to Boost sales"},
        {
            "role": "assistant",
            "content": "Awesome goal! Let's set sail and boost your sales.",
        },
        {"role": "user", "content": "Am excited to get started!"},
    ]
    expected = """chatbot: Welcome aboard! I'm Captn, your digital marketing companion.
            Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing.
            Before we set sail, could you steer our course by sharing the business goal you'd like to improve?
customer: I want to Boost sales
chatbot: Awesome goal! Let's set sail and boost your sales.
customer: Am excited to get started!"""
    actual = _format_conversation(messages)
    assert actual == expected
