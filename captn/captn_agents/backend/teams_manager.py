import ast
from typing import Dict, List, Union

from fastapi import BackgroundTasks

from captn.captn_agents.application import CaptnAgentRequest, chat

TEAMS_STATUS: Dict[
    str, Dict[str, Union[str, bool, int, Dict[str, Union[str, List[str]]]]]
] = {}

TEAM_EXCEPTION_MESSAGE = "Ahoy, mate! It seems our voyage hit an unexpected squall. Let's trim the sails and set a new course. Cast off once more by clicking the button below."


def add_to_teams_status(user_id: int, chat_id: int, team_name: str) -> None:
    TEAMS_STATUS[f"{chat_id}"] = {
        "team_id": chat_id,
        "user_id": user_id,
        "team_name": team_name,
        "team_status": "inprogress",
        "msg": "",
        "is_question": False,
        "smart_suggestions": {"suggestions": [""], "type": ""},
        "is_exception_occured": False,
    }


def change_teams_status(
    chat_id: int,
    team_status: str,
    message: str,
    is_question: bool,
    smart_suggestions: Dict[str, Union[str, List[str]]],
    is_exception_occured: bool = False,
) -> None:
    TEAMS_STATUS[f"{chat_id}"].update(
        {
            "team_status": team_status,
            "msg": message,
            "is_question": is_question,
            "smart_suggestions": smart_suggestions,
            "is_exception_occured": is_exception_occured,
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
        smart_suggestions: Dict[str, Union[str, List[str]]] = {
            "suggestions": [""],
            "type": "",
        }
        change_teams_status(
            chat_id, team_status, message, is_question, smart_suggestions
        )

    try:
        response = chat_with_team(message, user_id, chat_id)
        change_teams_status(
            chat_id=chat_id,
            team_status=response["status"],  # type: ignore
            message=response["message"],  # type: ignore
            is_question=response["is_question"],  # type: ignore
            smart_suggestions=response["smart_suggestions"],  # type: ignore
        )
    except Exception:
        change_teams_status(
            chat_id=chat_id,
            team_status="completed",
            message=TEAM_EXCEPTION_MESSAGE,
            is_question=False,
            smart_suggestions={"suggestions": ["Let's try again"], "type": "oneOf"},
            is_exception_occured=True,
        )


async def create_team(
    user_id: int,
    chat_id: int,
    message: str,
    team_name: str,
    background_tasks: BackgroundTasks,
) -> None:
    print("======")
    print("Team details:")
    print(f"User ID: {user_id}")
    print(f"Team ID: {chat_id}")
    print(f"Team Name: {team_name}")
    print(f"Message: {message}")
    print("======")
    background_tasks.add_task(teams_handler, user_id, chat_id, team_name, message)


async def get_team_status(
    chat_id: int,
) -> Dict[str, Union[str, bool, int, Dict[str, Union[str, List[str]]]]]:
    return TEAMS_STATUS.get(str(chat_id), {})
