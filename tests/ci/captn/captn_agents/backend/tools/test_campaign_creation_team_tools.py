import unittest
from typing import Any, Dict, List, Optional, Tuple

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent
from pydantic import ValidationError

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.teams._campaign_creation_team import (
    ad_group_with_ad_and_keywords,
)
from captn.captn_agents.backend.toolboxes.base import Toolbox
from captn.captn_agents.backend.tools._campaign_creation_team_tools import (
    AdGroupAdForCreation,
    _remove_resources,
    create_campaign_creation_team_toolbox,
)
from captn.captn_agents.backend.tools._functions import Context
from captn.captn_agents.backend.tools._google_ads_team_tools import (
    get_resource_id_from_response,
)
from captn.google_ads.client import clean_nones
from google_ads.model import RemoveResource

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


class TestTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }
        self.toolbox = create_campaign_creation_team_toolbox(
            user_id=12345,
            conv_id=67890,
            recommended_modifications_and_answer_list=[],
        )

    def test_llm_config(self) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        user_proxy = UserProxyAgent(name="user_proxy", code_execution_config=False)

        self.toolbox.add_to_agent(agent, user_proxy)
        llm_config = agent.llm_config

        check_llm_config_total_tools(llm_config, 7)
        check_llm_config_descriptions(
            llm_config,
            {
                "create_ad_group_with_ad_and_keywords": "Create an ad group with a single ad and a list of keywords",
                "reply_to_client": r"Respond to the client \(answer to his task or question for additional information\)",
                "ask_client_for_permission": "Ask the client for permission to make the changes.",
                "change_google_account": "This method should be used only when the client explicitly asks for the change of the Google account",
                "list_accessible_customers": "List all the customers accessible to the user",
                "execute_query": "Query the Google Ads API.",
                "create_campaign": "Creates Google Ads Campaign. VERY IMPORTANT:",
            },
        )

    @pytest.mark.parametrize(
        "response",
        [
            "Created customers/1212/adGroups/3434.",
            "Created customers/7119828439/adGroupCriteria/1212~3434.",
        ],
    )
    def test_get_resource_id_from_response(self, response) -> None:
        resource_id = get_resource_id_from_response(response)
        assert resource_id == "3434", resource_id

    @pytest.mark.parametrize(
        "side_effect",
        [
            [
                "Created customers/1212/adGroups/3434.",
                "Created customers/1212/adGroupAds/3434~5656.",
                "Created customers/1212/adGroupCriteria/3434~7878.",
                "Created customers/1212/adGroupCriteria/3434~8989.",
            ],
            [
                "Created customers/1212/adGroups/3434.",
                "Created customers/1212/adGroupAds/3434~5656.",
                "Created customers/1212/adGroupCriteria/3434~7878.",
                ValueError("Error: 400: The keyword text 'keyword1' is invalid."),
                "Removed customers/1212/adGroupCriteria/3434~7878.",
                "Removed customers/1212/adGroupAds/3434~5656.",
                "Removed customers/1212/adGroups/3434.",
            ],
        ],
    )
    def test_create_ad_group_with_ad_and_keywords(self, side_effect) -> None:
        ad_group = ad_group_with_ad_and_keywords.ad_group
        ad_group_ad = ad_group_with_ad_and_keywords.ad_group_ad
        keyword1 = ad_group_with_ad_and_keywords.keywords[0]
        keyword2 = ad_group_with_ad_and_keywords.keywords[1]

        with (
            unittest.mock.patch(
                "captn.captn_agents.backend.tools._campaign_creation_team_tools.google_ads_create_update",
                side_effect=side_effect,
            ) as mock_google_ads_create_update,
            unittest.mock.patch(
                "captn.captn_agents.backend.tools._campaign_creation_team_tools._remove_resources",
                wraps=_remove_resources,
            ) as mock_remove_resources,
        ):
            modification_function_params = clean_nones(
                {
                    "ad_group_with_ad_and_keywords": ad_group_with_ad_and_keywords.model_dump()
                }
            )
            context = Context(
                user_id=1,
                conv_id=1,
                recommended_modifications_and_answer_list=[
                    (modification_function_params, "yes")
                ],
                toolbox=Toolbox(),
            )
            create_ad_group_with_ad_and_keywords = self.toolbox.get_function(
                "create_ad_group_with_ad_and_keywords"
            )

            if isinstance(side_effect[3], ValueError):
                with pytest.raises(ValueError):
                    create_ad_group_with_ad_and_keywords(
                        ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
                        context=context,
                    )

                # 4 create calls (the last one failed) + 3 remove calls
                assert mock_google_ads_create_update.call_count == 7
                mock_remove_resources.assert_called_once_with(
                    user_id=1,
                    conv_id=1,
                    list_of_resources=[
                        RemoveResource(
                            customer_id="2222",
                            resource_id="3434",
                            resource_type="ad_group",
                        ),
                        RemoveResource(
                            customer_id="2222",
                            parent_id="3434",
                            resource_id="5656",
                            resource_type="ad",
                        ),
                        RemoveResource(
                            customer_id="2222",
                            parent_id="3434",
                            resource_id="7878",
                            resource_type="ad_group_criterion",
                        ),
                    ],
                    login_customer_id=None,
                )

            else:
                response = create_ad_group_with_ad_and_keywords(
                    ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords,
                    context=context,
                )

                expected_response = f"""Ad group '{ad_group.name}': {side_effect[0]}
Ad group ad with final url - '{ad_group_ad.final_url}': {side_effect[1]}
Keyword '{keyword1.keyword_text}': {side_effect[2]}
Keyword '{keyword2.keyword_text}': {side_effect[3]}
"""

                assert mock_google_ads_create_update.call_count == 4
                assert response == expected_response, response
                mock_remove_resources.assert_not_called()


