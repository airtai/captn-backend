from tempfile import TemporaryDirectory
from typing import Dict, List, Type

from autogen.agentchat import UserProxyAgent
from autogen.cache import Cache

from captn.captn_agents.backend.benchmarking.helpers import (
    get_client_response_for_the_team_conv,
)
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


def start_converstaion(
    user_id: int, google_sheets_team: Team, expected_messages: List[str]
) -> None:
    with TemporaryDirectory() as cache_dir:
        with Cache.disk(cache_path_root=cache_dir) as cache:
            google_sheets_team.initiate_chat(cache=cache)

            while True:
                messages = google_sheets_team.get_messages()
                for message in messages:
                    if "tool_responses" in message:
                        expected_messages_copy = expected_messages.copy()
                        for expected_message in expected_messages_copy:
                            if expected_message in message["content"]:
                                expected_messages.remove(expected_message)

                    if len(expected_messages) == 0:
                        break
                if len(expected_messages) == 0:
                    break

                num_messages = len(messages)
                if num_messages < google_sheets_team.max_round:
                    customers_response = get_client_response_for_the_team_conv(
                        user_id=user_id,
                        conv_id=456,
                        message=google_sheets_team.get_last_message(),
                        cache=cache,
                        client_system_message="Just accept everything. If asked which account to use, use customer with id 3333",
                    )
                    google_sheets_team.toolbox._context.waiting_for_client_response = (
                        False
                    )
                    google_sheets_team.continue_chat(message=customers_response)
