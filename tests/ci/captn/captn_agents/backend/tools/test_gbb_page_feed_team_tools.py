import unittest
import unittest.mock
from typing import Any, Iterator, List

import pandas as pd
import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent
from autogen.io.base import IOStream

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._gbb_page_feed_team_tools import (
    PageFeedTeamContext,
    _get_page_feed_asset_sets,
    _get_page_feed_items,
    _get_relevant_page_feeds_and_accounts,
    _get_sheet_data_and_return_df,
    _sync_page_feed_asset_set,
    create_page_feed_team_toolbox,
    get_and_validate_page_feed_data,
)

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


def _get_assets_execute_query_return_value(
    customer_id: str, page_urls: List[str]
) -> str:
    request_json = {customer_id: []}
    for i in range(len(page_urls)):
        asset_id = f"17311100649{i}"
        asset = {
            "asset": {
                "resourceName": f"customers/{customer_id}/assets/{asset_id}",
                "type": "PAGE_FEED",
                "id": asset_id,
                "pageFeedAsset": {
                    "pageUrl": page_urls[i],
                },
            },
            "assetSetAsset": {
                "resourceName": f"customers/{customer_id}/assetSetAssets/8783430659~{asset_id}"
            },
        }

        request_json[customer_id].append(asset)

    mock_execute_query_return_value = str(request_json)
    return mock_execute_query_return_value


def _get_asset_sets_execute_query_return_value(customer_id: str) -> str:
    response_json = {
        customer_id: [
            {
                "assetSet": {
                    "resourceName": f"customers/{customer_id}/assetSets/8783430659",
                    "name": "fastagency-reference",
                    "id": "8783430659",
                },
            },
            {
                "assetSet": {
                    "resourceName": f"customers/{customer_id}/assetSets/8841207092",
                    "name": "fastagency-tutorial",
                    "id": "8841207092",
                },
            },
        ]
    }
    return str(response_json)


@pytest.fixture()
def mock_execute_query_f(request: pytest.FixtureRequest) -> Iterator[Any]:
    response_str = _get_asset_sets_execute_query_return_value(request.param)

    with unittest.mock.patch(
        "captn.captn_agents.backend.tools._gbb_page_feed_team_tools.execute_query",
        return_value=response_str,
    ) as mock_execute_query:
        yield mock_execute_query


