import unittest

import pytest
from freezegun import freeze_time

from captn.captn_agents.backend.end_to_end import start_conversation
from captn.captn_agents.backend.team import Team
from captn.google_ads.client import google_ads_create_update

from .utils import last_message_is_termination


@pytest.fixture(autouse=True)
def clear_team() -> None:
    Team._team_name_counter = 0
    Team._teams = {}


SHARED_PROMPT = (
    "Allow the chages to the google ads team without any confirmation from the client."
    "After the task is completed, use the reply_to_client command to return the result to the client."
)


@freeze_time("2023-11-01")
def test_update_campaign_name() -> None:
    # task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    # task = "Please pause all of my Google ads campaigns. Finally return me the status for all of my campaigns."
    # task = "Give me the names, ids and status for all of my campaignsf."
    # task = "Pause 'Website traffic-Search-3' campaign"

    # task = "Enable all Ads for the 'Website traffic-Search-3' campaign"
    # task = "I need customer_id and campaign id for 'Website traffic-Search-3' campaign"

    task = f"""To each campaign which name starts with: 'Website', add '-up' at the end of the name (add 'up' even if name already contains it)
You have all the permissions to update the campaign name, so do not ask me for any additional info, just do it!!
{SHARED_PROMPT}"""

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.google_ads_create_update",
        side_effect=google_ads_create_update,
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
    task = f"""Pause all campaigns which start with 'Website' campaign. (Pause them even if they are already paused)
You have all the permissions to pause the campaign, so do not ask me for any additional info, just do it!!
{SHARED_PROMPT}"""

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.google_ads_create_update",
        side_effect=google_ads_create_update,
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
    task = f"""Pause all ad groups for the campaigns which name starts with 'Website' (do not pause the campains).
You have all the permissions to pause the ad groups, so do not ask me for any additional info, just do it!!
{SHARED_PROMPT}"""

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.google_ads_create_update",
        side_effect=google_ads_create_update,
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
    task = f"""Pause all ads for the campaigns which name starts with 'Website' (do not pause tha campaign, just the ads).
You have all the permissions to pause the ads, so do not ask me for any additional info, just do it!!
{SHARED_PROMPT}"""

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.google_ads_create_update",
        side_effect=google_ads_create_update,
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


@freeze_time("2023-11-01")
def test_add_negative_keywords() -> None:
    task = f"""Add negative kwyword for customer_id=2324127278, campaign_id=20761810762.
Set keyword_text=new_keyword_testing and the keyqord match type should be Broad.
You have all the permissions to pause the ads, so do not ask me for any additional info, just do it!!
{SHARED_PROMPT}"""

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.google_ads_create_update",
        side_effect=google_ads_create_update,
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
        assert kwargs["endpoint"] == "/add-negative-keywords-to-campaign"

        assert last_message_is_termination(initial_team)


@freeze_time("2023-11-01")
def test_add_regular_keywords() -> None:
    task = f"""Add Btoad keyword 'pytest keyword' to the 'Ad group 1'.
You have all the permissions to pause the ads, so do not ask me for any additional info, just do it!!
{SHARED_PROMPT}"""

    user_id = 1
    conv_id = 17

    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.google_ads_create_update",
        side_effect=google_ads_create_update,
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
        assert kwargs["endpoint"] == "/add-keywords-to-ad-group"

        assert last_message_is_termination(initial_team)


def test_search_query() -> None:
    # task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    task = f"""Please give me the following attributes from campaigns: customer_id, ad_group_id, ad_id.

{SHARED_PROMPT}"""
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


def test_ending_the_conversation() -> None:
    task = "Which is more important: positive or negative keywords?"
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        max_round=80,
        human_input_mode="NEVER",
        class_name="google_ads_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team, is_gads_team=True)

    task = "Never mind"

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        max_round=80,
        human_input_mode="NEVER",
        class_name="google_ads_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team, is_gads_team=True)

    END_OF_CONV = "If there are any other tasks or questions, we are ready to assist."
    assert END_OF_CONV in last_message
