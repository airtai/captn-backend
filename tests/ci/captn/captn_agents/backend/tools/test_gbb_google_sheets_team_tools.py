import unittest
from typing import Any, Dict, Iterator, List, Optional, Union

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
    _add_existing_sitelinks,
    _add_negative_campaign_keywords_lists,
    _add_new_sitelinks,
    _check_if_both_include_and_exclude_language_values_exist,
    _check_mandatory_columns,
    _get_alredy_existing_campaigns,
    _get_language_codes,
    _setup_campaign,
    _setup_campaigns,
    _setup_campaigns_with_retry,
    _update_callouts,
    _update_geo_targeting,
    _update_language_targeting,
    create_google_ads_resources,
    create_google_sheets_team_toolbox,
)

from ..fixtures.google_sheets_team import ads_values, campaigns_values
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
            campaigns_title="campaigns_title",
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

        check_llm_config_total_tools(llm_config, 6)
        check_llm_config_descriptions(
            llm_config,
            {
                "reply_to_client": r"Respond to the client \(answer to his task or question for additional information\)",
                "ask_client_for_permission": "Ask the client for permission to make the changes.",
                "list_accessible_customers_with_account_types": "List accessible customers with account types",
                "list_sub_accounts": "Use this function to list sub accounts of a Google Ads manager account",
                "create_google_ads_resources": "Creates Google Ads resources",
                "change_google_ads_account_or_refresh_token": "Change Google Ads account or refresh access token",
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
                campaigns_values,
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
        mock_requests_post: Iterator[Any],
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
Croatia | Ancona-Split | Search | Croatia | EN""",
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
                    "campaign name": [
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
        self.campaign_id = "12345"

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
        campaigns_df = pd.DataFrame(
            {
                "campaign name": ["My Campaign"],
                "campaign budget": ["10"],
                "search network": [True],
                "google search network": [True],
                "default max. cpc": ["0.30"],
            }
        )

        ads_df = pd.DataFrame(
            {
                "campaign name": ["My Campaign"],
                "campaign budget": ["10"],
                "ad group name": ["My Campaign Ad Group"],
                "match type": ["Exact"],
                "headline 1": [headline],
                "headline 2": ["Svi autobusni polasci"],
                "headline 3": ["Svi autobusni polasci"],
                "headline 4": ["Svi autobusni polasci"],
                "headline 5": ["Svi autobusni polasci"],
                "headline 6": ["Svi autobusni polasci"],
                "headline 7": ["Svi autobusni polasci"],
                "headline 8": ["Svi autobusni polasci"],
                "headline 9": ["Svi autobusni polasci"],
                "headline 10": ["Svi autobusni polasci"],
                "headline 11": ["Svi autobusni polasci"],
                "headline 12": ["Svi autobusni polasci"],
                "headline 13": ["Svi autobusni polasci"],
                "headline 14": ["Svi autobusni polasci"],
                "headline 15": ["Svi autobusni polasci"],
                "description line1": ["Svi autobusni polasci"],
                "description line2": ["Svi autobusni polasci"],
                "description line3": ["Svi autobusni polasci"],
                "description line4": ["Svi autobusni polasci"],
                "path 1": [None],
                "path 2": [None],
                "final url": ["https://www.example.com"],
            }
        )

        keywords_df = pd.DataFrame(
            {
                "campaign name": ["My Campaign"],
                "campaign budget": ["10"],
                "ad group name": ["My Campaign Ad Group"],
                "match type": ["Exact"],
                "keyword": ["Svi autobusni polasci"],
                "level": [None],
                "negative": [False],
            }
        )

        _, error_msg = _setup_campaign(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            campaign_row=campaigns_df.iloc[0],
            context=self.context,
            ads_df=ads_df,
            keywords_df=keywords_df,
            iostream=IOStream.get_default(),
        )

        if expected_error_msg is None:
            assert error_msg is None
        else:
            assert expected_error_msg in error_msg

    def _get_ads_df(
        self, headline: str, headline_1_1: str, headline_1_2: str
    ) -> pd.DataFrame:
        ads_df = pd.DataFrame(
            {
                "Campaign Name": ["My Campaign 1", "My Campaign 2"],
                "Campaign Budget": ["10", "10"],
                "Ad Group Name": ["My Campaign Ad Group 1", "My Campaign Ad Group 2"],
                "Match Type": ["Exact", "Exact"],
                "Headline 1": [headline_1_1, headline_1_2],
                "Headline 2": [headline, headline],
                "Headline 3": [headline, headline],
                "Headline 4": [headline, headline],
                "Headline 5": [headline, headline],
                "Headline 6": [headline, headline],
                "Headline 7": [headline, headline],
                "Headline 8": [headline, headline],
                "Headline 9": [headline, headline],
                "Headline 10": [headline, headline],
                "Headline 11": [headline, headline],
                "Headline 12": [headline, headline],
                "Headline 13": [headline, headline],
                "Headline 14": [headline, headline],
                "Headline 15": [headline, headline],
                "Description Line 1": [headline, headline],
                "Description Line 2": [headline, headline],
                "Description Line 3": [headline, headline],
                "Description Line 4": [headline, headline],
                "Path 1": [None, None],
                "Path 2": [None, None],
                "Final URL": ["https://www.example.com", "https://www.example.com"],
            }
        )
        ads_df.columns = ads_df.columns.str.lower()
        return ads_df

    @pytest.mark.parametrize(
        ("num_failed_campaigns", "error_msg"),
        [
            (
                0,
                None,
            ),
            (
                1,
                "Value error, Each headlines must be less than 30 characters!",
            ),
            (
                2,
                "Value error, Each headlines must be less than 30 characters!",
            ),
        ],
    )
    def test_setup_campaigns(
        self,
        num_failed_campaigns: int,
        error_msg: Optional[str],
        mock_get_login_url: Iterator[None],
        mock_requests_get: Iterator[Any],
    ) -> None:
        headline = "Svi autobusni polasci"

        if num_failed_campaigns == 0:
            headline_1_1 = headline
            headline_1_2 = headline
        elif num_failed_campaigns == 1:
            headline_1_1 = "a" * 31
            headline_1_2 = headline
        else:
            headline_1_1 = "a" * 31
            headline_1_2 = "a" * 31

        ads_df = self._get_ads_df(headline, headline_1_1, headline_1_2)

        keywords_df = pd.DataFrame(
            {
                "campaign name": ["My Campaign 1", "My Campaign 2"],
                "campaign budget": ["10", "10"],
                "ad group name": ["My Campaign Ad Group 1", "My Campaign Ad Group 2"],
                "match type": ["Exact", "Exact"],
                "keyword": ["Svi autobusni polasci", "Svi autobusni polasci"],
                "level": [None, None],
                "negative": [False, False],
            }
        )

        campaigns_df = pd.DataFrame(
            {
                "campaign name": ["My Campaign 1", "My Campaign 2"],
                "campaign budget": ["10", "10"],
                "search network": [True, True],
                "google search network": [True, True],
                "default max. cpc": ["0.30", "0.30"],
            }
        )

        response = _setup_campaigns(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            skip_campaigns=[],
            context=self.context,
            campaigns_df=campaigns_df,
            ads_df=ads_df,
            keywords_df=keywords_df,
            iostream=IOStream.get_default(),
        )

        if num_failed_campaigns == 0:
            assert response.created_campaigns == ["My Campaign 1", "My Campaign 2"]
            assert response.failed_campaigns == {}
        elif num_failed_campaigns == 1:
            assert response.created_campaigns == ["My Campaign 2"]
            assert response.failed_campaigns.keys() == {"My Campaign 1"}
            assert error_msg in response.failed_campaigns["My Campaign 1"]
        else:
            assert response.created_campaigns == []
            assert response.failed_campaigns.keys() == {
                "My Campaign 1",
                "My Campaign 2",
            }
            assert error_msg in response.failed_campaigns["My Campaign 1"]
            assert error_msg in response.failed_campaigns["My Campaign 2"]

    def test_setup_campaigns_with_retry(
        self,
        mock_get_login_url: Iterator[None],
        mock_requests_get: Iterator[Any],
    ) -> None:
        headline = "Svi autobusni polasci"

        ads_df = self._get_ads_df(headline, headline, headline)

        keywords_df = pd.DataFrame(
            {
                "campaign name": ["My Campaign 1", "My Campaign 2"],
                "ad group name": ["My Campaign Ad Group 1", "My Campaign Ad Group 2"],
                "match type": ["Exact", "Exact"],
                "keyword": ["Svi autobusni polasci", "Svi autobusni polasci"],
                "level": [None, None],
                "negative": [False, False],
            }
        )

        campaigns_df = pd.DataFrame(
            {
                "campaign name": ["My Campaign 1", "My Campaign 2"],
                "campaign budget": ["10", "10"],
                "search network": [True, True],
                "google search network": [True, True],
                "default max. cpc": ["0.30", "0.30"],
            }
        )

        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools._create_negative_campaign_keywords",
            side_effect=[
                Exception("Some error"),
                None,
                None,
            ],
        ) as mock_create_negative_campaign_keywords:
            response = _setup_campaigns_with_retry(
                customer_id=self.customer_id,
                login_customer_id=self.login_customer_id,
                skip_campaigns=[],
                context=self.context,
                campaigns_df=campaigns_df,
                ads_df=ads_df,
                keywords_df=keywords_df,
                iostream=IOStream.get_default(),
            )

        assert response.created_campaigns == ["My Campaign 2", "My Campaign 1"]
        assert response.failed_campaigns == {}
        assert mock_create_negative_campaign_keywords.call_count == 3

    @pytest.mark.parametrize(
        ("columns_prefix", "negative", "expected_location_names"),
        [
            (
                "include location",
                False,
                ["Croatia", "Slovenia"],
            ),
            (
                "exclude location",
                True,
                ["Montenegro"],
            ),
        ],
    )
    def test_update_geo_targeting(
        self,
        mock_get_login_url: Iterator[None],
        mock_requests_get: Iterator[Any],
        columns_prefix: str,
        negative: bool,
        expected_location_names: List[str],
    ) -> None:
        campaign_row = pd.Series(
            {
                "campaign name": "My Campaign",
                "include location 1": "Croatia",
                "include location 2": "Slovenia",
                "include location 3": None,
                "exclude location 1": "Montenegro",
                "exclude location 2": None,
                "exclude location 3": None,
            }
        )

        _update_geo_targeting(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            campaign_id=self.campaign_id,
            campaign_row=campaign_row,
            context=self.context,
            columns_prefix=columns_prefix,
            negative=negative,
        )

        mock_requests_get.assert_called_once()
        call = mock_requests_get.call_args_list[0]

        assert call[1]["params"]["location_names"] == expected_location_names
        assert call[1]["params"]["negative"] == negative

    @pytest.mark.parametrize(
        ("row", "expected"),
        [
            (
                pd.Series(
                    {
                        "include language 1": "English",
                        "include language 2": "Croatian",
                        "include language 3": None,
                    }
                ),
                ["en", "hr"],
            ),
            (
                pd.Series(
                    {
                        "include language 1": "English",
                        "include language 2": "Croatian",
                        "include language 3": "German",
                    }
                ),
                ["en", "hr", "de"],
            ),
            (
                pd.Series(
                    {
                        "include language 1": "English",
                        "include language 2": "English",
                        "include language 3": None,
                    }
                ),
                ["en"],
            ),
            (
                pd.Series(
                    {
                        "include language 1": "English",
                        "include language 2": "Croatian",
                        "include language 3": "German",
                        "include language 4": "Non valid language",
                    }
                ),
                ValueError,
            ),
        ],
    )
    def test_get_language_codes(
        self, row: pd.Series, expected: Union[List[str], ValueError]
    ) -> None:
        if isinstance(expected, list):
            language_codes = _get_language_codes(row, columns_prefix="include language")
            assert language_codes.sort() == expected.sort()

        else:
            with pytest.raises(ValueError):
                language_codes = _get_language_codes(
                    row, columns_prefix="include language"
                )

    @pytest.mark.parametrize(
        ("campaign_row", "expected"),
        [
            (
                pd.Series(
                    {
                        "include language 1": "English",
                        "include language 2": "Croatian",
                        "include language 3": None,
                    }
                ),
                None,
            ),
            (
                pd.Series(
                    {
                        "exclude language 1": "English",
                        "exclude language 2": "Croatian",
                        "exclude language 3": "German",
                    }
                ),
                None,
            ),
            (
                pd.Series(
                    {
                        "include language 1": "English",
                        "exclude language 2": "Croatian",
                    }
                ),
                ValueError,
            ),
        ],
    )
    def test_check_if_both_include_and_exclude_language_values_exist(
        self, campaign_row: pd.Series, expected: Optional[ValueError]
    ) -> None:
        if expected is None:
            _check_if_both_include_and_exclude_language_values_exist(
                campaign_row=campaign_row,
                columns_prefixes=["include language", "exclude language"],
            )
        else:
            with pytest.raises(ValueError):
                _check_if_both_include_and_exclude_language_values_exist(
                    campaign_row=campaign_row,
                    columns_prefixes=["include language", "exclude language"],
                )

    @pytest.mark.parametrize(
        ("campaign_row", "expected"),
        [
            (
                pd.Series(
                    {
                        "include language 1": "English",
                        "include language 2": "Croatian",
                        "include language 3": None,
                    }
                ),
                ["en", "hr"],
            ),
            (
                pd.Series(
                    {
                        "include language 1": "English",
                        "include language 2": "Croatian",
                        "include language 3": "German",
                    }
                ),
                ["en", "hr", "de"],
            ),
            (
                pd.Series(
                    {
                        "include language 1": None,
                        "include language 2": None,
                    }
                ),
                None,
            ),
        ],
    )
    def test_update_language_targeting(
        self,
        mock_get_login_url: Iterator[None],
        mock_requests_get: Iterator[Any],
        campaign_row: pd.Series,
        expected: Optional[List[str]],
    ) -> None:
        _update_language_targeting(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            campaign_id=self.campaign_id,
            campaign_row=campaign_row,
            context=self.context,
            columns_prefix="include language",
        )

        if expected is None:
            mock_requests_get.assert_not_called()
        else:
            mock_requests_get.assert_called_once()
            call = mock_requests_get.call_args_list[0]

            assert call[1]["params"]["language_codes"].sort() == expected.sort()

    def test_update_callouts(
        self,
        mock_get_login_url: Iterator[None],
        mock_requests_post: Iterator[Any],
    ) -> None:
        campaign_row = pd.Series(
            {
                "Campaign Name": "My Campaign",
                "Callout 1": "Free cancellation",
                "Callout 2": "Return tickets",
                "Callout 3": None,
            }
        )

        _update_callouts(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            campaign_id=self.campaign_id,
            campaign_row=campaign_row,
            context=self.context,
        )

        mock_requests_post.assert_called_once()
        call = mock_requests_post.call_args_list[0]
        assert call[1]["json"]["callouts"] == ["Free cancellation", "Return tickets"]

    def test_add_negative_campaign_keywords_lists(
        self,
        mock_get_login_url: Iterator[None],
        mock_requests_post: Iterator[Any],
    ) -> None:
        keywords_df = pd.DataFrame(
            {
                "campaign name": ["My Campaign", "My Campaign"],
                "ad group name": ["My Campaign Ad Group", "My Campaign Ad Group"],
                "match type": ["Exact", "Exact"],
                "keyword": ["Svi autobusni polasci", "my-list"],
                "level": [None, "Campaign List"],
                "negative": [False, True],
            }
        )

        _add_negative_campaign_keywords_lists(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            keywords_df=keywords_df,
            campaign_id=self.campaign_id,
            context=self.context,
        )

        mock_requests_post.assert_called_once()
        call = mock_requests_post.call_args_list[0]
        assert call[1]["json"]["shared_set_name"] == "my-list"

    def test_add_existing_sitelinks(
        self,
        mock_get_login_url: Iterator[None],
        mock_requests_post: Iterator[Any],
    ) -> None:
        campaign_row = pd.Series(
            {
                "campaign name": "My Campaign",
                "sitelink asset id 1": "12345",
                "sitelink asset id 2": "23456",
                "sitelink text 1": "Free cancellation",
            }
        )

        _add_existing_sitelinks(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            campaign_id=self.campaign_id,
            campaign_row=campaign_row,
            context=self.context,
        )

        mock_requests_post.assert_called_once()
        call = mock_requests_post.call_args_list[0]
        assert call[1]["json"]["sitelink_ids"] == ["12345", "23456"]

    @pytest.mark.parametrize(
        ("campaign_row", "expected"),
        [
            (
                pd.Series(
                    {
                        "campaign name": "My Campaign",
                        "sitelink 1 text": "Free cancellation",
                        "sitelink 2 text": "Return tickets",
                        "sitelink 1 final url": "https://www.example.com",
                        "sitelink 2 final url": "https://www.example2.com",
                        "sitelink 1 description 1": "s1 d1",
                        "sitelink 1 description 2": "s1 d2",
                        "sitelink 2 description 1": None,
                        "sitelink 2 description 2": None,
                    }
                ),
                [
                    {
                        "final_urls": ["https://www.example.com"],
                        "link_text": "Free cancellation",
                        "description1": "s1 d1",
                        "description2": "s1 d2",
                    },
                    {
                        "final_urls": ["https://www.example2.com"],
                        "link_text": "Return tickets",
                        "description1": None,
                        "description2": None,
                    },
                ],
            ),
            (
                pd.Series(
                    {
                        "campaign name": "My Campaign",
                        "sitelink 1 text": "Free cancellation",
                        "sitelink 1 final url": "https://www.example.com",
                        "sitelink 1 description 1": "s1 d1",
                        "sitelink 1 description 2": "s1 d2",
                        "sitelink 2 text": None,
                        "sitelink 2 final url": None,
                    }
                ),
                [
                    {
                        "final_urls": ["https://www.example.com"],
                        "link_text": "Free cancellation",
                        "description1": "s1 d1",
                        "description2": "s1 d2",
                    },
                ],
            ),
        ],
    )
    def test_add_new_sitelinks(
        self,
        mock_get_login_url: Iterator[None],
        mock_requests_post: Iterator[Any],
        campaign_row: pd.Series,
        expected: List[Dict[str, Union[str, List[str]]]],
    ) -> None:
        _add_new_sitelinks(
            customer_id=self.customer_id,
            login_customer_id=self.login_customer_id,
            campaign_id=self.campaign_id,
            campaign_row=campaign_row,
            context=self.context,
        )

        mock_requests_post.assert_called_once()
        call = mock_requests_post.call_args_list[0]

        assert call[1]["json"]["site_links"] == expected
