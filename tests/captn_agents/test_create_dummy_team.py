# test_status_updater.py

import pytest
import asyncio
from captn.captn_agents.backend.create_dummy_team import (
    create_dummy_task,
    get_dummy_task_status,
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


@pytest.mark.asyncio
async def test_dummy_task_creation():
    conversation_id = 1000000
    message = "Some message"
    team_name = "Google Ads Team"
    create_dummy_task(conversation_id, message, team_name)
    
    # Initially, the status should be inprogress
    await asyncio.sleep(1)
    assert get_dummy_task_status(conversation_id) == {
            "team_id": f"{conversation_id}",
            "team_name": team_name,
            "team_status": "inprogress",
            "msg": "",
            "is_question": True,
        }
    
    await asyncio.sleep(16)  # Wait for the first task to complete (15 seconds + 1 second buffer)
    assert get_dummy_task_status(conversation_id) == {
            "team_id": f"{conversation_id}",
            "team_name": team_name,
            "team_status": "pause",
            "msg": QUESTION_MSG.format(team_name),
            "is_question": True,
        }

    # call create_dummy_task for the second time
    create_dummy_task(conversation_id, message, team_name)
    
    # After the second creation, the status should reset to inprogress
    await asyncio.sleep(1)
    assert get_dummy_task_status(conversation_id) == {
            "team_id": f"{conversation_id}",
            "team_name": team_name,
            "team_status": "inprogress",
            "msg": "",
            "is_question": False,
        }
    
    await asyncio.sleep(21)  # Wait for the second task to complete (20 seconds + 1 second buffer)
    assert get_dummy_task_status(conversation_id) == {
            "team_id": f"{conversation_id}",
            "team_name": team_name,
            "team_status": "completed",
            "msg": ANSWER_MSG.format(team_name),
            "is_question": False,
        }


    # call create_dummy_task for the second time
    create_dummy_task(conversation_id, message, team_name)

    await asyncio.sleep(16)  # Wait for the first task to complete (15 seconds + 1 second buffer)
    assert get_dummy_task_status(conversation_id) == {
            "team_id": f"{conversation_id}",
            "team_name": team_name,
            "team_status": "pause",
            "msg": QUESTION_MSG.format(team_name),
            "is_question": True,
        }
