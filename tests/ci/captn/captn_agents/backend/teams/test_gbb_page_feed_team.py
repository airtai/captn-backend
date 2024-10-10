import unittest
from typing import Any, Iterator

import pytest

from captn.captn_agents.backend.teams import (
    GBBPageFeedTeam,
    Team,
)

from ..tools.test_gbb_page_feed_team_tools import (
    _get_asset_sets_execute_query_return_value,
    _get_assets_execute_query_return_value,
)
from .helpers import helper_test_init, start_converstaion
from .test_gbb_google_sheets_team import mock_list_accessible_customers_f


class TestGBBPageFeedTeam:
    @pytest.fixture(autouse=True)
    def setup(self, google_sheets_fastapi_openapi_url: str) -> Iterator[None]:
        self.google_sheets_fastapi_openapi_url = google_sheets_fastapi_openapi_url
        Team._teams.clear()
        yield

    def test_init(self, mock_get_conv_uuid: Iterator[Any]) -> None:
        with mock_get_conv_uuid:
            team = GBBPageFeedTeam(
                task="do your magic",
                user_id=123,
                conv_id=456,
                openapi_url=self.google_sheets_fastapi_openapi_url,
            )
        agent_number_of_functions_dict = {
            "google_sheets_expert": 3,
            "account_manager": 5,
            "google_ads_expert": 5,
            "user_proxy": 0,
        }

        number_of_registered_executions = (
            agent_number_of_functions_dict["google_sheets_expert"]
            + agent_number_of_functions_dict["account_manager"]
        )
        helper_test_init(
            team=team,
            number_of_registered_executions=number_of_registered_executions,
            agent_number_of_functions_dict=agent_number_of_functions_dict,
            team_class=GBBPageFeedTeam,
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.fastapi_openapi_team
    def test_page_feed_real_fastapi_team_end2end(
        self,
        mock_get_conv_uuid: Iterator[Any],
    ) -> None:
        user_id = 13
        openapi_url = "https://google-sheets.tools.staging.fastagency.ai/openapi.json"

        with mock_get_conv_uuid:
            team = GBBPageFeedTeam(
                task="Do your job.",
                user_id=user_id,
                conv_id=456,
                openapi_url=openapi_url,
            )

        expected_messages = [
            "Page feed 'fastagency-reference' changes:",
            "Page feed 'fastagency-tutorial' changes:",
            "Added page feed items:",
            "The following page feed items should be removed by you manually:",
        ]

        customer_id = "1111"
        page_urls = [
            "https://fastagency.ai/latest/api/fastagency/FunctionCallExecution",
            "https://fastagency.ai/latest/api/fastagency/FastAgency",
        ]
        execuse_query_side_effect = [
            _get_asset_sets_execute_query_return_value(customer_id),
            _get_assets_execute_query_return_value(
                customer_id=customer_id, page_urls=page_urls
            ),
            _get_assets_execute_query_return_value(
                customer_id=customer_id, page_urls=[]
            ),
        ]

        with (
            mock_list_accessible_customers_f(),
            unittest.mock.patch(
                "captn.captn_agents.backend.tools._gbb_page_feed_team_tools.execute_query",
                side_effect=execuse_query_side_effect,
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
            start_converstaion(
                user_id=user_id, team=team, expected_messages=expected_messages
            )

        assert (
            len(expected_messages) == 0
        ), f"Expected messages left: {expected_messages}"
