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
        gbb_initial_team = GBBInitialTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        agent_number_of_functions_dict = {
            "digitial_marketing_strategist": 3,
            "account_manager": 3,
            "user_proxy": 0,
        }

        helper_test_init(
            team=gbb_initial_team,
            number_of_registered_executions=3,
            agent_number_of_functions_dict=agent_number_of_functions_dict,
            team_class=GBBInitialTeam,
        )
