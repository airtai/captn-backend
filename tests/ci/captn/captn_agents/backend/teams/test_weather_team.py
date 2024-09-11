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
            "weather_forecaster": 2,
            "news_reporter": 1,
            "user_proxy": 0,
        }

        helper_test_init(
            team=weather_team,
            number_of_registered_executions=3,
            agent_number_of_functions_dict=agent_number_of_functions_dict,
            team_class=WeatherTeam,
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.fastapi_openapi_team
    def test_weather_team_end2end(self, weather_fastapi_openapi_url: str) -> None:
        weather_team = WeatherTeam(
            task="What's the weather like in London?",
            user_id=123,
            conv_id=456,
            openapi_url=weather_fastapi_openapi_url,
        )

        weather_team.initiate_chat()

        messages = weather_team.get_messages()
        success = False
        for message in messages:
            if (
                "tool_responses" in message
                and message["content"] == "Weather in London is sunny"
            ):
                success = True
                break

        assert success, messages
