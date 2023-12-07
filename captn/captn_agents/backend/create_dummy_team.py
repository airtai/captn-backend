import asyncio
from os import environ
from typing import Dict, Union

from prisma.errors import RecordNotFoundError
from prisma.models import Task

from captn.captn_agents.application import CaptnAgentRequest, chat
from captn.captn_agents.helpers import get_db_connection

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


async def create_task(
    *,
    team_id: int,
    user_id: int,
    chat_id: int,
    team_name: str,
    team_status: str,
    msg: str,
    is_question: bool,
    call_counter: int,
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
        task: Task = await db.task.upsert(
            where={"team_id": team_id},
            data={
                "create": {**{"team_id": team_id}, **kwargs},
                "update": kwargs,
            },
        )
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
        call_counter=0,
    )
    # await asyncio.sleep(15)
    request_obj = CaptnAgentRequest(
        message=message, user_id=user_id, conv_id=conversation_id
    )
    # last_message, is_question, status= chat(request_obj)
    # todo: add try except block
    last_message = chat(request_obj)
    task = await update_task(
        team_id=task.team_id,
        team_status="pause",
        msg=NOTIFICATION_MSG.format(team_name, last_message),
        call_counter=task.call_counter + 1,
    )
    return task


async def ask_question(chat_id: int, conversation_id: int, team_name: str) -> None:
    task = await get_task(team_id=conversation_id)
    task = await update_task(
        team_id=conversation_id,
        team_name=team_name,
        team_status="inprogress",
        msg="",
        is_question=True,
        call_counter=task.call_counter,
    )
    await asyncio.sleep(15)
    task = await update_task(
        team_id=task.team_id,
        team_status="pause",
        msg=QUESTION_MSG.format(team_name),
        call_counter=task.call_counter + 1,
    )


async def complete_task(chat_id: int, conversation_id: int, team_name: str) -> None:
    task = await get_task(team_id=conversation_id)
    task = await update_task(
        team_id=conversation_id,
        team_name=team_name,
        team_status="inprogress",
        msg="",
        is_question=False,
        call_counter=task.call_counter,
    )
    await asyncio.sleep(15)
    task = await update_task(
        team_id=task.team_id,
        team_status="completed",
        msg=ANSWER_MSG.format(team_name),
        call_counter=task.call_counter + 1,
    )


async def execute_dummy_task(
    user_id: int, chat_id: int, conversation_id: int, team_name: str, message: str
) -> None:
    try:
        task = await get_task(team_id=conversation_id)
    except RecordNotFoundError:
        task = await create_new_task(
            user_id, chat_id, conversation_id, team_name, message
        )

    if task.call_counter == 1:
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
        execute_dummy_task(user_id, chat_id, conversation_id, team_name, message)
    )


def get_dummy_task_status(conversation_id: int) -> Dict[str, Union[str, bool]]:
    task = asyncio.run(get_task(team_id=conversation_id))
    d = task.model_dump()
    exclude_columns = ["call_counter", "created_at", "updated_at"]
    return {k: v for k, v in d.items() if k not in exclude_columns}  # type: ignore
