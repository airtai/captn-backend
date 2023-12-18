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

TEAMS_STATUS: Dict[str, Dict[str, Union[str, bool, int]]] = {}


def add_to_teams_status(user_id: int, chat_id: int, team_name: str) -> None:
    TEAMS_STATUS[f"{chat_id}"] = {
        "team_id": chat_id,
        "user_id": user_id,
        "team_name": team_name,
        "team_status": "inprogress",
        "msg": "",
        "is_question": False,
    }


def change_teams_status(
    chat_id: int, team_status: str, message: str, is_question: bool
) -> None:
    TEAMS_STATUS[f"{chat_id}"].update(
        {
            "team_status": team_status,
            "msg": message,
            "is_question": is_question,
        }
    )


def chat_with_team(
    message: str, user_id: int, chat_id: int
) -> Dict[str, Union[str, bool]]:
    request_obj = CaptnAgentRequest(message=message, user_id=user_id, conv_id=chat_id)
    response: Dict[str, Union[str, bool]] = ast.literal_eval(chat(request_obj))
    return response


def teams_handler(user_id: int, chat_id: int, team_name: str, message: str) -> None:
    is_new_team = str(chat_id) not in TEAMS_STATUS

    if is_new_team:
        add_to_teams_status(user_id, chat_id, team_name)
    else:
        team_status = "inprogress"
        message = message
        is_question = False
        change_teams_status(chat_id, team_status, message, is_question)

    response = chat_with_team(message, user_id, chat_id)
    change_teams_status(
        chat_id=chat_id,
        team_status=response["status"],  # type: ignore
        message=NOTIFICATION_MSG.format(team_name, response["message"]),
        is_question=response["is_question"],  # type: ignore
    )


async def create_team(
    user_id: int,
    chat_id: int,
    message: str,
    team_name: str,
    background_tasks: BackgroundTasks,
) -> None:
    print("======")
    print("New team is created with the following details:")
    print(f"User ID: {user_id}")
    print(f"Team ID: {chat_id}")
    print(f"Team Name: {team_name}")
    print(f"Message: {message}")
    print("======")
    background_tasks.add_task(teams_handler, user_id, chat_id, team_name, message)


async def get_team_status(
    chat_id: int,
) -> Dict[str, Union[str, bool, int]]:
    return TEAMS_STATUS.get(str(chat_id), {})
