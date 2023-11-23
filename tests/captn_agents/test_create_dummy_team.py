# test_status_updater.py

import pytest
import asyncio
from captn.captn_agents.backend.create_dummy_team import create_dummy_task, get_dummy_task_status

@pytest.mark.asyncio
async def test_dummy_task_creation():
    conversation_id = "test_conv_1"
    message = "Some message"
    create_dummy_task(conversation_id, message)
    
    # Initially, the status should be inprogress
    await asyncio.sleep(1)
    assert get_dummy_task_status(conversation_id) == {"status": "inprogress", "msg": ""}
    
    await asyncio.sleep(16)  # Wait for the first task to complete (15 seconds + 1 second buffer)
    assert get_dummy_task_status(conversation_id) == {"status": "ready", "msg": "I have a question. What is your name?"}

    # call create_dummy_task for the second time
    create_dummy_task(conversation_id, message)
    
    # After the second creation, the status should reset to inprogress
    await asyncio.sleep(1)
    assert get_dummy_task_status(conversation_id) == {"status": "inprogress", "msg": ""}
    
    await asyncio.sleep(21)  # Wait for the second task to complete (20 seconds + 1 second buffer)
    assert get_dummy_task_status(conversation_id) == {"status": "ready", "msg": "Nevermind. I know the answer already."}