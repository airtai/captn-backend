import unittest
from tempfile import TemporaryDirectory
from typing import Iterator, Optional
from unittest.mock import MagicMock

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.teams import Team
from captn.captn_agents.backend.teams._campaign_creation_team import (
    CampaignCreationTeam,
)
from captn.captn_agents.backend.tools._campaign_creation_team_tools import (
    AdGroupAdForCreation,
    AdGroupCriterionForCreation,
    AdGroupForCreation,
    AdGroupWithAdAndKeywords,
    _create_ad_group,
    _create_ad_group_ad,
    _create_ad_group_keyword,
)
from captn.google_ads.client import ALREADY_AUTHENTICATED

from .fixtures.shared_descriptions import WEB_PAGE_SUMMARY_IKEA
from .helpers import helper_test_init


class TestCampaignCreationTeam:
    @pytest.fixture()
    def setup_ad_group_with_ad_and_keywords(self) -> Iterator[None]:
        ad_group_ad = AdGroupAdForCreation(
            final_url="https://www.example.com",
            headlines=["headline1", "headline2", "headline3"],
            descriptions=["description1", "description2"],
            status="ENABLED",
        )

        keyword1 = AdGroupCriterionForCreation(
            keyword_text="keyword1",
            keyword_match_type="EXACT",
            status="ENABLED",
        )
        keyword2 = AdGroupCriterionForCreation(
            keyword_text="keyword2",
            keyword_match_type="EXACT",
            status="ENABLED",
        )

        ad_group = AdGroupForCreation(
            name="ad_group",
            status="ENABLED",
            ad_group_ad=ad_group_ad,
            keywords=[keyword1, keyword2],
        )

        self.ad_group_with_ad_and_keywords: Optional[AdGroupWithAdAndKeywords] = None

        self.ad_group_with_ad_and_keywords = AdGroupWithAdAndKeywords(
            customer_id="1111",
            campaign_id="1212",
            ad_group=ad_group,
            ad_group_ad=ad_group_ad,
            keywords=[keyword1, keyword2],
        )

        Team._teams.clear()
        try:
            yield
        finally:
            # do some cleanup if needed
            Team._teams.clear()

    def test_init(self) -> None:
        campaign_creation_team = CampaignCreationTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        helper_test_init(
            team=campaign_creation_team,
            number_of_team_members=3,
            number_of_functions=8,
            team_class=CampaignCreationTeam,
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.campaign_creation_team
    def test_end2end(self, setup_ad_group_with_ad_and_keywords: None) -> None:
        def ask_client_for_permission_mock(*args, **kwargs) -> str:
            customer_to_update = (
                "We propose changes for the following customer: 'IKEA' (ID: 1111)"
            )
            assert "resource_details" in kwargs, f"{kwargs.keys()=}"
            assert "proposed_changes" in kwargs, f"{kwargs.keys()=}"
            message = f"{customer_to_update}\n\n{kwargs['resource_details']}\n\n{kwargs['proposed_changes']}"

            clients_answer = "yes"
            # In real ask_client_for_permission, we would append (message, None)
            # and we would update the clients_question_answer_list with the clients_answer in the continue_conversation function
            context = kwargs["context"]
            context.clients_question_answer_list.append((message, clients_answer))
            return clients_answer

        task = """Here is the customer brief:
Business: IKEA
Goal: The goal of the Google Ads campaign is to increase brand awareness and boost sales for https://www.ikea.com/gb/en.
Current Situation: The client is currently running digital marketing campaigns.
Website: The website for https://www.ikea.com/gb/en is [https://www.ikea.com/gb/en](https://https://www.ikea.com/gb/en).
Digital Marketing Objectives: The objectives of the Google Ads campaign are to increase brand awareness and drive website traffic for https://www.ikea.com/gb/en.
Any Other Information Related to Customer Brief: N/A
And the task is following:
For customer with ID 1111 I have already created campaign with ID: 1212.
The currency set for that campaign is EUR.
Create new ad groups with ad and keywords for the campaign.
- create ONLY ad groups for "IKEA for Business" and "Beds & Mattresses"

DO NOT ask client for feedback while you are planning or executing the task. You can ask for feedback only after you
have all information needed to ask for the final approval by calling 'ask_client_for_permission' function. Only after
you have the final approval, you can execute the task by calling 'create_ad_group_with_ad_and_keywords' function.
"""

        try:
            campaign_creation_team = CampaignCreationTeam(
                user_id=123,
                conv_id=456,
                task=task,
            )

            with (
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "list_accessible_customers",
                    return_value=["1111"],
                ),
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "ask_client_for_permission",
                    wraps=ask_client_for_permission_mock,
                ) as mock_ask_client_for_permission,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group",
                    wraps=_create_ad_group,
                ) as mock_create_ad_group,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group_ad",
                    wraps=_create_ad_group_ad,
                ) as mock_create_ad_group_ad,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group_keyword",
                    wraps=_create_ad_group_keyword,
                ) as mock_create_ad_group_keyword,
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "get_info_from_the_web_page",
                    return_value=WEB_PAGE_SUMMARY_IKEA,
                ),
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "execute_query",
                    return_value=(
                        "This method isn't implemented yet. So do NOT use it."
                    ),
                ),
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "create_campaign",
                    return_value="Campaign with id 1212 has already been created.",
                ),
                unittest.mock.patch(
                    "captn.google_ads.client.get_login_url",
                    return_value={"login_url": ALREADY_AUTHENTICATED},
                ),
                unittest.mock.patch(
                    "captn.google_ads.client.requests_get",
                    return_value=MagicMock(),
                ) as mock_requests_get,
            ):
                mock_requests_get.return_value.ok = True
                mock_requests_get.return_value.json.return_value = "Resource created!"

                with TemporaryDirectory() as cache_dir:
                    with Cache.disk(cache_path_root=cache_dir) as cache:
                        campaign_creation_team.initiate_chat(cache=cache)

                mock_ask_client_for_permission.assert_called()
                mock_create_ad_group.assert_called()
                mock_create_ad_group_ad.assert_called()
                mock_create_ad_group_keyword.assert_called()
                assert len(campaign_creation_team.clients_question_answer_list) > 0
                assert (
                    len(campaign_creation_team.clients_question_answer_list)
                    == mock_ask_client_for_permission.call_count
                )
        finally:
            user_id, conv_id = campaign_creation_team.name.split("_")[-2:]
            success = Team.pop_team(user_id=int(user_id), conv_id=int(conv_id))
            assert success is not None
