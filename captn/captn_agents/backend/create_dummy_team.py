import asyncio
from typing import Dict, Union

ACTION_MSG = """
## 📢 Notification from **{}**:

<br/>

To navigate Google Ads waters, I require access to your account. Please use the link below to grant permission

<br/>

[Mock Link](http://localhost:3000/chat/{}?msg=LoggedIn&team_name={}&team_id={})
"""

QUESTION_MSG = """
## 📢 Notification from **{}**:

<br/>

Our team has a question for you. Can you please answer the below:

<br/>

What is your name? 😊"""

ANSWER_MSG = """
## 📢 Notification from **{}**:

<br/>

Hurray! Your campaign report is ready😊"""

TASK_STATUS: Dict[str, Dict[str, Union[str, bool, int]]] = {}


async def create_new_task(chat_id: str, conversation_id: str, team_name: str) -> None:
    TASK_STATUS[str(conversation_id)] = {
        "team_id": conversation_id,
        "team_name": team_name,
        "team_status": "inprogress",
        "msg": "",
        "is_question": False,
        "call_counter": 0,
    }
    await asyncio.sleep(15)
    TASK_STATUS[str(conversation_id)].update(
        {
            "team_status": "pause",
            "msg": ACTION_MSG.format(team_name, chat_id, team_name, conversation_id),
            "call_counter": int(TASK_STATUS[str(conversation_id)]["call_counter"]) + 1,
        }
    )


async def ask_question(chat_id: str, conversation_id: str, team_name: str) -> None:
    TASK_STATUS[str(conversation_id)] = {
        "team_id": conversation_id,
        "team_name": team_name,
        "team_status": "inprogress",
        "msg": "",
        "is_question": True,
        "call_counter": TASK_STATUS[str(conversation_id)]["call_counter"],
    }
    await asyncio.sleep(15)
    TASK_STATUS[str(conversation_id)].update(
        {
            "team_status": "pause",
            "msg": QUESTION_MSG.format(team_name),
            "call_counter": int(TASK_STATUS[str(conversation_id)]["call_counter"]) + 1,
        }
    )


async def complete_task(chat_id: str, conversation_id: str, team_name: str) -> None:
    TASK_STATUS[str(conversation_id)] = {
        "team_id": conversation_id,
        "team_name": team_name,
        "team_status": "inprogress",
        "msg": "",
        "is_question": False,
        "call_counter": TASK_STATUS[str(conversation_id)]["call_counter"],
    }
    await asyncio.sleep(15)
    TASK_STATUS[str(conversation_id)].update(
        {
            "team_status": "completed",
            "msg": ANSWER_MSG.format(team_name),
            "call_counter": int(TASK_STATUS[str(conversation_id)]["call_counter"]) + 1,
        }
    )


async def execute_dummy_task(
    chat_id: str, conversation_id: str, team_name: str
) -> None:
    is_new_task = conversation_id not in TASK_STATUS

    if is_new_task:
        await create_new_task(chat_id, conversation_id, team_name)
    else:
        if TASK_STATUS[str(conversation_id)]["call_counter"] == 1:
            await ask_question(chat_id, conversation_id, team_name)
        else:
            await complete_task(chat_id, conversation_id, team_name)


def create_dummy_task(
    user_id: int,
    chat_id: int,
    conversation_id: int,
    message: str,
    team_name: str,
) -> None:
    print("======")
    print("New team is created with the following details:")
    print(f"User ID: {user_id}")
    print(f"Chat ID: {chat_id}")
    print(f"Team ID/Conversation ID: {conversation_id}")
    print(f"Team Name: {team_name}")
    print(f"Message: {message}")
    print("======")
    # Start the task execution with the given conversation_id
    asyncio.create_task(
        execute_dummy_task(str(chat_id), str(conversation_id), team_name)
    )


def get_dummy_task_status(conversation_id: int) -> Dict[str, Union[str, bool]]:
    result = {
        k: v
        for k, v in TASK_STATUS.get(str(conversation_id), {}).items()
        if k != "call_counter"
    }
    return result  # type: ignore
