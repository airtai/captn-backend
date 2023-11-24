import asyncio

# Global variable to keep track of the status of tasks
TASK_STATUS = {}

QUESTION_MSG = """
## 📢 Notification from our team: 

👋 Hey there!

Our team has a question for you. Can you please answer the below:

What is your name? 😊"""

ANSWER_MSG = """
## 📢 Notification from our team: 

👋 Hey there!

Your campaign report is ready😊"""

async def execute_dummy_task(conversation_id):
    global TASK_STATUS

    if (conversation_id not in TASK_STATUS) or (not TASK_STATUS[conversation_id]["is_question"]):
        # If conversation_id is not in TASK_STATUS, create new entry
        TASK_STATUS[conversation_id] = {"status": "inprogress", "msg": "", "is_question": True}
        await asyncio.sleep(15)
        TASK_STATUS[conversation_id]["status"] = "ready"
        TASK_STATUS[conversation_id]["msg"] = QUESTION_MSG
    else:
        # If conversation_id already exists in TASK_STATUS, reset and update
        TASK_STATUS[conversation_id] = {"status": "inprogress", "msg": "", "is_question": not TASK_STATUS[conversation_id]["is_question"]}
        await asyncio.sleep(20)
        TASK_STATUS[conversation_id]["status"] = "ready"
        TASK_STATUS[conversation_id]["msg"] = ANSWER_MSG

def create_dummy_task(conversation_id, message):
    # Start the task execution with the given conversation_id
    asyncio.create_task(execute_dummy_task(conversation_id))
    print("======")
    print(f"New task is created: {conversation_id}")
    print(f"Message: {message}")
    print("======")

def get_dummy_task_status(conversation_id):
    return TASK_STATUS.get(conversation_id, {})