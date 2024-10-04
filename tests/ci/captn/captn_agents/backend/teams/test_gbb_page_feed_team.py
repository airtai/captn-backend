from typing import Any, Iterator

import pytest

from captn.captn_agents.backend.teams import (
    GBBPageFeedTeam,
    Team,
)

from ..tools.test_gbb_page_feed_team_tools import mock_execute_query_f  # noqa: F401
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
    @pytest.mark.parametrize("mock_execute_query_f", ["1111"], indirect=True)
    def test_page_feed_real_fastapi_team_end2end(
        self,
        mock_get_conv_uuid: Iterator[Any],
        mock_execute_query_f: Iterator[Any],  # noqa: F811
        # mock_get_login_url: Iterator[Any],
        # mock_requests_get: Iterator[Any],
        # mock_requests_post: Iterator[Any],
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
            "All page feeds have been updated.",
        ]

        with mock_execute_query_f, mock_list_accessible_customers_f():
            start_converstaion(
                user_id=user_id, team=team, expected_messages=expected_messages
            )

        assert (
            len(expected_messages) == 0
        ), f"Expected messages left: {expected_messages}"
