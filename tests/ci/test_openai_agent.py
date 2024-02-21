import os
import unittest
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from openai_agent.application import (
    _format_proposed_user_action,
    _get_message_as_string,
    _get_openai_response,
)

os.environ["AZURE_OPENAI_API_KEY"] = "dummy"

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

        expected = {"content": TEST_CONTENT, "smart_suggestions": [""]}

        assert mock_create.call_count == 4
        assert actual == expected


def test_format_proposed_user_action() -> None:
    proposed_user_action = [
        'Remove "Free" keyword because it is not performing well',
        "Increase budget from $10/day to $20/day",
        'Remove the headline "New product" and replace it with "Very New product" in the "Adgroup 1"',
        "Select some or all of them",
    ]
    actual = _format_proposed_user_action(proposed_user_action)
    expected = """1. Remove "Free" keyword because it is not performing well
2. Increase budget from $10/day to $20/day
3. Remove the headline "New product" and replace it with "Very New product" in the "Adgroup 1"
4. Select some or all of them"""
    assert actual == expected


def test_get_message_as_string() -> None:
    message = [
        {
            "role": "agent",
            "content": """Below is your daily analysis for 29-Jan-24

Your campaigns have performed yetserday:
 - Clicks:         124 clicks ( +3.12%)
 - Spend:           $6.54 USD ( -1.12%)
 - Cost per click:  $0.05 USD (+12.00%)

### Proposed User Action ###
1. Remove "Free" keyword because it is not performing well
2. Increase budget from $10/day to $20/day
3. Remove the headline "New product" and replace it with "Very New product" in the "Adgroup 1"
4. Select some or all of them""",
        },
        {
            "role": "user",
            "content": 'Remove "Free" keyword because it is not performing well',
        },
    ]
    proposed_user_action = [
        'Remove "Free" keyword because it is not performing well',
        "Increase budget from $10/day to $20/day",
        'Remove the headline "New product" and replace it with "Very New product" in the "Adgroup 1"',
        "Select some or all of them",
    ]
    agent_chat_history = '[{"role": "agent", "content": "Here is the summary"},{"role": "agent", "content": "Here is the report"},{"role": "user", "content": "proceed"}]'
    actual = _get_message_as_string(message, proposed_user_action, agent_chat_history)
    expected = """
### History ###
This is the JSON encoded history of your conversation that made the Daily Analysis and Proposed User Action. Please use this context and continue the execution according to the User Action:

[{"role": "agent", "content": "Here is the summary"},{"role": "agent", "content": "Here is the report"},{"role": "user", "content": "proceed"}]

### Daily Analysis ###
Below is your daily analysis for 29-Jan-24

Your campaigns have performed yetserday:
 - Clicks:         124 clicks ( +3.12%)
 - Spend:           $6.54 USD ( -1.12%)
 - Cost per click:  $0.05 USD (+12.00%)

### Proposed User Action ###
1. Remove "Free" keyword because it is not performing well
2. Increase budget from $10/day to $20/day
3. Remove the headline "New product" and replace it with "Very New product" in the "Adgroup 1"
4. Select some or all of them

### User Action ###
Remove "Free" keyword because it is not performing well

"""
    assert actual == expected