class TestContext:
    def test_context_objects_are_not_coppies(self):
        recommended_modifications_and_answer_list: List[
            Tuple[Dict[str, Any], Optional[str]]
        ] = []
        context = Context(
            user_id=12345,
            conv_id=67890,
            recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
            toolbox=Toolbox(),
        )
        recommended_modifications_and_answer_list.append(("question", "answer"))

        actual = context.recommended_modifications_and_answer_list
        expected = [("question", "answer")]
        assert actual == expected, actual


class TestAdGroupAdForCreation:
    @pytest.mark.parametrize(
        "headlines, descriptions, expected",
        [
            (
                [
                    "H1",
                    "H2",
                    "H3",
                    "H4",
                    "H5",
                    "H6",
                    "H7",
                    "H8",
                    "H9",
                    "H10",
                    "H11",
                    "H12",
                    "H13",
                    "H14",
                    "H15",
                ],
                ["D1", "D2", "D3", "D4"],
                None,
            ),
            (
                ["H1", "H2", "H3", "H4"],
                ["D1", "D2", "D3", "D4"],
                ValidationError,
            ),
            (
                [
                    "H1",
                    "H2",
                    "H3",
                    "H4",
                    "H5",
                    "H6",
                    "H7",
                    "H8",
                    "H9",
                    "H10",
                    "H11",
                    "H12",
                    "H13",
                    "H14",
                    "H15",
                ],
                ["D1", "D2", "D3"],
                ValidationError,
            ),
        ],
    )
    def test_minimum_number_of_headlines_and_descriptions(
        self, headlines, descriptions, expected
    ):
        if expected == ValidationError:
            with pytest.raises(ValidationError):
                AdGroupAdForCreation(
                    customer_id="2222",
                    headlines=headlines,
                    descriptions=descriptions,
                    final_url="https://www.example.com",
                    status="ENABLED",
                )
        else:
            AdGroupAdForCreation(
                customer_id="2222",
                headlines=headlines,
                descriptions=descriptions,
                final_url="https://www.example.com",
                status="ENABLED",
            )

    @pytest.mark.parametrize(
        "headline, expected",
        [
            ("A" * 31, ValueError),
            ("{KeyWord: " + "A" * 30 + "}", None),
            ("{KeyWord: " + "A" * 31 + "}", ValueError),
        ],
    )
    def test_maximum_headline_string_length(self, headline, expected):
        descriptions = ["D1", "D2", "D3", "D4"]
        headlines = [
            "H1",
            "H2",
            "H3",
            "H4",
            "H5",
            "H6",
            "H7",
            "H8",
            "H9",
            "H10",
            "H11",
            "H12",
            "H13",
            "H14",
        ]
        headlines.append(headline)
        if expected is ValueError:
            with pytest.raises(ValueError):
                AdGroupAdForCreation(
                    customer_id="2222",
                    headlines=headlines,
                    descriptions=descriptions,
                    final_url="https://www.example.com",
                    status="ENABLED",
                )
        else:
            AdGroupAdForCreation(
                customer_id="2222",
                headlines=headlines,
                descriptions=descriptions,
                final_url="https://www.example.com",
                status="ENABLED",
            )
