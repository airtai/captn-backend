from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Any, Iterator, Tuple
from unittest.mock import patch

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

    @contextmanager
    def mock_list_accessible_customers_f(self) -> Iterator[Tuple[Any, Any]]:
        with (
            patch(
                "captn.captn_agents.backend.tools._google_ads_team_tools.list_accessible_customers_client",
                return_value=["1111"],
            ) as mock_list_accessible_customers1,
            patch(
                "captn.captn_agents.backend.tools._functions.list_accessible_customers",
                return_value=["1111"],
            ) as mock_list_accessible_customers2,
            patch(
                "captn.captn_agents.backend.tools._functions.BENCHMARKING",
                True,
            ),
        ):
            yield (mock_list_accessible_customers1, mock_list_accessible_customers2)

    def test_init(self, mock_get_conv_uuid: Iterator[Any]) -> None:
        with mock_get_conv_uuid:
            google_sheets_team = GBBGoogleSheetsTeam(
                task="do your magic",
                user_id=123,
                conv_id=456,
                openapi_url=self.google_sheets_fastapi_openapi_url,
            )
        agent_number_of_functions_dict = {
            "google_sheets_expert": 8,
            "account_manager": 4,
            "google_ads_expert": 4,
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

    def _test_google_sheets_team_end2end(
        self,
        user_id: int,
        google_sheets_fastapi_openapi_url: str,
        mock_get_conv_uuid: Iterator[Any],
        mock_get_login_url: Iterator[Any],
        mock_requests_get: Iterator[Any],
    ) -> None:
        with (
            mock_get_conv_uuid,
            mock_get_login_url,
            mock_requests_get,
            self.mock_list_accessible_customers_f() as (
                mock_list_accessible_customers1,
                mock_list_accessible_customers2,
            ),
        ):
            google_sheets_team = GBBGoogleSheetsTeam(
                task="Do your job.",
                user_id=user_id,
                conv_id=456,
                openapi_url=google_sheets_fastapi_openapi_url,
            )

            expected_messages = [
                "Sheet with the name 'Captn - Ads",
                "Sheet with the name 'Captn - Keywords",
                "Keyword 'Rezerviraj odmah': Created resource",
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
                            google_sheets_team.toolbox._context.waiting_for_client_response = False
                            google_sheets_team.continue_chat(message=customers_response)

        assert (
            len(expected_messages) == 0
        ), f"Expected messages left: {expected_messages}"
        mock_list_accessible_customers1.assert_called_once()

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.fastapi_openapi_team
    def test_google_sheets_team_end2end(
        self,
        google_sheets_fastapi_openapi_url: str,
        mock_get_conv_uuid: Iterator[Any],
        mock_get_login_url: Iterator[Any],
        mock_requests_get: Iterator[Any],
        mock_get_sheet_data: Iterator[Any],
    ) -> None:
        with mock_get_sheet_data:
            self._test_google_sheets_team_end2end(
                user_id=123,
                google_sheets_fastapi_openapi_url=google_sheets_fastapi_openapi_url,
                mock_get_conv_uuid=mock_get_conv_uuid,
                mock_get_login_url=mock_get_login_url,
                mock_requests_get=mock_requests_get,
            )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.fastapi_openapi_team
    def test_google_sheets_real_fastapi_team_end2end(
        self,
        mock_get_conv_uuid: Iterator[Any],
        mock_get_login_url: Iterator[Any],
        mock_requests_get: Iterator[Any],
    ) -> None:
        self._test_google_sheets_team_end2end(
            user_id=13,
            google_sheets_fastapi_openapi_url="https://google-sheets.tools.staging.fastagency.ai/openapi.json",
            mock_get_conv_uuid=mock_get_conv_uuid,
            mock_get_login_url=mock_get_login_url,
            mock_requests_get=mock_requests_get,
        )
