import unittest

from captn.captn_agents.backend.campaign_creation_team import CampaignCreationTeam
from captn.captn_agents.backend.campaign_creation_team_tools import (
    AdGroupAdForCreation,
    AdGroupCriterionForCreation,
    AdGroupForCreation,
    AdGroupWithAdAndKeywords,
)
from captn.captn_agents.backend.team import Team


class TestCampaignCreationTeam:
    def setup(self) -> None:
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

        self.ad_group_with_ad_and_keywords = AdGroupWithAdAndKeywords(
            customer_id="1111",
            campaign_id="1212",
            ad_group=ad_group,
            ad_group_ad=ad_group_ad,
            keywords=[keyword1, keyword2],
        )

    def test_init(self) -> None:
        campaign_creation_team = CampaignCreationTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )
        assert isinstance(campaign_creation_team, CampaignCreationTeam)
        assert campaign_creation_team.user_id == 123
        assert campaign_creation_team.conv_id == 456
        assert campaign_creation_team.task == "do your magic"

        assert len(campaign_creation_team.members) == 2

        expected_no_tools = 8
        for agent in campaign_creation_team.members:
            # execution of the tools
            assert len(agent.function_map) == expected_no_tools

            # specification of the tools
            llm_config = agent.llm_config
            assert "tools" in llm_config, f"{llm_config.keys()=}"
            assert (
                len(llm_config["tools"]) == expected_no_tools
            ), f"{llm_config['tools']=}"

            function_names = [tool["function"]["name"] for tool in llm_config["tools"]]

            assert set(agent.function_map.keys()) == set(function_names)

    def test_end2end(self) -> None:
        Team.pop_team("campaign_creation_team_123_456")
        task = (
            "For customer with ID 1111 I have already created campaign with ID: 1212."
            "The currency set for that campaign is EUR."
            "The final URL for the ad is airt.ai"
            "Now I want to create an ad group with an ad and keywords."
            "So Please do JUST that! Do NOT use execute_query command beacause you have all the info!"
            "If you need to modify headlines/descriptions, just do it, you don't need to ask me."
        )

        campaign_creation_team = CampaignCreationTeam(
            user_id=123,
            conv_id=456,
            task=task,
        )

        with unittest.mock.patch(
            "captn.captn_agents.backend.google_ads_team.list_accessible_customers"
        ) as mock_list_accessible_customers:
            with unittest.mock.patch(
                "captn.captn_agents.backend.google_ads_team.ask_client_for_permission"
            ) as mock_ask_client_for_permission:

                with unittest.mock.patch(
                    "captn.captn_agents.backend.campaign_creation_team_tools.google_ads_create_update"
                ) as mock_google_ads_create_update:
                    mock_list_accessible_customers.return_value = ["1111"]
                    mock_ask_client_for_permission.return_value = "yes"
                    # create ad group and ad
                    side_effect = [
                        "Created customers/1212/adGroups/3434.",
                        "Created customers/1212/adGroupAds/3434~5656.",
                    ]
                    # create 10 keywords
                    for i in range(10):
                        side_effect.append(
                            f"Created customers/1212/adGroupCriteria/3434~{i}."
                        )
                    mock_google_ads_create_update.side_effect = side_effect

                    campaign_creation_team.initiate_chat()

                    # At least 3 calls to google_ads_create_update: 1 ad group, 1 ad, 1 (or more) keywords
                    assert mock_google_ads_create_update.call_count >= 3
