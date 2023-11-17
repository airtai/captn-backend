import pytest

import shutil
import unittest
from pathlib import Path

from captn.captn_agents.backend.end_to_end import a_start_conversation
from captn.captn_agents.backend.google_ads_team import (
    get_create_google_ads_team,
)

from captn.captn_agents.backend.google_ads_team import (
    GoogleAdsTeam,
)

from captn.captn_agents.backend.team import Team

from .utils import last_message_is_termination


def _login_was_called(google_ads_team: GoogleAdsTeam) -> bool:
    last_message = google_ads_team.manager.chat_messages[google_ads_team.members[0]][
        -1
    ]["content"]
    return "https://accounts.google.com/o/oauth2/auth?client_id" in last_message


@pytest.mark.asyncio
async def test_get_login_url() -> None:
    user_id = 1
    conv_id = 1

    task = "I need a login url"
    google_ads_team = GoogleAdsTeam(task=task, user_id=user_id, conv_id=conv_id)
    await google_ads_team.a_initiate_chat()

    assert _login_was_called(google_ads_team)
    assert last_message_is_termination(google_ads_team)


@pytest.mark.asyncio
async def test_end_to_end() -> None:
    root_dir = Path("./logs/captn").resolve()
    if root_dir.exists():
        shutil.rmtree(root_dir)

    task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    user_id = 1
    conv_id = 17

    team_name, last_message = await a_start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        root_dir=root_dir,
        seed=45,
        max_round=15,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    initial_team = Team.get_team(team_name)

    assert last_message_is_termination(initial_team)

    # continue_conversation(
    #     team_name=team_name,
    #     message="Please write a summary of what has been done",
    # )
