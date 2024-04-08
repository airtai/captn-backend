import unittest
from typing import List, Optional, Tuple

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._campaign_creation_team_tools import (
    AdGroupAdForCreation,
    AdGroupCriterionForCreation,
    AdGroupForCreation,
    AdGroupWithAdAndKeywords,
    Context,
    # create_ad_group_with_ad_and_keywords,
    create_campaign_creation_team_toolbox,
)


class TestTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }
        self.toolbox = create_campaign_creation_team_toolbox(
            user_id=12345,
            conv_id=67890,
            clients_question_answer_list=[],
        )

    def test_llm_config(self) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        user_proxy = UserProxyAgent(name="user_proxy")

        self.toolbox.add_to_agent(agent, user_proxy)

        # add_create_ad_group_with_ad_and_keywords_to_agent(
        #     agent=agent,
        #     user_id=1,
        #     conv_id=1,
        #     clients_question_answer_list=[("question", "yes")],
        # )

        llm_config = agent.llm_config
        # print(f"{llm_config=}")
        assert "tools" in llm_config, f"{llm_config.keys()=}"
        assert len(llm_config["tools"]) == 1, f"{llm_config['tools']=}"
        assert (
            llm_config["tools"][0]["type"] == "function"
        ), f"{llm_config['tools'][0]['type']=}"

        function_config = llm_config["tools"][0]["function"]

        assert (
            function_config["name"] == "create_ad_group_with_ad_and_keywords"
        ), function_config
        assert (
            function_config["description"]
            == "Create an ad group with a single ad and a list of keywords"
        ), function_config["description"]

    def test_create_ad_group_with_ad_and_keywords(self) -> None:
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

        ad_group_with_ad_and_keywords = AdGroupWithAdAndKeywords(
            customer_id="1111",
            campaign_id="1212",
            ad_group=ad_group,
            ad_group_ad=ad_group_ad,
            keywords=[keyword1, keyword2],
        )

        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._campaign_creation_team_tools.google_ads_create_update"
        ) as mock_google_ads_create_update:
            side_effect = [
                "Created customers/1212/adGroups/3434.",
                "Created customers/1212/adGroupAds/3434~5656.",
                "Created customers/1212/adGroupCriteria/3434~7878.",
                "Created customers/1212/adGroupCriteria/3434~8989.",
            ]
            mock_google_ads_create_update.side_effect = side_effect

            context = Context(
                user_id=1,
                conv_id=1,
                clients_question_answer_list=[("question", "yes")],
            )
            create_ad_group_with_ad_and_keywords = self.toolbox.get_function(
                "create_ad_group_with_ad_and_keywords"
            )

            response = create_ad_group_with_ad_and_keywords(
                ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
                clients_approval_message="yes",
                modification_question="question",
                context=context,
            )

            expected_response = f"""Ad group: {side_effect[0]}
Ad group ad: {side_effect[1]}
Keyword: {side_effect[2]}
Keyword: {side_effect[3]}
"""

            print()
            print(f"{response=}")
            print(f"{expected_response=}")

            assert mock_google_ads_create_update.call_count == 4
            assert response == expected_response, response


class TestContext:
    def test_context_objects_are_not_coppies(self):
        clients_question_answer_list: List[Tuple[str, Optional[str]]] = []
        context = Context(
            user_id=12345,
            conv_id=67890,
            clients_question_answer_list=clients_question_answer_list,
        )
        clients_question_answer_list.append(("question", "answer"))

        actual = context.clients_question_answer_list
        expected = [("question", "answer")]
        assert actual == expected, actual
