import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Union

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


def read_json_file(file_path: str) -> Dict[str, Any]:
    try:
        with open(Path(file_path)) as file:
            return json.load(file)  # type: ignore[no-any-return]
    except Exception as e:
        print(
            f"An error occurred while reading the task_status.json file: {e}. So returning empty dict."
        )
        return {}


def write_dict_to_json_file(data: Dict[str, str], file_path: str) -> None:
    try:
        with open(Path(file_path), "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error while writing to the task_status.json file: {e}")


async def execute_dummy_task(conversation_id: str, task_status_file_path: str) -> None:
    task_status = read_json_file(task_status_file_path)
    is_question: bool = task_status[conversation_id]["is_question"]  # type: ignore
    is_new_task = (conversation_id not in task_status) or (not is_question)

    if is_new_task:
        task_status[conversation_id] = {
            "status": "inprogress",
            "msg": "",
            "is_question": True,
        }
        write_dict_to_json_file(task_status, task_status_file_path)

        await asyncio.sleep(15)
        task_status[conversation_id].update({"status": "pause", "msg": QUESTION_MSG})
    else:
        task_status[conversation_id] = {
            "status": "inprogress",
            "msg": "",
            "is_question": not task_status[conversation_id]["is_question"],
        }
        write_dict_to_json_file(task_status, task_status_file_path)

        await asyncio.sleep(20)
        task_status[conversation_id].update({"status": "completed", "msg": ANSWER_MSG})

    write_dict_to_json_file(task_status, task_status_file_path)


def create_dummy_task(
    conversation_id: int,
    message: str,
    task_status_file_path: Path = TASK_STATUS_FILE_PATH,
) -> None:
    print("======")
    print(f"New task is created: {conversation_id}")
    print(f"Message: {message}")
    print("======")
    # Start the task execution with the given conversation_id
    asyncio.create_task(
        execute_dummy_task(str(conversation_id), str(task_status_file_path))
    )


def get_dummy_task_status(
    conversation_id: int, task_status_file_path: Path = TASK_STATUS_FILE_PATH
) -> Dict[str, Union[str, bool]]:
    task_status = read_json_file(str(task_status_file_path))
    return task_status.get(str(conversation_id), {})  # type: ignore[no-any-return]
