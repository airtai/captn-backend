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
    }
    return return_msg
