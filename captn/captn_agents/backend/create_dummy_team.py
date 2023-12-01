from typing import Dict, Union
import asyncio

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

TASK_STATUS: Dict[str, Dict[str, Union[str, bool]]] = {}

async def execute_dummy_task(conversation_id: str, team_name: str) -> None:
    is_new_task = (conversation_id not in TASK_STATUS) or (
        not TASK_STATUS[conversation_id]["is_question"]
    )

    if is_new_task:
        TASK_STATUS[conversation_id] = {
            "team_id": conversation_id,
            "team_name": team_name,
            "team_status": "inprogress",
            "msg": "",
            "is_question": True,
        }
        await asyncio.sleep(15)
        TASK_STATUS[conversation_id].update({"team_status": "pause", "msg": QUESTION_MSG.format(team_name)})
    else:
        TASK_STATUS[conversation_id] = {
            "team_id": conversation_id,
            "team_name": team_name,
            "team_status": "inprogress",
            "msg": "",
            "is_question": not TASK_STATUS[conversation_id]["is_question"],
        }

        await asyncio.sleep(20)
        TASK_STATUS[conversation_id].update({"team_status": "completed", "msg": ANSWER_MSG.format(team_name)})


def create_dummy_task(
    conversation_id: int,
    message: str,
    team_name: str,
) -> None:
    print("======")
    print(f"New team is created with the following details:")
    print(f"Team ID/Conversation ID: {conversation_id}")
    print(f"Team Name: {team_name}")
    print(f"Message: {message}")
    print("======")
    # Start the task execution with the given conversation_id
    asyncio.create_task(execute_dummy_task(str(conversation_id), team_name))


def get_dummy_task_status(
    conversation_id: int
) -> Dict[str, Union[str, bool]]:
    return TASK_STATUS.get(str(conversation_id), {})