class TestPageFeedTeamTools:
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
        self.toolbox = create_page_feed_team_toolbox(
            user_id=self.user_id, conv_id=self.conv_id, kwargs=kwargs
        )

        self.context = PageFeedTeamContext(
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
                "get_and_validate_page_feed_data": "Get and validate page feed data",
                "update_page_feeds": "Update Google Ads Page Feeds",
                "change_google_ads_account_or_refresh_token": "Change Google Ads account or refresh access token",
            },
        )

    def test_get_sheet_data_and_return_df(self) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_page_feed_team_tools.get_sheet_data",
            return_value={
                "values": [
                    ["Manager Customer Id", "Customer Id", "Name"],
                    ["758-703-7554", "711-982-8439", "airt technologies d.o.o."],
                ],
                "issues_present": False,
            },
        ):
            df = _get_sheet_data_and_return_df(
                user_id=-1,
                base_url="https://google_sheets_api_url.com",
                spreadsheet_id="abc123",
                title="Sheet1",
            )

            expected_df = pd.DataFrame(
                {
                    "Manager Customer Id": ["758-703-7554"],
                    "Customer Id": ["711-982-8439"],
                    "Name": ["airt technologies d.o.o."],
                }
            )

            pd.testing.assert_frame_equal(df, expected_df)

    @pytest.mark.parametrize(
        "page_feeds_and_accounts_templ_df, expected_df",
        [
            (
                pd.DataFrame(
                    {
                        "Customer Id": ["abc123"],
                        "Custom Label 1": ["StS; hr; Croatia"],
                        "Custom Label 2": ["StS; en; Croatia"],
                    }
                ),
                pd.DataFrame(
                    {
                        "Customer Id": ["abc123"],
                        "Custom Label 1": ["StS; hr; Croatia"],
                        "Custom Label 2": ["StS; en; Croatia"],
                    },
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "Customer Id": ["abc123", "def456"],
                        "Custom Label 1": ["StS; hr; Croatia", "StS; de; Croatia"],
                        "Custom Label 2": ["StS; en; Croatia", ""],
                    }
                ),
                pd.DataFrame(
                    {
                        "Customer Id": ["abc123", "def456"],
                        "Custom Label 1": ["StS; hr; Croatia", "StS; de; Croatia"],
                        "Custom Label 2": ["StS; en; Croatia", ""],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "Customer Id": ["abc123", "def456", "ghi789"],
                        "Custom Label 1": [
                            "None existent",
                            "None existent",
                            "None existent",
                        ],
                        "Custom Label 2": ["None existent", "None existent", ""],
                    }
                ),
                pd.DataFrame(columns=[]),
            ),
        ],
    )
    def test_get_relevant_page_feeds_and_accounts(
        self, page_feeds_and_accounts_templ_df: pd.DataFrame, expected_df: pd.DataFrame
    ) -> None:
        page_feeds_df = pd.DataFrame(
            {
                "Custom Label": ["StS; hr; Croatia", "StS; de; Croatia"],
            }
        )
        return_df = _get_relevant_page_feeds_and_accounts(
            page_feeds_and_accounts_templ_df=page_feeds_and_accounts_templ_df,
            page_feeds_df=page_feeds_df,
        )
        if not expected_df.empty:
            pd.testing.assert_frame_equal(return_df, expected_df)
        else:
            assert return_df.empty

    def test_get_and_validate_page_feed_data(self) -> None:
        side_effect_get_sheet_data = [
            {
                "values": [
                    ["Manager Customer Id", "Customer Id", "Name"],
                    ["758-703-7554", "711-982-8439", "airt technologies d.o.o."],
                ],
                "issues_present": False,
            },
            {
                "values": [
                    ["Customer Id", "Name", "Custom Label 1", "Custom Label 2"],
                    [
                        "711-982-8439",
                        "fastagency-reference",
                        "StS; hr; Croatia",
                        "StS; en; Croatia",
                    ],
                    [
                        "711-982-8439",
                        "fastagency-reference-de",
                        "StS; de; Croatia",
                        "",
                    ],
                ],
                "issues_present": False,
            },
            {
                "values": [
                    [
                        "Created Date",
                        "Language",
                        "Country From",
                        "Slug",
                        "URL Formula",
                        "Page URL",
                        "Custom Label",
                        "Station From",
                        "Station To",
                        "Country To",
                        "No. Landings",
                    ],
                    [
                        "Mar 5, 2023",
                        "en",
                        "Japan",
                        "bus-nara-to-tokyo",
                        "https://getbybus.com/en/bus-nara-to-tokyo",
                        "https://getbybus.com/en/bus-nara-to-tokyo",
                        "StS; Japan; en",
                        "Nara",
                        "Tokyo",
                        "Japan",
                        "876",
                    ],
                    [
                        "Feb 25, 2023",
                        "en",
                        "Egypt",
                        "bus-cairo-to-aswan",
                        "https://getbybus.com/en/bus-cairo-to-aswan",
                        "https://getbybus.com/en/bus-cairo-to-aswan",
                        "StS; Egypt; en",
                        "Cairo",
                        "Aswan",
                        "Egypt",
                        "474",
                    ],
                    [
                        "Jan 16, 2023",
                        "en",
                        "Thailand",
                        "bus-sukhothai-to-chiang-mai",
                        "https://getbybus.com/en/bus-sukhothai-to-chiang-mai",
                        "https://getbybus.com/en/bus-sukhothai-to-chiang-mai",
                        "StS; Thailand; en",
                        "Sukhothai",
                        "Chiang Mai",
                        "Thailand",
                        "346",
                    ],
                    [
                        "Jan 8, 2023",
                        "en",
                        "Jordan",
                        "bus-aqaba-to-petra",
                        "https://getbybus.com/en/bus-aqaba-to-petra",
                        "https://getbybus.com/en/bus-aqaba-to-petra",
                        "StS; Jordan; en",
                        "Aqaba",
                        "Petra",
                        "Jordan",
                        "280",
                    ],
                    [
                        "Mar 5, 2023",
                        "en",
                        "Croatia",
                        "bus-nara-to-tokyo",
                        "https://getbybus.com/en/bus-nara-to-tokyo",
                        "https://getbybus.com/en/bus-nara-to-tokyo",
                        "StS; en; Croatia",
                        "Nara",
                        "Tokyo",
                        "Croatia",
                        "876",
                    ],
                ],
                "issues_present": False,
            },
        ]
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_page_feed_team_tools.get_sheet_data",
            side_effect=side_effect_get_sheet_data,
        ):
            return_value = get_and_validate_page_feed_data(
                template_spreadsheet_id="abc123",
                page_feed_spreadsheet_id="def456",
                page_feed_sheet_title="Sheet1",
                context=self.context,
            )

            assert (
                "{'7119828439': {'Login Customer Id': '7587037554', 'Name Account': 'airt technologies d.o.o.'}"
                in return_value
            )

    @pytest.mark.parametrize("mock_execute_query_f", ["1111"], indirect=True)
    def test_get_page_feed_asset_sets(
        self, mock_execute_query_f: Iterator[Any]
    ) -> None:
        customer_id = "1111"
        with mock_execute_query_f:
            page_feed_asset_sets = _get_page_feed_asset_sets(
                user_id=1,
                conv_id=2,
                customer_id=customer_id,
                login_customer_id=customer_id,
            )

            assert len(page_feed_asset_sets) == 2

    @pytest.mark.parametrize(
        ("gads_page_urls", "page_feeds_df", "expected"),
        [
            (
                [
                    "https://getbybus.com/en/bus-zagreb-to-split",
                    "https://getbybus.com/hr/bus-zagreb-to-split",
                ],
                pd.DataFrame(
                    {
                        "Page URL": [
                            "https://getbybus.com/en/bus-zagreb-to-split",
                            "https://getbybus.com/hr/bus-zagreb-to-split/",
                            "https://getbybus.com/it/bus-zagreb-to-split",
                        ],
                        "Custom Label": [
                            "StS; en; Croatia",
                            "StS; hr; Croatia",
                            "StS; it; Croatia",
                        ],
                    }
                ),
                "No changes needed for page feed 'fastagency-reference'\n",
            ),
            (
                [
                    "https://getbybus.com/en/bus-zagreb-to-split",
                    "https://getbybus.com/hr/bus-zagreb-to-split/",
                    "https://getbybus.com/it/bus-zagreb-to-split",
                ],
                pd.DataFrame(
                    {
                        "Page URL": [
                            "https://getbybus.com/en/bus-zagreb-to-split",
                            "https://getbybus.com/hr/bus-zagreb-to-split/",
                            "https://getbybus.com/it/bus-zagreb-to-split",
                        ],
                        "Custom Label": [
                            "StS; en; Croatia",
                            "StS; hr; Croatia",
                            "StS; it; Croatia",
                        ],
                    }
                ),
                "Page feed 'fastagency-reference' changes:\nRemoved an asset set asset link",
            ),
            (
                [
                    "https://getbybus.com/en/bus-zagreb-to-split",
                    "https://getbybus.com/hr/bus-zagreb-to-split/",
                ],
                pd.DataFrame(
                    {
                        "Page URL": [
                            "https://getbybus.com/en/bus-zagreb-to-split",
                            "https://getbybus.com/hr/bus-zagreb-to-split/",
                            "https://getbybus.com/hr/bus-zagreb-to-karlovac",
                        ],
                        "Custom Label": [
                            "StS; en; Croatia",
                            "StS; hr; Croatia",
                            "StS; hr; Croatia",
                        ],
                    }
                ),
                "Page feed 'fastagency-reference' changes:\nCreated an asset set asset link",
            ),
        ],
    )
    def test_sync_page_feed_asset_set(
        self, gads_page_urls: List[str], page_feeds_df: pd.DataFrame, expected: str
    ) -> None:
        customer_id = "1111"
        page_feeds_and_accounts_templ_df = pd.DataFrame(
            {
                "Customer Id": [customer_id],
                "Name Page Feed": ["fastagency-reference"],
                "Custom Label 1": ["StS; hr; Croatia"],
                "Custom Label 2": ["StS; en; Croatia"],
            }
        )

        page_feed_asset_set_name = "fastagency-reference"
        page_feed_asset_set = {
            "resourceName": f"customers/{customer_id}/assetSets/8783430659",
            "id": "8783430659",
        }

        mock_execute_query_return_value = _get_assets_execute_query_return_value(
            customer_id, gads_page_urls
        )

        with (
            unittest.mock.patch(
                "captn.captn_agents.backend.tools._gbb_page_feed_team_tools.execute_query",
                side_effect=[mock_execute_query_return_value],
            ),
            unittest.mock.patch(
                "captn.captn_agents.backend.tools._gbb_page_feed_team_tools.google_ads_post_or_get",
                return_value="Created an asset set asset link",
            ),
            unittest.mock.patch(
                "captn.captn_agents.backend.tools._gbb_page_feed_team_tools.google_ads_create_update",
                return_value="Removed an asset set asset link",
            ),
        ):
            result = _sync_page_feed_asset_set(
                user_id=-1,
                conv_id=-1,
                customer_id=customer_id,
                login_customer_id=customer_id,
                page_feeds_and_accounts_templ_df=page_feeds_and_accounts_templ_df,
                page_feeds_df=page_feeds_df,
                page_feed_asset_set_name=page_feed_asset_set_name,
                page_feed_asset_set=page_feed_asset_set,
                iostream=IOStream.get_default(),
            )
            assert result == expected

    def test_get_page_feed_items(self) -> None:
        expected_page_urls = [
            "https://fastagency.ai/latest/api/fastagency/FunctionCallExecution",
            "https://fastagency.ai/latest/api/fastagency/FastAgency",
        ]
        expected_page_urls_and_labels_df = pd.DataFrame(
            {
                "Page URL": expected_page_urls,
                "Custom Label": [None, None],
            }
        )
        customer_id = "1111"

        mock_execute_query_return_value = _get_assets_execute_query_return_value(
            customer_id, expected_page_urls
        )
        asset_set_resource_name = f"customers/{customer_id}/assetSets/8783430659"

        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_page_feed_team_tools.execute_query",
            return_value=mock_execute_query_return_value,
        ):
            page_urls_and_labels_df = _get_page_feed_items(
                user_id=-1,
                conv_id=-1,
                customer_id=customer_id,
                login_customer_id=customer_id,
                asset_set_resource_name=asset_set_resource_name,
            )

        page_urls_and_labels_df = page_urls_and_labels_df.drop(columns=["Id"])
        assert page_urls_and_labels_df.sort_values("Page URL").equals(
            expected_page_urls_and_labels_df.sort_values("Page URL")
        )
