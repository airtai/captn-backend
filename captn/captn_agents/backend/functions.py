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
        "is_question": is_question,
        # Always return status: "pause"
        "status": "pause" # "completed" if completed else "pause",
    }
    return return_msg
