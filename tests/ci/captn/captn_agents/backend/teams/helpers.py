import json
from typing import Dict, List, Optional, Type, Union

from autogen.agentchat import AssistantAgent, UserProxyAgent
from autogen.cache import Cache

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.teams import Team
from captn.captn_agents.backend.tools._functions import reply_to_client


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


def get_client_response(
    team: Team,
    cache: Cache,
    client_system_message: str = "Just accept everything.",
) -> str:
    def clients_response(
        message: str,
        completed: bool,
        smart_suggestions: Optional[Dict[str, Union[str, List[str]]]] = None,
    ) -> str:
        message_for_client = reply_to_client(
            message=message,
            completed=completed,
            smart_suggestions=smart_suggestions,
        )

        message_for_client_json = json.loads(message_for_client)
        # Remove the keys that are not relevant for the client
        message_for_client_json.pop("is_question")
        message_for_client_json.pop("status")
        message_for_client_json.pop("terminate_groupchat")
        message_for_client = json.dumps(message_for_client_json)

        # This agent is used only to send the message to the client
        sender = AssistantAgent(
            name="assistant",
            is_termination_msg=lambda x: True,  # Once the client replies, the sender will terminate the conversation
        )

        config_list = Config().config_list_gpt_3_5

        client = AssistantAgent(
            name="client",
            system_message=client_system_message,
            llm_config={
                "config_list": config_list,
                "temperature": 0,
            },
        )

        # Get the conversation history of the team, excluding the first and last message
        team_chat_history = (
            team.get_messages()[1:-1]
            if len(team.get_messages()) > 2
            else "No conversation yet."
        )

        message = f"This is the whole conversation between the team:\n\n{team_chat_history}\n\nYou must answer the following question:\n\n{message_for_client}"

        sender.initiate_chat(client, message=message, cache=cache)
        # last_message is the last message sent by the client
        last_message = client.chat_messages[sender][-1]["content"]
        return last_message

    return clients_response
