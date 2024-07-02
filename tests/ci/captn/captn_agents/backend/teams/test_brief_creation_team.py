from typing import Iterator

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

        helper_test_init(
            team=brief_creation_team,
            number_of_team_members=3,
            number_of_functions=4,
            team_class=BriefCreationTeam,
        )

    def test_get_avaliable_teams_and_their_descriptions(self) -> None:
        avaliable_teams_and_their_descriptions = (
            BriefCreationTeam.get_avaliable_team_names_and_their_descriptions()
        )

        # Only campaign_creation_team and default_team are available
        assert len(avaliable_teams_and_their_descriptions) == 2
        assert list(avaliable_teams_and_their_descriptions.keys()) == [
            "campaign_creation_team",
            "default_team",
        ]

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
