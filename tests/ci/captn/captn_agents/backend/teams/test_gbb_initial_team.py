from typing import Iterator

import pytest

from captn.captn_agents.backend.teams import (
    GBBInitialTeam,
    Team,
)

from .helpers import helper_test_init


class TestGBBInitialTeam:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        Team._teams.clear()
        yield

    def test_init(self) -> None:
        brief_creation_team = GBBInitialTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        helper_test_init(
            team=brief_creation_team,
            number_of_team_members=3,
            number_of_functions=3,
            team_class=GBBInitialTeam,
        )
