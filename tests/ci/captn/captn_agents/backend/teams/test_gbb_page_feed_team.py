from typing import Any, Iterator

import pytest

from captn.captn_agents.backend.teams import (
    GBBPageFeedTeam,
    Team,
)

from .helpers import helper_test_init


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
            "google_sheets_expert": 8,
            "account_manager": 6,
            "google_ads_expert": 6,
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
