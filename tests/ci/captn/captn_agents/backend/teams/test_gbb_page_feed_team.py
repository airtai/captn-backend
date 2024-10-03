from tempfile import TemporaryDirectory
from typing import Any, Iterator

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.benchmarking.helpers import (
    get_client_response_for_the_team_conv,
)
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
        # mock_get_login_url: Iterator[Any],
        # mock_requests_get: Iterator[Any],
        # mock_requests_post: Iterator[Any],
        # mock_execute_query_f: Iterator[Any],
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
        with TemporaryDirectory() as cache_dir:
            with Cache.disk(cache_path_root=cache_dir) as cache:
                team.initiate_chat(cache=cache)

                while True:
                    messages = team.get_messages()
                    for message in messages:
                        if "tool_responses" in message:
                            expected_messages_copy = expected_messages.copy()
                            for expected_message in expected_messages_copy:
                                if expected_message in message["content"]:
                                    expected_messages.remove(expected_message)

                        if len(expected_messages) == 0:
                            break
                    if len(expected_messages) == 0:
                        break

                    num_messages = len(messages)
                    if num_messages < team.max_round:
                        customers_response = get_client_response_for_the_team_conv(
                            user_id=user_id,
                            conv_id=456,
                            message=team.get_last_message(),
                            cache=cache,
                            client_system_message="Just accept everything. If asked which account to use, use customer with id 3333",
                        )
                        team.toolbox._context.waiting_for_client_response = False
                        team.continue_chat(message=customers_response)
