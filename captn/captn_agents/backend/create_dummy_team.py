import ast
import asyncio
from typing import Dict, Union

from prisma.errors import RecordNotFoundError
from prisma.models import Task

from captn.captn_agents.application import CaptnAgentRequest, chat
from captn.captn_agents.helpers import get_db_connection

NOTIFICATION_MSG = """
## 📢 Notification from **{}**:

<br/>

{}

<br/>
"""


async def create_task(
    *,
    team_id: int,
    user_id: int,
    chat_id: int,
    team_name: str,
    team_status: str,
    msg: str,
    is_question: bool,
) -> Task:
    data = locals()
    async with get_db_connection() as db:  # type: ignore[var-annotated]
        task: Task = await db.task.create(data=data)
    return task


async def get_task(*, team_id: int) -> Task:
    async with get_db_connection() as db:  # type: ignore[var-annotated]
        task: Task = await db.task.find_unique_or_raise(where={"team_id": team_id})
    return task


async def update_task(team_id: int, **kwargs: Union[int, str, bool]) -> Task:
    async with get_db_connection() as db:  # type: ignore[var-annotated]
        task: Task = await db.task.update(where={"team_id": team_id}, data=kwargs)
    return task


async def create_new_task(
    user_id: int, chat_id: int, conversation_id: int, team_name: str, message: str
) -> Task:
    task = await create_task(
        team_id=conversation_id,
        user_id=user_id,
        chat_id=chat_id,
        team_name=team_name,
        team_status="inprogress",
        msg="",
        is_question=False,
    )
    return task


async def update_existing_task(
    task: Task, user_id: int, conversation_id: int, message: str, team_name: str
) -> Task:
    task = await update_task(
        team_id=conversation_id,
        team_name=team_name,
        team_status="inprogress",
        msg="",
        is_question=False,
    )
    request_obj = CaptnAgentRequest(
        message=message, user_id=user_id, conv_id=conversation_id
    )
    response = ast.literal_eval(chat(request_obj))
    last_message = response["message"]
    status = response["status"]
    is_question = response["is_question"]
    task = await update_task(
        team_id=task.team_id,
        team_status=status,
        msg=NOTIFICATION_MSG.format(team_name, last_message),
        is_question=is_question,
    )
    return task


async def execute_dummy_task(
    user_id: int, chat_id: int, conversation_id: int, team_name: str, message: str
) -> None:
    try:
        task = await get_task(team_id=conversation_id)
    except RecordNotFoundError:
        task = await create_new_task(
            user_id, chat_id, conversation_id, team_name, message
        )
    await update_existing_task(task, user_id, conversation_id, message, team_name)


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
    asyncio.create_task(
        execute_dummy_task(user_id, chat_id, conversation_id, team_name, message)
    )


async def get_dummy_task_status(
    conversation_id: int,
) -> Dict[str, Union[str, bool, int]]:
    task = await get_task(team_id=conversation_id)
    d = task.model_dump()
    exclude_columns = ["created_at", "updated_at"]
    result = {k: v for k, v in d.items() if k not in exclude_columns}  # type: ignore
    return result
