from tempfile import TemporaryDirectory
from typing import Iterator

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.benchmarking.helpers import (
    get_client_response_for_the_team_conv,
)
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
        user_id = 123
        google_sheets_team = GBBGoogleSheetsTeam(
            task="Do your job.",
            user_id=user_id,
            conv_id=456,
            openapi_url=google_sheets_fastapi_openapi_url,
        )

        expected_messages = [
            "Sheet with the name 'Captn - Ads' has been created successfully.",
            "Sheet with the name 'Captn - Keywords' has been created successfully.",
        ]
        with TemporaryDirectory() as cache_dir:
            with Cache.disk(cache_path_root=cache_dir) as cache:
                google_sheets_team.initiate_chat(cache=cache)

                while True:
                    messages = google_sheets_team.get_messages()
                    for message in messages:
                        if "tool_responses" in message:
                            expected_messages_copy = expected_messages.copy()
                            for expected_message in expected_messages_copy:
                                if expected_message in message["content"]:
                                    expected_messages.remove(expected_message)
                                    print(f"Found message: {expected_message}")

                        if len(expected_messages) == 0:
                            break
                    if len(expected_messages) == 0:
                        break

                    num_messages = len(messages)
                    if num_messages < google_sheets_team.max_round:
                        customers_response = get_client_response_for_the_team_conv(
                            user_id=user_id,
                            conv_id=456,
                            message=google_sheets_team.get_last_message(),
                            cache=cache,
                            # client_system_message=_client_system_messages,
                        )
                        google_sheets_team.continue_chat(message=customers_response)

        assert (
            len(expected_messages) == 0
        ), f"Expected messages left: {expected_messages}"