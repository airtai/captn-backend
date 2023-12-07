import asyncio
from os import environ
from typing import Dict, Union

from captn.captn_agents.application import CaptnAgentRequest, chat

REDIRECT_DOMAIN = environ.get("REDIRECT_DOMAIN", "https://captn.ai")

NOTIFICATION_MSG = """
## 📢 Notification from **{}**:

<br/>

{}

<br/>
"""

ACTION_MSG = (
    """
## 📢 Notification from **{}**:

<br/>

To navigate Google Ads waters, I require access to your account. Please use the link below to grant permission

<br/>

<a class="underline text-white" href="""
    + f""""{REDIRECT_DOMAIN}/chat/"""
    + """{}?msg=LoggedIn&team_name={}&team_id={}">Mock Link</a>"""
    ""
)

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


async def create_new_task(
    chat_id: str, conversation_id: str, team_name: str, message: str
) -> None:
    TASK_STATUS[str(conversation_id)] = {
        "team_id": conversation_id,
        "team_name": team_name,
        "team_status": "inprogress",
        "msg": "",
        "is_question": False,
        "call_counter": 0,
    }
    # await asyncio.sleep(15)
    request_obj = CaptnAgentRequest(
        message=message, user_id=1, conv_id=int(conversation_id)
    )
    # last_message, is_question, status= chat(request_obj)
    # todo: add try except block
    last_message = chat(request_obj)
    TASK_STATUS[str(conversation_id)].update(
        {
            "team_status": "pause",
            # "msg": ACTION_MSG.format(team_name, chat_id, team_name, conversation_id),
            "msg": NOTIFICATION_MSG.format(team_name, last_message),
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
    chat_id: str, conversation_id: str, team_name: str, message: str
) -> None:
    is_new_task = conversation_id not in TASK_STATUS

    if is_new_task:
        await create_new_task(chat_id, conversation_id, team_name, message)
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
        execute_dummy_task(str(chat_id), str(conversation_id), team_name, message)
    )


def get_dummy_task_status(conversation_id: int) -> Dict[str, Union[str, bool]]:
    result = {
        k: v
        for k, v in TASK_STATUS.get(str(conversation_id), {}).items()
        if k != "call_counter"
    }
    return result  # type: ignore
