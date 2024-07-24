import unittest
from typing import Any, Dict, Iterator, List, Optional

import pandas as pd
import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent
from autogen.io.base import IOStream

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.toolboxes.base import Toolbox
from captn.captn_agents.backend.tools._gbb_google_sheets_team_tools import (
    GoogleAdsResources,
    GoogleSheetsTeamContext,
    ResourceCreationResponse,
    _check_mandatory_columns,
    _get_alredy_existing_campaigns,
    _setup_campaign,
    create_google_ads_resources,
    create_google_sheets_team_toolbox,
)

from ..fixtures.google_sheets_team import ads_values
from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


def mock_execute_query_f(
    user_id: int,
    conv_id: int,
    customer_ids: List[str],
    login_customer_id: str,
    query: str,
) -> str:
    response_json = {
        customer_ids[0]: [
            {
                "campaign": {
                    "resourceName": "blah",
                    "name": "netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                    "id": "12345",
                }
            },
            {
                "campaign": {
                    "resourceName": "blah",
                    "name": "Netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                    "id": "23456",
                }
            },
        ]
    }
    return str(response_json)


class TestCreateGoogleAdsResources:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }
        self.user_id = 123
        self.conv_id = 456
        recommended_modifications_and_answer_list = []
        kwargs = {
            "recommended_modifications_and_answer_list": recommended_modifications_and_answer_list,
            "google_sheets_api_url": "https://google_sheets_api_url.com",
        }
        self.toolbox = create_google_sheets_team_toolbox(
            user_id=self.user_id, conv_id=self.conv_id, kwargs=kwargs
        )

        self.customer_id = "56-789"
        self.login_customer_id = "91-789"

        self.gads_resuces = GoogleAdsResources(
            customer_id=self.customer_id,
            spreadsheet_id="fkpvkfov",
            ads_title="ads_title",
            keywords_title="keywords_title",
            login_customer_id=self.login_customer_id,
        )
        recommended_modifications_and_answer_list.append(
            (self.gads_resuces.model_dump(), "yes")
        )
        self.context = GoogleSheetsTeamContext(
            user_id=self.user_id,
            conv_id=self.conv_id,
            toolbox=self.toolbox,
            recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
            google_sheets_api_url="https://google_sheets_api_url.com",
        )

    def test_llm_config(self) -> None:
        agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        user_proxy = UserProxyAgent(name="user_proxy", code_execution_config=False)

        self.toolbox.add_to_agent(agent, user_proxy)
        llm_config = agent.llm_config

        check_llm_config_total_tools(llm_config, 5)
        check_llm_config_descriptions(
            llm_config,
            {
                "reply_to_client": r"Respond to the client \(answer to his task or question for additional information\)",
                "ask_client_for_permission": "Ask the client for permission to make the changes.",
                "list_accessible_customers_with_account_types": "List accessible customers with account types",
                "list_sub_accounts": "Use this function to list sub accounts of a Google Ads manager account",
                "create_google_ads_resources": "Creates Google Ads resources",
            },
        )

    @pytest.mark.parametrize(
        ("mandatory_columns", "expected"),
        [
            (
                ["Campaign Name", "Level", "Negative"],
                "",
            ),
            (
                ["Campaign Name", "Level", "Negative", "Ad Group Name"],
                "table_title is missing columns: ['Ad Group Name']",
            ),
        ],
    )
    def test_check_mandatory_columns(
        self, mandatory_columns: List[str], expected: str
    ) -> None:
        df = pd.DataFrame(
            {
                "Campaign Name": ["abcd"],
                "Level": ["abcd"],
                "Negative": ["abcd"],
            }
        )
        result = _check_mandatory_columns(
            df=df,
            mandatory_columns=mandatory_columns,
            table_title="table_title",
        )

        assert result == expected

    def test_create_google_ads_resources_with_missing_mandatory_columns(self) -> None:
        keywords_values_with_missing_columns = {
            "values": [
                [
                    "Campaign Budget",
                    "Ad Group Name",
                    "Match Type",
                    "Keyword",
                ],
                [
                    "10",
                    "Pristina to Skoplje Transport | Exact",
                    "Exact",
                    "Svi autobusni polasci",
                ],
            ]
        }
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools._get_sheet_data",
            side_effect=[
                ads_values,
                keywords_values_with_missing_columns,
            ],
        ):
            with pytest.raises(ValueError) as exc_info:
                create_google_ads_resources(
                    google_ads_resources=self.gads_resuces,
                    context=self.context,
                )
            assert (
                str(exc_info.value)
                == "keywords_title is missing columns: ['Campaign Name', 'Level', 'Negative']"
            )

    def test_create_google_ads_resources(
        self,
        mock_get_sheet_data: Iterator[Any],
        mock_get_login_url: Iterator[None],
        mock_requests_get: Iterator[Any],
    ) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools.execute_query",
            wraps=mock_execute_query_f,
        ) as mock_execute_query:
            response = create_google_ads_resources(
                google_ads_resources=self.gads_resuces,
                context=self.context,
            )
            for expected in [
                """The following campaigns already exist:
netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN
Netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN""",
                """Created campaigns:
Kosovo-Macedonia | Pristina-Skoplje | Search | Worldwide | EN""",
            ]:
                assert expected in response

            assert mock_execute_query.call_count == 1

    def test_get_alredy_existing_campaigns(self) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools.execute_query",
            wraps=mock_execute_query_f,
        ):
            df = pd.DataFrame(
                {
                    "Campaign Name": [
                        "abcd",
                        "netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                        "Netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                    ],
                }
            )

            alredy_existing_campaigns = _get_alredy_existing_campaigns(
                df=df,
                user_id=123,
                conv_id=456,
                customer_id="123-456",
                login_customer_id="123-456",
            )
            assert alredy_existing_campaigns == [
                "netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                "Netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
            ]


