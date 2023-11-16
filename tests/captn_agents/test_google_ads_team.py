import unittest

# from unittest.mock import Mock
from captn.captn_agents.backend.google_ads_team import (
    GoogleAdsTeam,
)

from .utils import last_message_is_termination

# ask_for_additional_info = Mock()
# ask_for_additional_info.side_effect = [
#     "I'm not sure",
#     "Do what ever you think is the best solution",
# ] * 5


def _login_was_called(google_ads_team: GoogleAdsTeam) -> bool:
    last_message = google_ads_team.manager.chat_messages[google_ads_team.members[0]][
        -1
    ]["content"]
    return "https://accounts.google.com/o/oauth2/auth?client_id" in last_message


def test_get_login_url() -> None:
    user_id = 13
    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.get_login_url",
        return_value={
            "login_url": f"https://accounts.google.com/o/oauth2/auth?client_id=476761633153-o81jdsampd62i4biqef0k82494mepkjs.apps.googleusercontent.com&redirect_uri=http://localhost:9000/login/callback&response_type=code&scope=https://www.googleapis.com/auth/adwords email&access_type=offline&prompt=consent&state={user_id}"
        },  # type: ignore
    ) as mock_get_login_url:
        task = "I need a login url"
        google_ads_team = GoogleAdsTeam(task=task, user_id=user_id)
        google_ads_team.initiate_chat()

        mock_get_login_url.assert_called_once_with(user_id=user_id)
        assert _login_was_called(google_ads_team)
        assert last_message_is_termination(google_ads_team)


def test_list_accessible_customers() -> None:
    task = "List all the accesible customers"
    user_id = 13
    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.list_accessible_customers",
        return_value=["8942812744", "2324127278", "7119828439", "6505006790", "8913146119"],  # type: ignore
    ) as mock_list_accessible_customers:
        google_ads_team = GoogleAdsTeam(task=task, user_id=user_id)
        google_ads_team.initiate_chat()
        mock_list_accessible_customers.assert_called_once_with(user_id=user_id)
        assert last_message_is_termination(google_ads_team)


query_result = {
    "8942812744": [],
    "2324127278": [
        {
            "campaign": {
                "resourceName": "customers/2324127278/campaigns/20761810762",
                "name": "Website traffic-Search-3",
                "id": "20761810762",
            },
            "adGroup": {
                "resourceName": "customers/2324127278/adGroups/156261983518",
                "id": "156261983518",
                "name": "Ad group 1",
            },
            "keywordView": {
                "resourceName": "customers/2324127278/keywordViews/156261983518~304689274443"
            },
        },
        {
            "campaign": {
                "resourceName": "customers/2324127278/campaigns/20761810762",
                "name": "Website traffic-Search-3",
                "id": "20761810762",
            },
            "adGroup": {
                "resourceName": "customers/2324127278/adGroups/156261983518",
                "id": "156261983518",
                "name": "Ad group 1",
            },
            "keywordView": {
                "resourceName": "customers/2324127278/keywordViews/156261983518~327558728813"
            },
        },
        {
            "campaign": {
                "resourceName": "customers/2324127278/campaigns/20761810762",
                "name": "Website traffic-Search-3",
                "id": "20761810762",
            },
            "adGroup": {
                "resourceName": "customers/2324127278/adGroups/156261983518",
                "id": "156261983518",
                "name": "Ad group 1",
            },
            "keywordView": {
                "resourceName": "customers/2324127278/keywordViews/156261983518~327982491964"
            },
        },
        {
            "campaign": {
                "resourceName": "customers/2324127278/campaigns/20761810762",
                "name": "Website traffic-Search-3",
                "id": "20761810762",
            },
            "adGroup": {
                "resourceName": "customers/2324127278/adGroups/156261983518",
                "id": "156261983518",
                "name": "Ad group 1",
            },
            "keywordView": {
                "resourceName": "customers/2324127278/keywordViews/156261983518~352068863258"
            },
        },
    ],
}


def test_query_is_none() -> None:
    user_id = 13
    task = "Search database for customer ids: 8942812744 and 2324127278"
    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.execute_query",
        return_value=query_result,  # type: ignore
    ) as mock_query:
        google_ads_team = GoogleAdsTeam(task=task, user_id=user_id)
        google_ads_team.initiate_chat()
        mock_query.assert_called_once_with(user_id, ["8942812744", "2324127278"], None)

        assert last_message_is_termination(google_ads_team)


def test_query() -> None:
    user_id = 13
    task = "Search database for customer ids: 8942812744, 2324127278 and query: SELECT * FROM keyword_view"
    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.execute_query",
        return_value=query_result,  # type: ignore
    ) as mock_query:
        google_ads_team = GoogleAdsTeam(task=task, user_id=user_id)
        google_ads_team.initiate_chat()
        assert last_message_is_termination(google_ads_team)
        print(f"{mock_query.call_args_list=}")
        mock_query.assert_called_once_with(
            user_id, ["8942812744", "2324127278"], "SELECT * FROM keyword_view"
        )


def test_report_creation() -> None:
    user_id = 13
    task = "Create report for all customers and all campaigns"
    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.ask_for_additional_info",
        return_value="I don't know, I am fine with any proposal you suggest",  # type: ignore
    ):
        google_ads_team = GoogleAdsTeam(task=task, user_id=user_id)
        google_ads_team.initiate_chat()

    assert last_message_is_termination(google_ads_team)


def test_optimize_campaign() -> None:
    user_id = 13
    task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."
    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.google_ads.client.ask_for_additional_info",
        return_value="I don't know, please propose a solution and let's go with it without checking with me again.",  # type: ignore
    ):
        google_ads_team = GoogleAdsTeam(task=task, user_id=user_id)
        google_ads_team.initiate_chat()

    assert last_message_is_termination(google_ads_team)


def test_with_real() -> None:
    user_id = 1
    task = "Please optimize my Google ads campaigns, but don't change the budget. Propose and implement any solution as long it is legal and doesn't change the budget."

    google_ads_team = GoogleAdsTeam(task=task, user_id=user_id)
    google_ads_team.initiate_chat()

    assert last_message_is_termination(google_ads_team)

    google_ads_team.continue_chat(message="I am logged in.")


def test_real_query() -> None:
    user_id = 1
    task = "Search database for customer ids: 8942812744, 2324127278 and query: SELECT * FROM keyword_view"
    google_ads_team = GoogleAdsTeam(task=task, user_id=user_id)
    google_ads_team.initiate_chat()
    assert last_message_is_termination(google_ads_team)

    google_ads_team.continue_chat(message="We have the access")