import unittest

from captn.captn_agents.backend.end_to_end import start_conversation
from captn.captn_agents.backend.team import Team

from .utils import last_message_is_termination


def test_end_to_end() -> None:
    # task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    task = "Please stop all of my Google ads campaigns."
    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.ask_for_additional_info",
        return_value="The user has authenticated. And he allows all the changes that you suggest",  # type: ignore
    ):
        team_name, last_message = start_conversation(
            user_id=user_id,
            conv_id=conv_id,
            task=task,
            max_round=80,
            human_input_mode="NEVER",
            class_name="captn_initial_team",
        )

        initial_team = Team.get_team(team_name)

        # HOW TO MOCK INNER FUNCTION: get_create_google_ads_team.create_google_ads_team ???
        # print(f"{mock_get_create_google_ads_team.call_args_list=}")
        # mock_get_create_google_ads_team.assert_called_once()
        assert last_message_is_termination(initial_team)


def test_hello() -> None:
    task = "Hello"
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        max_round=80,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)


def test_non_relevant_questions() -> None:
    task = "Which city is the capital of Croatia?"
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        max_round=80,
        human_input_mode="NEVER",
        class_name="captn_initial_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)
