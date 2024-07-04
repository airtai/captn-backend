from typing import Iterator

import pytest
from autogen import UserProxyAgent

from captn.captn_agents.backend.teams import (
    Team,
    WeatherTeam,
)


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
        team_class = WeatherTeam
        number_of_team_members = 3
        number_of_registered_executions = 2
        agent_number_of_functions_dict = {
            "weather_forecaster": 1,
            "news_reporter": 1,
            "user_proxy": 0,
        }

        assert isinstance(weather_team, team_class)

        assert len(weather_team.members) == number_of_team_members

        for agent in weather_team.members:
            # execution of the tools
            number_of_functions_in_function_map = len(agent.function_map)
            if isinstance(agent, UserProxyAgent):
                print(agent.function_map)
                assert (
                    number_of_functions_in_function_map
                    == number_of_registered_executions
                )
            else:
                assert number_of_functions_in_function_map == 0

            number_of_functions = agent_number_of_functions_dict[agent.name]
            # specification of the tools
            llm_config = agent.llm_config
            if not isinstance(agent, UserProxyAgent):
                assert "tools" in llm_config, f"{llm_config.keys()=}"
                assert len(llm_config["tools"]) == number_of_functions, len(
                    llm_config["tools"]
                )

                function_names = [
                    tool["function"]["name"] for tool in llm_config["tools"]
                ]

                # Check if the agent's function names are in the user_proxy's function map
                assert set(function_names) <= set(
                    weather_team.user_proxy.function_map.keys()
                )
            else:
                assert llm_config is False
