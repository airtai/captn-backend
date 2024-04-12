from typing import Type

from autogen.agentchat import UserProxyAgent

from captn.captn_agents.backend.teams import Team


def helper_test_init(
    team: Team,
    number_of_team_members: int,
    number_of_functions: int,
    team_class: Type[Team],
) -> None:
    try:
        assert isinstance(team, team_class)

        assert len(team.members) == number_of_team_members

        for agent in team.members:
            # execution of the tools
            number_of_functions_in_function_map = len(agent.function_map)
            if isinstance(agent, UserProxyAgent):
                assert number_of_functions_in_function_map == number_of_functions
            else:
                assert number_of_functions_in_function_map == 0

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

                assert set(team.user_proxy.function_map.keys()) == set(function_names)
            else:
                assert llm_config is False

    finally:
        user_id, conv_id = team.name.split("_")[-2:]
        success = Team.pop_team(user_id=int(user_id), conv_id=int(conv_id))
        assert success is not None
