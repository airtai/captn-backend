from typing import Dict, Type

from autogen.agentchat import UserProxyAgent

from captn.captn_agents.backend.teams import Team


def helper_test_init(
    team: Team,
    number_of_registered_executions: int,
    agent_number_of_functions_dict: Dict[str, int],
    team_class: Type[Team],
) -> None:
    try:
        assert isinstance(team, team_class)

        assert len(team.members) == len(agent_number_of_functions_dict)

        for agent in team.members:
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
                assert set(function_names) <= set(team.user_proxy.function_map.keys())
            else:
                assert llm_config is False

    finally:
        user_id, conv_id = team.name.split("_")[-2:]
        success = Team.pop_team(user_id=int(user_id), conv_id=int(conv_id))
        assert success is not None
