import shutil
import unittest
from pathlib import Path

from captn_agents.end_to_end import start_conversation
from captn_agents.google_ads_team import (
    get_create_google_ads_team,
)
from captn_agents.team import Team

from .utils import last_message_is_termination


def test_end_to_end() -> None:
    root_dir = Path("./logs/captn").resolve()
    if root_dir.exists():
        shutil.rmtree(root_dir)

    task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    user_id = 1
    conv_id = 17
    working_dir: Path = root_dir / f"{user_id=}" / f"{conv_id=}"

    create_google_ads_team = get_create_google_ads_team(
        user_id=user_id, working_dir=working_dir
    )
    with unittest.mock.patch(
        "captn_agents.captn_initial_team.get_create_google_ads_team",
        return_value=create_google_ads_team,
    ) as mock_get_create_google_ads_team:
        team_name, last_message = start_conversation(
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

        # HOW TO MOCK INNER FUNCTION: get_create_google_ads_team.create_google_ads_team ???
        print(f"{mock_get_create_google_ads_team.call_args_list=}")
        mock_get_create_google_ads_team.assert_called_once()
        assert last_message_is_termination(initial_team)

        # continue_conversation(
        #     team_name=team_name,
        #     message="Please write a summary of what has been done",
        # )
