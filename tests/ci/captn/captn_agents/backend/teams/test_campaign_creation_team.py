import pytest

from captn.captn_agents.backend.benchmarking.campaign_creation_team import (
    benchmark_campaign_creation,
)
from captn.captn_agents.backend.benchmarking.end2end import benchmark_end2end
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

        agent_number_of_functions_dict = {
            "copywriter": 7,
            "account_manager": 7,
            "user_proxy": 0,
        }

        helper_test_init(
            team=campaign_creation_team,
            number_of_registered_executions=7,
            agent_number_of_functions_dict=agent_number_of_functions_dict,
            team_class=CampaignCreationTeam,
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.campaign_creation_team
    def test_campaign_creation_team_end2end(self) -> None:
        benchmark_campaign_creation(
            url="https://www.ikea.com/gb/en/",
        )

    @pytest.mark.skip(reason="This takes too long")
    @pytest.mark.flaky
    @pytest.mark.openai
    def test_real_end2end(self) -> None:
        benchmark_end2end(
            url="https://www.ikea.com/gb/en/",
        )
