import asyncio
from typing import Dict, Union
from unittest.mock import patch

import pytest

from captn.captn_agents.backend.teams_manager import (
    TEAM_EXCEPTION_MESSAGE,
    get_team_status,
    teams_handler,
)


def mock_chat_with_team_exception(message: str, user_id: int, chat_id: int) -> None:
    raise Exception("Simulated exception from chat_with_team")


@pytest.mark.asyncio
async def test_exception_scenario() -> None:
    with patch(
        "captn.captn_agents.backend.teams_manager.chat_with_team",
        side_effect=mock_chat_with_team_exception,
    ):
        chat_id = 10000
        message = "Some message"
        team_name = "Google Ads Team"
        user_id = 1

        teams_handler(user_id, chat_id, team_name, message)

        # Initially, the status should be inprogress
        await asyncio.sleep(1)
        result = await get_team_status(chat_id)
        assert result == {
            "team_id": chat_id,
            "user_id": user_id,
            "team_name": team_name,
            "team_status": "completed",
            "msg": TEAM_EXCEPTION_MESSAGE,
            "is_question": False,
        }


def mock_chat_with_team_success(
    message: str, user_id: int, chat_id: int
) -> Dict[str, Union[str, bool]]:
    return {"message": "Success", "is_question": False, "status": "pause"}


@pytest.mark.asyncio
async def test_success_scenario() -> None:
    with patch(
        "captn.captn_agents.backend.teams_manager.chat_with_team",
        side_effect=mock_chat_with_team_success,
    ):
        chat_id = 10000
        message = "Some message"
        team_name = "Google Ads Team"
        user_id = 1

        teams_handler(user_id, chat_id, team_name, message)

        # Initially, the status should be inprogress
        await asyncio.sleep(1)
        result = await get_team_status(chat_id)
        print(result)
        assert result == {
            "team_id": chat_id,
            "user_id": user_id,
            "team_name": team_name,
            "team_status": "pause",
            "msg": "Success",
            "is_question": False,
        }
