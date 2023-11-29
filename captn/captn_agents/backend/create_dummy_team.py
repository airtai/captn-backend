from typing import Dict
from pathlib import Path
import json
import asyncio

current_dir = Path(__file__).parent

project_root_dir = current_dir.parent.parent.parent

TASK_STATUS_FILE_PATH = project_root_dir / "task_status.json"

QUESTION_MSG = """
## 📢 Notification from our team: 

<br/>

Our team has a question for you. Can you please answer the below:

<br/>

What is your name? 😊"""

ANSWER_MSG = """
## 📢 Notification from our team: 

<br/>

Hurray! Your campaign report is ready😊"""


def read_json_file(file_path: str) -> Dict[str, str]:
    try:
        with open(Path(file_path), "r") as file:
            return json.load(file)
    except Exception as e:
        print(
            f"An error occurred while reading the task_status.json file: {e}. So returning empty dict."
        )
        return {}


def write_dict_to_json_file(data: Dict[str, str], file_path: str):
    try:
        with open(Path(file_path), "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error while writing to the task_status.json file: {e}")


async def execute_dummy_task(conversation_id: str, team_name: str, task_status_file_path: str):
    task_status = read_json_file(task_status_file_path)
    is_new_task = (conversation_id not in task_status) or (
        not task_status[conversation_id]["is_question"]
    )

    if is_new_task:
        task_status[conversation_id] = {
            "team_id": conversation_id,
            "team_name": team_name,
            "team_status": "inprogress",
            "msg": "",
            "is_question": True,
        }
        write_dict_to_json_file(task_status, task_status_file_path)

        await asyncio.sleep(15)
        task_status[conversation_id].update({"team_status": "pause", "msg": QUESTION_MSG})
    else:
        task_status[conversation_id] = {
            "team_id": conversation_id,
            "team_name": team_name,
            "team_status": "inprogress",
            "msg": "",
            "is_question": not task_status[conversation_id]["is_question"],
        }
        write_dict_to_json_file(task_status, task_status_file_path)

        await asyncio.sleep(20)
        task_status[conversation_id].update({"team_status": "completed", "msg": ANSWER_MSG})

    write_dict_to_json_file(task_status, task_status_file_path)


def create_dummy_task(
    conversation_id: int,
    message: str,
    team_name: str,
    task_status_file_path: str = TASK_STATUS_FILE_PATH,
):
    print("======")
    print(f"New team is created with the following details:")
    print(f"Team ID/Conversation ID: {conversation_id}")
    print(f"Team Name: {team_name}")
    print(f"Message: {message}")
    print("======")
    # Start the task execution with the given conversation_id
    asyncio.create_task(execute_dummy_task(str(conversation_id), team_name, task_status_file_path))


def get_dummy_task_status(
    conversation_id, task_status_file_path: str = TASK_STATUS_FILE_PATH
):
    task_status = read_json_file(task_status_file_path)
    return task_status.get(str(conversation_id), {})
