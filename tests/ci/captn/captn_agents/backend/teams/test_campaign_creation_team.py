import pytest

from captn.captn_agents.backend.benchmarking.campaign_creation_team import (
    benchmark_campaign_creation,
)
from captn.captn_agents.backend.teams._campaign_creation_team import (
    CampaignCreationTeam,
)

from .helpers import helper_test_init


class TestCampaignCreationTeam:
    def test_init(self) -> None:
        campaign_creation_team = CampaignCreationTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        helper_test_init(
            team=campaign_creation_team,
            number_of_team_members=3,
            number_of_functions=7,
            team_class=CampaignCreationTeam,
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.campaign_creation_team
    def test_end2end(self) -> None:
        benchmark_campaign_creation(
            url="https://www.ikea.com/gb/en/",
        )
