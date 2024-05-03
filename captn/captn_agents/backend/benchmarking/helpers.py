import json
from typing import Callable, Dict, List, Optional, Union

from autogen.agentchat import AssistantAgent
from autogen.cache import Cache

from ..config import Config
from ..teams import Team
from ..tools._functions import reply_to_client

__all__ = ("get_client_response",)


def get_client_response(
    team: Team,
    cache: Cache,
    client_system_message: str = "Just accept everything.",
) -> Callable[[str, bool, Optional[Dict[str, Union[str, List[str]]]]], str]:
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

        message = f"This is the whole conversation between the team:\n\n{team_chat_history}\n\nYou must answer the following question/last message from the team:\n\n{message_for_client}"

        sender.initiate_chat(client, message=message, cache=cache)
        # last_message is the last message sent by the client
        last_message = client.chat_messages[sender][-1]["content"]
        return last_message  # type: ignore[no-any-return]

    return clients_response
