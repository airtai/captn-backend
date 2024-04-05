import unittest
from tempfile import TemporaryDirectory
from typing import Iterator, Optional

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
)
from captn.google_ads.client import ALREADY_AUTHENTICATED

# _create_ad_group,
# _create_ad_group_ad,
# _create_ad_group_keyword,


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

    def test_init(self, setup_ad_group_with_ad_and_keywords: None) -> None:
        campaign_creation_team = CampaignCreationTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )
        try:
            assert isinstance(campaign_creation_team, CampaignCreationTeam)
            assert campaign_creation_team.user_id == 123
            assert campaign_creation_team.conv_id == 456
            assert campaign_creation_team.task == "do your magic"

            assert len(campaign_creation_team.members) == 2

            expected_no_tools = 8
            for agent in campaign_creation_team.members:
                # execution of the tools
                print()
                for k, v in agent.function_map.items():
                    print(f"  - {k=}, {v=}")
                print()
                assert len(agent.function_map) == expected_no_tools

                # specification of the tools
                llm_config = agent.llm_config
                assert "tools" in llm_config, f"{llm_config.keys()=}"
                assert (
                    len(llm_config["tools"]) == expected_no_tools
                ), f"{llm_config['tools']=}"

                function_names = [
                    tool["function"]["name"] for tool in llm_config["tools"]
                ]

                assert set(agent.function_map.keys()) == set(function_names)
        finally:
            user_id, conv_id = campaign_creation_team.name.split("_")[-2:]
            success = Team.pop_team(user_id=int(user_id), conv_id=int(conv_id))
            assert success is not None

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.campaign_creation_team
    def test_end2end(self, setup_ad_group_with_ad_and_keywords: None) -> None:
        def ask_client_for_permission_mock(*args, **kwargs) -> str:
            customer_to_update = "We propose changes for the following customer: 'airt technologies d.o.o' (ID: 1111)"
            assert "resource_details" in kwargs, f"{kwargs.keys()=}"
            assert "proposed_changes" in kwargs, f"{kwargs.keys()=}"
            message = f"{customer_to_update}\n\n{kwargs['resource_details']}\n\n{kwargs['proposed_changes']}"

            clients_answer = "yes"
            # In real ask_client_for_permission, we would append (message, None)
            # and we would update the clients_question_answer_list with the clients_answer in the continue_conversation function
            kwargs["clients_question_answer_list"].append((message, clients_answer))
            return clients_answer

        task = """Here is the customer brief:
Business: airt.ai
Goal: The goal of the Google Ads campaign is to increase brand awareness and boost sales for airt.ai.
Current Situation: The client is currently running digital marketing campaigns.
Website: The website for airt.ai is [airt.ai](https://airt.ai).
Digital Marketing Objectives: The objectives of the Google Ads campaign are to increase brand awareness and drive website traffic for airt.ai.
Any Other Information Related to Customer Brief: N/A
Additional info from the web page:
airt.ai is a website that offers an AI-powered framework for streaming app development. They provide a fast and efficient framework for creating, testing, and managing microservices for streaming data. They also use bleeding-edge technology and deep learning to drive impact in their solutions. The website offers various products and tools for developers to explore, including the FastStream framework, Monotonic Neural Networks, and Material for nbdev. Users can also find news and information about the company on the website.
And the task is following:
For customer with ID 1111 I have already created campaign with ID: 1212.
The currency set for that campaign is EUR.
Create new ad groups with ad and keywords for the campaign.

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
                unittest.mock.patch(
                    "captn.captn_agents.backend.teams._google_ads_team.list_accessible_customers",
                ) as mock_list_accessible_customers,
                unittest.mock.patch(
                    "captn.captn_agents.backend.teams._google_ads_team.ask_client_for_permission",
                    wraps=ask_client_for_permission_mock,
                ) as mock_ask_client_for_permission,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group",
                    # wraps=_create_ad_group,
                ) as mock_create_ad_group,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group_ad",
                    # wraps=_create_ad_group_ad,
                ) as mock_create_ad_group_ad,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group_keyword",
                    # wraps=_create_ad_group_keyword,
                ) as mock_create_ad_group_keyword,
                unittest.mock.patch(
                    "captn.captn_agents.backend.teams._google_ads_team.get_info_from_the_web_page"
                ) as mock_get_info_from_the_web_page,
                unittest.mock.patch(
                    "captn.captn_agents.backend.teams._google_ads_team.execute_query"
                ) as mock_execute_query,
                unittest.mock.patch(
                    "captn.captn_agents.backend.teams._google_ads_team.create_campaign"
                ) as mock_create_campaign,
                unittest.mock.patch(
                    "captn.google_ads.client.get_login_url"
                ) as mock_get_login_url,
                # unittest.mock.patch(
                #     "captn.google_ads.client.requests.get"
                # ) as mock_requests_get,
            ):
                mock_list_accessible_customers.return_value = ["1111"]
                ### Delet aftter fixing gha
                mock_ask_client_for_permission.return_value = "yes"
                mock_create_ad_group.return_value = (
                    "Created customers/1212/adGroups/3434."
                )
                mock_create_ad_group_ad.return_value = (
                    "Created customers/1212/adGroupAds/3434~5656."
                )
                # create 20 keywords
                side_effect = [
                    f"Created customers/1212/adGroupCriteria/3434~{i}."
                    for i in range(20)
                ]
                mock_create_ad_group_keyword.side_effect = side_effect
                ### Delet aftter fixing gha
                mock_get_info_from_the_web_page.return_value = """SUMMARY:

Page content: The website is for a company called "airt" that offers an AI-powered framework for streaming app development. They provide a FastStream framework for creating, testing, and managing microservices for streaming data. They also have tools like Monotonic Neural Networks and Material for nbdev. The company focuses on driving impact with deep learning and incorporates a GPT-based model for predicting future events to be streamed. They have a community section and offer various products and tools. The website provides information about the company, news, and contact details.

Relevant links:
- FastStream framework: https://faststream.airt.ai
- Monotonic Neural Networks: https://monotonic.airt.ai
- Material for nbdev: https://nbdev-mkdocs.airt.ai
- News: /news
- About Us: /about-us
- Company information: /company-information
- Contact Us: /contact-us

Keywords: airt, AI-powered framework, streaming app development, FastStream framework, microservices, Monotonic Neural Networks, Material for nbdev, deep learning, GPT-based model

Headlines (MAX 30 char each): airt, AI-powered framework, FastStream, microservices, Monotonic Neural Networks, deep learning, GPT-based model, community, news, contact

Descriptions (MAX 90 char each): AI-powered framework for streaming app development, Create, test, and manage microservices for streaming data, Driving impact with deep learning, GPT-based model for predicting future events, Explore news and contact information

Use these information to SUGGEST the next steps to the client, but do NOT make any permanent changes without the client's approval!
"""
                mock_execute_query.return_value = (
                    "This method isn't implemented yet. So do NOT use it."
                )
                mock_create_campaign.return_value = (
                    "Campaign with id 1212 has already been created."
                )

                mock_get_login_url.return_value = {"login_url": ALREADY_AUTHENTICATED}
                # mock_requests_get.return_value.ok = True
                # mock_requests_get.return_value.json.return_value = "Resource created!"

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
