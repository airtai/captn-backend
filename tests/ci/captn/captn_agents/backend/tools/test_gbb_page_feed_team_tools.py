import unittest
from typing import Iterator

import pandas as pd
import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._gbb_google_sheets_team_tools import (
    GoogleSheetsTeamContext,
)
from captn.captn_agents.backend.tools._gbb_page_feed_team_tools import (
    _get_sheet_data_and_return_df,
    create_page_feed_team_toolbox,
    validate_page_feed_data,
)

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


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
                "validate_page_feed_data": "Validate page feed data",
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

    def test_validate_page_feed_data(self) -> None:
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
            return_value = validate_page_feed_data(
                template_spreadsheet_id="abc123",
                page_feed_spreadsheet_id="def456",
                page_feed_sheet_title="Sheet1",
                context=self.context,
            )

            assert "{'7119828439': 'airt technologies d.o.o.'}" in return_value
