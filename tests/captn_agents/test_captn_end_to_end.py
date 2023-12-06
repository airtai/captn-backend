import unittest

from freezegun import freeze_time

from captn.captn_agents.backend.end_to_end import start_conversation
from captn.captn_agents.backend.team import Team
from captn.google_ads.client import update_campaign_or_group_or_ad

from .utils import last_message_is_termination


@freeze_time("2023-11-01")
def test_update_campaign_name() -> None:
    # task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    # task = "Please pause all of my Google ads campaigns. Finally return me the status for all of my campaigns."
    # task = "Give me the names, ids and status for all of my campaignsf."
    # task = "Pause 'Website traffic-Search-3' campaign"

    # task = "Enable all Ads for the 'Website traffic-Search-3' campaign"
    # task = "I need customer_id and campaign id for 'Website traffic-Search-3' campaign"

    task = "To each campaign which name starts with: 'Website', add '-up' at the end of the name"

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.ask_for_additional_info",
        return_value="The user has authenticated. And he allows all the changes that you suggest",  # type: ignore
    ):
        with unittest.mock.patch(
            "captn.captn_agents.backend.google_ads_team.update_campaign_or_group_or_ad",
            side_effect=update_campaign_or_group_or_ad,
        ) as update_mock:
            team_name, last_message = start_conversation(
                user_id=user_id,
                conv_id=conv_id,
                task=task,
                max_round=80,
                human_input_mode="NEVER",
                class_name="captn_initial_team",
            )

            initial_team = Team.get_team(team_name)
            update_mock.assert_called()

            _, kwargs = update_mock.call_args
            assert kwargs["endpoint"] == "/update-campaign"

            assert last_message_is_termination(initial_team)


@freeze_time("2023-11-01")
def test_pause_campaigns() -> None:
    task = "Pause all campaigns which start with 'Website' campaign"

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.ask_for_additional_info",
        return_value="The user has authenticated. And he allows all the changes that you suggest",  # type: ignore
    ):
        with unittest.mock.patch(
            "captn.captn_agents.backend.google_ads_team.update_campaign_or_group_or_ad",
            side_effect=update_campaign_or_group_or_ad,
        ) as update_mock:
            team_name, last_message = start_conversation(
                user_id=user_id,
                conv_id=conv_id,
                task=task,
                max_round=80,
                human_input_mode="NEVER",
                class_name="captn_initial_team",
            )

            initial_team = Team.get_team(team_name)
            update_mock.assert_called()

            _, kwargs = update_mock.call_args
            assert kwargs["endpoint"] == "/update-campaign"

            assert last_message_is_termination(initial_team)


@freeze_time("2023-11-01")
def test_pause_ad_groups() -> None:
    task = "Pause all ad groups for the campaigns which name starts with 'Website'"

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.ask_for_additional_info",
        return_value="The user has authenticated. And he allows all the changes that you suggest",  # type: ignore
    ):
        with unittest.mock.patch(
            "captn.captn_agents.backend.google_ads_team.update_campaign_or_group_or_ad",
            side_effect=update_campaign_or_group_or_ad,
        ) as update_mock:
            team_name, last_message = start_conversation(
                user_id=user_id,
                conv_id=conv_id,
                task=task,
                max_round=80,
                human_input_mode="NEVER",
                class_name="captn_initial_team",
            )

            initial_team = Team.get_team(team_name)
            update_mock.assert_called()

            _, kwargs = update_mock.call_args
            assert kwargs["endpoint"] == "/update-ad-group"

            assert last_message_is_termination(initial_team)


@freeze_time("2023-11-01")
def test_pause_ads() -> None:
    task = "Pause all ads for the campaigns which name starts with 'Website'"

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.ask_for_additional_info",
        return_value="The user has authenticated. And he allows all the changes that you suggest",  # type: ignore
    ):
        with unittest.mock.patch(
            "captn.captn_agents.backend.google_ads_team.update_campaign_or_group_or_ad",
            side_effect=update_campaign_or_group_or_ad,
        ) as update_mock:
            team_name, last_message = start_conversation(
                user_id=user_id,
                conv_id=conv_id,
                task=task,
                max_round=80,
                human_input_mode="NEVER",
                class_name="captn_initial_team",
            )

            initial_team = Team.get_team(team_name)
            update_mock.assert_called()

            _, kwargs = update_mock.call_args
            assert kwargs["endpoint"] == "/update-ad"

            assert last_message_is_termination(initial_team)


def test_search_query() -> None:
    # task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    task = "Please give me the following attributes from campaigns: customer_id, ad_group_id, ad_id."
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
