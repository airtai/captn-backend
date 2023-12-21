from typing import Any, Dict


def ask_for_additional_info(question: str) -> str:
    return f"QUESTION FROM ANOTHER TEAM:\n{question}\nPAUSE"


def reply_to_client(message: str) -> str:
    return f"{message}\nPAUSE"


def reply_to_client_2(
    message: str, is_question: bool, completed: bool
) -> Dict[str, Any]:
    return_msg = {
        "message": message,
        # is_question must be true, otherwise text input box will not be displayed in the chat
        "is_question": True,  # is_question,
        "status": "completed" if completed else "pause",
        "terminate_groupchat": True,
    }
    return return_msg


def ask_client_for_approval_before_change_making(
    message: str, command_to_execute: str, resource_to_modify: str
) -> Dict[str, Any]:
    return reply_to_client_2(message=message, is_question=True, completed=False)
