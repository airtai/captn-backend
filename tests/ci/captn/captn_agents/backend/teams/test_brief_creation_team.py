from typing import Iterator, List, Optional

import pytest

from captn.captn_agents.backend.benchmarking.brief_creation_team import (
    benchmark_brief_creation,
)
from captn.captn_agents.backend.benchmarking.models import Models
from captn.captn_agents.backend.teams import (
    BriefCreationTeam,
    Team,
)

from .helpers import helper_test_init


class TestBriefCreationTeam:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        Team._teams.clear()
        yield

    def test_init(self) -> None:
        brief_creation_team = BriefCreationTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        agent_number_of_functions_dict = {
            "digitial_marketing_strategist": 4,
            "account_manager": 4,
            "user_proxy": 0,
        }

        helper_test_init(
            team=brief_creation_team,
            number_of_registered_executions=4,
            agent_number_of_functions_dict=agent_number_of_functions_dict,
            team_class=BriefCreationTeam,
        )

    @pytest.mark.parametrize(
        ("use_only_team_names", "expected_keys"),
        [
            (None, ["campaign_creation_team", "default_team"]),
            (["campaign_creation_team"], ["campaign_creation_team"]),
        ],
    )
    def test_get_avaliable_teams_and_their_descriptions(
        self, use_only_team_names: Optional[List[str]], expected_keys: List[str]
    ) -> None:
        if use_only_team_names is None:
            avaliable_teams_and_their_descriptions = (
                BriefCreationTeam.get_avaliable_team_names_and_their_descriptions()
            )
        else:
            avaliable_teams_and_their_descriptions = (
                BriefCreationTeam.get_avaliable_team_names_and_their_descriptions(
                    use_only_team_names=use_only_team_names
                )
            )
        assert list(avaliable_teams_and_their_descriptions.keys()) == expected_keys

    @pytest.mark.parametrize(
        "team_name",
        [
            "campaign_creation_team",
            "default_team",
        ],
    )
    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.brief_creation_team
    def test_end2end_correct_team_choosed(self, team_name) -> None:
        benchmark_brief_creation(
            url="https://www.ikea.com/gb/en/",
            team_name=team_name,
            llm=Models.gpt4o,
        )
