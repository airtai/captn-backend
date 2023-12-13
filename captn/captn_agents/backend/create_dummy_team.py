import ast
from typing import Dict, Union

from fastapi import BackgroundTasks

from captn.captn_agents.application import CaptnAgentRequest, chat

NOTIFICATION_MSG = """
## 📢 Notification from **{}**:

<br/>

{}

<br/>
"""

TASK_STATUS: Dict[str, Dict[str, Union[str, bool, int]]] = {}


def create_new_task(
    conversation_id: int, user_id: int, chat_id: int, team_name: str
) -> None:
    TASK_STATUS[f"{conversation_id}"] = {
        "team_id": conversation_id,
        "user_id": user_id,
        "chat_id": chat_id,
        "team_name": team_name,
        "team_status": "inprogress",
        "msg": "",
        "is_question": False,
    }


def update_task(
    conversation_id: int, team_status: str, message: str, is_question: bool
) -> None:
    TASK_STATUS[f"{conversation_id}"].update(
        {
            "team_status": team_status,
            "msg": message,
            "is_question": is_question,
        }
    )


def chat_with_team(
    message: str, user_id: int, conversation_id: int
) -> Dict[str, Union[str, bool]]:
    request_obj = CaptnAgentRequest(
        message=message, user_id=user_id, conv_id=conversation_id
    )
    response: Dict[str, Union[str, bool]] = ast.literal_eval(chat(request_obj))
    return response


def execute_dummy_task(
    user_id: int, chat_id: int, conversation_id: int, team_name: str, message: str
) -> None:
    is_new_task = str(conversation_id) not in TASK_STATUS

    if is_new_task:
        create_new_task(conversation_id, user_id, chat_id, team_name)
    else:
        team_status = "inprogress"
        message = message
        is_question = False
        update_task(conversation_id, team_status, message, is_question)

    response = chat_with_team(message, user_id, conversation_id)
    update_task(
        conversation_id=conversation_id,
        team_status=response["status"],  # type: ignore
        message=NOTIFICATION_MSG.format(team_name, response["message"]),
        is_question=response["is_question"],  # type: ignore
    )


async def create_dummy_task(
    user_id: int,
    chat_id: int,
    conversation_id: int,
    message: str,
    team_name: str,
    background_tasks: BackgroundTasks,
) -> None:
    print("======")
    print("New team is created with the following details:")
    print(f"User ID: {user_id}")
    print(f"Team ID/Conversation ID: {conversation_id}")
    print(f"Team Name: {team_name}")
    print(f"Message: {message}")
    print("======")
    background_tasks.add_task(
        execute_dummy_task, user_id, chat_id, conversation_id, team_name, message
    )


async def get_dummy_task_status(
    conversation_id: int,
) -> Dict[str, Union[str, bool, int]]:
    return TASK_STATUS.get(str(conversation_id), {})
