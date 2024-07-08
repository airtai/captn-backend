from typing import Iterator

import pytest

from captn.captn_agents.backend.teams import (
    GBBGoogleSheetsTeam,
    Team,
)

from .helpers import helper_test_init


class TestGBBGoogleSheetsTeam:
    @pytest.fixture(autouse=True)
    def setup(self, google_sheets_fastapi_openapi_url: str) -> Iterator[None]:
        self.google_sheets_fastapi_openapi_url = google_sheets_fastapi_openapi_url
        Team._teams.clear()
        yield

    def test_init(self) -> None:
        google_sheets_team = GBBGoogleSheetsTeam(
            task="do your magic",
            user_id=123,
            conv_id=456,
            openapi_url=self.google_sheets_fastapi_openapi_url,
        )
        agent_number_of_functions_dict = {
            "google_sheets_expert": 10,
            "account_manager": 1,
            "user_proxy": 0,
        }

        number_of_registered_executions = (
            agent_number_of_functions_dict["google_sheets_expert"]
            + agent_number_of_functions_dict["account_manager"]
        )
        helper_test_init(
            team=google_sheets_team,
            number_of_registered_executions=number_of_registered_executions,
            agent_number_of_functions_dict=agent_number_of_functions_dict,
            team_class=GBBGoogleSheetsTeam,
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.fastapi_openapi_team
    def test_google_sheets_team_end2end(
        self, google_sheets_fastapi_openapi_url: str
    ) -> None:
        google_sheets_team = GBBGoogleSheetsTeam(
            task="I want to get the data from the Google spreadsheet id: 1234, title: 'New'.",
            user_id=123,
            conv_id=456,
            openapi_url=google_sheets_fastapi_openapi_url,
        )

        google_sheets_team.initiate_chat()

        messages = google_sheets_team.get_messages()
        success = False
        for message in messages:
            if (
                "tool_responses" in message
                and message["content"]
                == '{"values": [["Country", "Station From", "Station To"], ["USA", "New York", "Los Angeles"]]}'
            ):
                success = True
                break

        assert success, messages
