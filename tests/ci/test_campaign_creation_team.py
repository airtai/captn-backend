import unittest

from captn.captn_agents.backend.campaign_creation_team import CampaignCreationTeam
from captn.captn_agents.backend.campaign_creation_team_tools import (
    AdGroupAdForCreation,
    AdGroupCriterionForCreation,
    AdGroupForCreation,
    AdGroupWithAdAndKeywords,
)


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

        campaign_creation_team = CampaignCreationTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        with unittest.mock.patch(
            "captn.captn_agents.backend.campaign_creation_team.google_ads_create_update"
        ) as mock_google_ads_create_update:
            side_effect = [
                "Created customers/1212/adGroups/3434.",
                "Created customers/1212/adGroupAds/3434~5656.",
                "Created customers/1212/adGroupCriteria/3434~7878.",
                "Created customers/1212/adGroupCriteria/3434~8989.",
            ]
            mock_google_ads_create_update.side_effect = side_effect

            assert 0 != 1, "continue here"  # type: ignore[comparison-overlap]
