import asyncio

# Global variable to keep track of the status of tasks
TASK_STATUS = {}

async def execute_dummy_task(conversation_id):
    global TASK_STATUS

    if conversation_id not in TASK_STATUS:
        # If conversation_id is not in TASK_STATUS, create new entry
        TASK_STATUS[conversation_id] = {"status": "inprogress", "msg": ""}
        await asyncio.sleep(15)
        TASK_STATUS[conversation_id] = {"status": "ready", "msg": "I have a question. What is your name?"}
    else:
        # If conversation_id already exists in TASK_STATUS, reset and update
        TASK_STATUS[conversation_id] = {"status": "inprogress", "msg": ""}
        await asyncio.sleep(20)
        TASK_STATUS[conversation_id] = {"status": "ready", "msg": "I have an answer for your question"}

async def create_dummy_task(conversation_id):
    # Start the task execution with the given conversation_id
    asyncio.create_task(execute_dummy_task(conversation_id))

def get_dummy_task_status(conversation_id):
    return TASK_STATUS.get(conversation_id, {})