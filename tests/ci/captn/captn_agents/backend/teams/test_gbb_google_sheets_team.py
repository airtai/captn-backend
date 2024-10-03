from contextlib import contextmanager
from typing import Any, Iterator, Tuple
from unittest.mock import patch

import pytest

from captn.captn_agents.backend.teams import (
    GBBGoogleSheetsTeam,
    Team,
)

from .helpers import helper_test_init, start_converstaion


@contextmanager
def mock_list_accessible_customers_f() -> Iterator[Tuple[Any, Any, Any]]:
    ret_value1 = {
        "2222": [
            {
                "customerClient": {
                    "resourceName": "customers/2222/customerClients/2222",
                    "manager": True,
                    "descriptiveName": "Manager Account 1",
                    "id": "2222",
                }
            }
        ],
        "1111": [
            {
                "customerClient": {
                    "resourceName": "customers/1111/customerClients/1111",
                    "manager": False,
                    "descriptiveName": "airt technologies d.o.o.",
                    "id": "1111",
                }
            }
        ],
        "3333": [
            {
                "customerClient": {
                    "resourceName": "customers/3333/customerClients/3333",
                    "manager": True,
                    "descriptiveName": "My First Manager Account",
                    "id": "3333",
                }
            }
        ],
    }

    ret_value2 = {
        "3333": [
            {
                "customerClient": {
                    "resourceName": "customers/3333/customerClients/1111",
                    "manager": False,
                    "descriptiveName": "airt technologies d.o.o.",
                    "currencyCode": "EUR",
                    "id": "1111",
                }
            }
        ]
    }

    ret_value3 = {
        "1111": [
            {
                "customerClient": {
                    "resourceName": "customers/1111/customerClients/1111",
                    "manager": False,
                    "descriptiveName": "airt technologies d.o.o.",
                    "currencyCode": "EUR",
                    "id": "1111",
                }
            }
        ]
    }

    with (
        patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools.list_accessible_customers_with_account_types_client",
            return_value=ret_value1,
        ) as mock_list_accessible_customers_with_account_types_client,
        patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools.list_sub_accounts_client",
            return_value=ret_value2,
        ) as mock_list_sub_accounts_client,
        patch(
            "captn.captn_agents.backend.tools._functions.list_sub_accounts",
            return_value=ret_value3,
        ) as mock_list_sub_accounts2,
        patch(
            "captn.captn_agents.backend.tools._functions.BENCHMARKING",
            True,
        ),
    ):
        yield (
            mock_list_accessible_customers_with_account_types_client,
            mock_list_sub_accounts_client,
            mock_list_sub_accounts2,
        )


@pytest.fixture
def mock_execute_query_f() -> Iterator[Any]:
    with patch(
        "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools.execute_query",
        return_value="{'1111': []}",
    ) as mock_execute_query:
        yield mock_execute_query


class TestGBBGoogleSheetsTeam:
    @pytest.fixture(autouse=True)
    def setup(self, google_sheets_fastapi_openapi_url: str) -> Iterator[None]:
        self.google_sheets_fastapi_openapi_url = google_sheets_fastapi_openapi_url
        Team._teams.clear()
        yield

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
            "account_manager": 6,
            "google_ads_expert": 6,
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
        mock_requests_post: Iterator[Any],
        mock_execute_query_f: Iterator[Any],
    ) -> None:
        with (
            mock_get_conv_uuid,
            mock_get_login_url,
            mock_requests_get,
            mock_requests_post,
            mock_execute_query_f,
            mock_list_accessible_customers_f() as (
                mock_list_accessible_customers_with_account_types_client,
                mock_list_sub_accounts_client,
                mock_list_sub_accounts2,
            ),
        ):
            google_sheets_team = GBBGoogleSheetsTeam(
                task="Do your job.",
                user_id=user_id,
                conv_id=456,
                openapi_url=google_sheets_fastapi_openapi_url,
            )

            expected_messages = [
                "Sheet with the name 'Captn - Campaigns",
                "Sheet with the name 'Captn - Ads",
                "Sheet with the name 'Captn - Keywords",
                "Created campaigns:",
            ]
            start_converstaion(
                user_id=user_id,
                google_sheets_team=google_sheets_team,
                expected_messages=expected_messages,
            )

        assert (
            len(expected_messages) == 0
        ), f"Expected messages left: {expected_messages}"
        mock_list_accessible_customers_with_account_types_client.assert_called_once()

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.fastapi_openapi_team
    def test_google_sheets_team_end2end(
        self,
        google_sheets_fastapi_openapi_url: str,
        mock_get_conv_uuid: Iterator[Any],
        mock_get_login_url: Iterator[Any],
        mock_requests_get: Iterator[Any],
        mock_requests_post: Iterator[Any],
        mock_get_sheet_data: Iterator[Any],
        mock_execute_query_f: Iterator[Any],
    ) -> None:
        with mock_get_sheet_data:
            self._test_google_sheets_team_end2end(
                user_id=123,
                google_sheets_fastapi_openapi_url=google_sheets_fastapi_openapi_url,
                mock_get_conv_uuid=mock_get_conv_uuid,
                mock_get_login_url=mock_get_login_url,
                mock_requests_get=mock_requests_get,
                mock_requests_post=mock_requests_post,
                mock_execute_query_f=mock_execute_query_f,
            )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.fastapi_openapi_team
    def test_google_sheets_real_fastapi_team_end2end(
        self,
        mock_get_conv_uuid: Iterator[Any],
        mock_get_login_url: Iterator[Any],
        mock_requests_get: Iterator[Any],
        mock_requests_post: Iterator[Any],
        mock_execute_query_f: Iterator[Any],
    ) -> None:
        self._test_google_sheets_team_end2end(
            user_id=13,
            google_sheets_fastapi_openapi_url="https://google-sheets.tools.staging.fastagency.ai/openapi.json",
            mock_get_conv_uuid=mock_get_conv_uuid,
            mock_get_login_url=mock_get_login_url,
            mock_requests_get=mock_requests_get,
            mock_requests_post=mock_requests_post,
            mock_execute_query_f=mock_execute_query_f,
        )
