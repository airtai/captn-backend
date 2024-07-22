import unittest
from typing import Any, Iterator, List

import pandas as pd
import pytest

from captn.captn_agents.backend.toolboxes import Toolbox
from captn.captn_agents.backend.tools._gbb_google_sheets_team_tools import (
    GoogleAdsResources,
    GoogleSheetsTeamContext,
    _get_alredy_existing_campaigns,
    create_google_ads_resources,
)

from ..fixtures.google_sheets_team import ads_values


def mock_execute_query_f(
    user_id: int,
    conv_id: int,
    customer_ids: List[str],
    login_customer_id: str,
    query: str,
) -> str:
    response_json = {
        customer_ids[0]: [
            {
                "campaign": {
                    "resourceName": "blah",
                    "name": "netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                    "id": "12345",
                }
            },
            {
                "campaign": {
                    "resourceName": "blah",
                    "name": "Netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                    "id": "23456",
                }
            },
        ]
    }
    return str(response_json)


class TesteCreateGoogleAdsResources:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        toolbox = Toolbox()
        recommended_modifications_and_answer_list = []

        self.gads_resuces = GoogleAdsResources(
            customer_id="56-789",
            spreadsheet_id="fkpvkfov",
            ads_title="ads_title",
            keywords_title="keywords_title",
            login_customer_id="91-789",
        )
        recommended_modifications_and_answer_list.append(
            (self.gads_resuces.model_dump(), "yes")
        )
        self.context = GoogleSheetsTeamContext(
            user_id=123,
            conv_id=456,
            toolbox=toolbox,
            recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
            google_sheets_api_url="https://google_sheets_api_url.com",
        )

    def test_create_google_ads_resources_with_missing_mandatory_columns(self) -> None:
        keywords_values_with_missing_columns = {
            "values": [
                [
                    "Campaign Budget",
                    "Ad Group Name",
                    "Match Type",
                    "Keyword",
                ],
                [
                    "10",
                    "Pristina to Skoplje Transport | Exact",
                    "Exact",
                    "Svi autobusni polasci",
                ],
            ]
        }
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools._get_sheet_data",
            side_effect=[
                ads_values,
                keywords_values_with_missing_columns,
            ],
        ):
            with pytest.raises(ValueError) as exc_info:
                create_google_ads_resources(
                    google_ads_resources=self.gads_resuces,
                    context=self.context,
                )
            assert (
                str(exc_info.value)
                == "keywords_title is missing columns: ['Campaign Name', 'Level', 'Negative']"
            )

    def test_create_google_ads_resources(
        self,
        mock_get_sheet_data: Iterator[Any],
        mock_get_login_url: Iterator[None],
        mock_requests_get: Iterator[Any],
    ) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools.execute_query",
            wraps=mock_execute_query_f,
        ) as mock_execute_query:
            response = create_google_ads_resources(
                google_ads_resources=self.gads_resuces,
                context=self.context,
            )
            for expected in [
                """Skipped campaigns:
netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN
Netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN""",
                """Created campaigns:
Kosovo-Macedonia | Pristina-Skoplje | Search | Worldwide | EN""",
            ]:
                assert expected in response

            assert mock_execute_query.call_count == 1

    def test_get_alredy_existing_campaigns(self) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._gbb_google_sheets_team_tools.execute_query",
            wraps=mock_execute_query_f,
        ):
            df = pd.DataFrame(
                {
                    "Campaign Name": [
                        "abcd",
                        "netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                        "Netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                    ],
                }
            )

            alredy_existing_campaigns = _get_alredy_existing_campaigns(
                df=df,
                user_id=123,
                conv_id=456,
                customer_id="123-456",
                login_customer_id="123-456",
            )
            assert alredy_existing_campaigns == [
                "netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
                "Netherlands | Eindhoven-Amsterdam | Search | Worldwide | EN",
            ]
