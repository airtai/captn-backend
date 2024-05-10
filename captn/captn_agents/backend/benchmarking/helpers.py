import json
from typing import Callable, Dict, List, Optional, Union

from autogen.cache import Cache

from ..config import Config
from ..teams import Team
from ..tools._brief_creation_team_tools import DELEGATE_TASK_ERROR_MESSAGE
from ..tools._functions import init_chat_and_get_last_message, reply_to_client
from .models import Models

__all__ = (
    "get_client_response",
    "get_config_list",
)


def get_config_list(llm: str) -> List[Dict[str, str]]:
    config = Config()
    if llm == Models.gpt3_5:
        return config.config_list_gpt_3_5

    if llm == Models.gpt4:
        return config.config_list_gpt_4

    raise ValueError(f"llm {llm} not supported")


def get_client_response(
    user_id: int,
    conv_id: int,
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
        # If the child team raises an error during the delegat_task, return the error message
        # The test will finish here
        if message == DELEGATE_TASK_ERROR_MESSAGE:
            return message_for_client

        message_for_client_json = json.loads(message_for_client)
        # Remove the keys that are not relevant for the client
        message_for_client_json.pop("is_question")
        message_for_client_json.pop("status")
        message_for_client_json.pop("terminate_groupchat")
        message_for_client = json.dumps(message_for_client_json)

        team = Team.get_team(user_id=user_id, conv_id=conv_id)
        if not isinstance(team, Team):
            raise ValueError(
                f"Team with user_id {user_id} and conv_id {conv_id} not found."
            )

        # Get the conversation history of the team, excluding the first and last message
        team_chat_history = (
            team.get_messages()[1:-1]
            if len(team.get_messages()) > 2
            else "No conversation yet."
        )

        message = f"This is the whole conversation between the team:\n\n{team_chat_history}\n\nYou must answer the following question/last message from the team:\n\n{message_for_client}"

        return init_chat_and_get_last_message(
            client_system_message=client_system_message,
            message=message,
            cache=cache,
        )

    return clients_response