class TestResourceCreationResponse:
    @pytest.mark.parametrize(
        ("skip_campaigns", "created_campaigns", "failed_campaigns", "expected"),
        [
            (
                ["Camp 1"],
                ["Camp 2"],
                {"Camp 3": "error 3", "Camp 4": "error 4"},
                """Created campaigns:
Camp 2

The following campaigns already exist:
Camp 1

Failed to create the following campaigns:
Camp 3:
error 3

Camp 4:
error 4

""",
            ),
            (
                [],
                [],
                {"Camp 3": "error 3"},
                """No campaigns were created.

Failed to create the following campaigns:
Camp 3:
error 3

""",
            ),
        ],
    )
    def test_response(
        self,
        skip_campaigns: List[str],
        created_campaigns: List[str],
        failed_campaigns: Dict[str, str],
        expected: str,
    ) -> None:
        resource_response = ResourceCreationResponse(
            skip_campaigns=skip_campaigns,
            created_campaigns=created_campaigns,
            failed_campaigns=failed_campaigns,
        )

        assert resource_response.response() == expected


class TestSetupCampaigns:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        self.user_id = 123
        self.conv_id = 456

        self.customer_id = "56-789"
        self.login_customer_id = "91-789"

        self.context = GoogleSheetsTeamContext(
            user_id=self.user_id,
            conv_id=self.conv_id,
            toolbox=Toolbox(),
            recommended_modifications_and_answer_list=[],
            google_sheets_api_url="https://google_sheets_api_url.com",
        )

    @pytest.mark.parametrize(
        ("headline", "expected_error_msg"),
        [
            (
                "Svi autobusni polasci",
                None,
            ),
            (
                "a" * 31,
                "Value error, Each headlines must be less than 30 characters!",
            ),
        ],
    )
    def test_setup_campaign(
        self,
        headline: str,
        expected_error_msg: Optional[str],
        mock_get_login_url: Iterator[None],
        mock_requests_get: Iterator[Any],
    ) -> None:
        ads_df = pd.DataFrame(
            {
                "Campaign Name": ["My Campaign"],
                "Campaign Budget": ["10"],
                "Ad Group Name": ["My Campaign Ad Group"],
                "Match Type": ["Exact"],
                "Headline 1": [headline],
                "Headline 2": ["Svi autobusni polasci"],
                "Headline 3": ["Svi autobusni polasci"],
                "Headline 4": ["Svi autobusni polasci"],
                "Headline 5": ["Svi autobusni polasci"],
                "Headline 6": ["Svi autobusni polasci"],
                "Headline 7": ["Svi autobusni polasci"],
                "Headline 8": ["Svi autobusni polasci"],
                "Headline 9": ["Svi autobusni polasci"],
                "Headline 10": ["Svi autobusni polasci"],
                "Headline 11": ["Svi autobusni polasci"],
                "Headline 12": ["Svi autobusni polasci"],
                "Headline 13": ["Svi autobusni polasci"],
                "Headline 14": ["Svi autobusni polasci"],
                "Headline 15": ["Svi autobusni polasci"],
                "Description Line 1": ["Svi autobusni polasci"],
                "Description Line 2": ["Svi autobusni polasci"],
                "Description Line 3": ["Svi autobusni polasci"],
                "Description Line 4": ["Svi autobusni polasci"],
                "Path 1": [None],
                "Path 2": [None],
                "Final URL": ["https://www.example.com"],
            }
        )

        kewords_df = pd.DataFrame(
            {
                "Campaign Name": ["My Campaign"],
                "Campaign Budget": ["10"],
                "Ad Group Name": ["My Campaign Ad Group"],
                "Match Type": ["Exact"],
                "Keyword": ["Svi autobusni polasci"],
                "Level": [None],
                "Negative": [False],
            }
        )

        _, error_msg = _setup_campaign(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            campaign_name="My Campaign",
            campaign_budget="10",
            context=self.context,
            ads_df=ads_df,
            keywords_df=kewords_df,
            iostream=IOStream.get_default(),
        )

        if expected_error_msg is None:
            assert error_msg is None
        else:
            assert expected_error_msg in error_msg
