import unittest
from typing import Any, Iterator

import pytest

from captn.captn_agents.backend.toolboxes import Toolbox
from captn.captn_agents.backend.tools._gbb_google_sheets_team_tools import (
    GoogleAdsResources,
    GoogleSheetsTeamContext,
    create_google_ads_resources,
)

from ..fixtures.google_sheets_team import ads_values


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
        response = create_google_ads_resources(
            google_ads_resources=self.gads_resuces,
            context=self.context,
        )
        for expected in [
            "Ad group ad",
            "Keyword",
            "Negative campaign keyword Neg Campaign",
            "Negative ad group keyword Neg",
        ]:
            assert expected in response
