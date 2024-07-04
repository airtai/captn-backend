from typing import Iterator

import pytest

from captn.captn_agents.backend.teams import (
    Team,
    WeatherTeam,
)

from .helpers import helper_test_init


class TestWeatherTeam:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        Team._teams.clear()
        yield

    def test_init(self) -> None:
        weather_team = WeatherTeam(
            task="do your magic",
            user_id=123,
            conv_id=456,
        )
        agent_number_of_functions_dict = {
            "weather_forecaster": 1,
            "news_reporter": 1,
            "user_proxy": 0,
        }

        helper_test_init(
            team=weather_team,
            number_of_registered_executions=2,
            agent_number_of_functions_dict=agent_number_of_functions_dict,
            team_class=WeatherTeam,
        )
