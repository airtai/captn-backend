from typing import Any, Dict, List, Optional


def ask_for_additional_info(question: str) -> str:
    return f"QUESTION FROM ANOTHER TEAM:\n{question}\nPAUSE"


def reply_to_client(message: str) -> str:
    return f"{message}\nPAUSE"


def reply_to_client_2(
    message: str,
    is_question: bool,
    completed: bool,
    smart_suggestions: List[Optional[str]],
) -> Dict[str, Any]:
    # REMOVE THIS LINE!!!!
    message += "\n\nSMART SUGGESTIONS:\n" + str(smart_suggestions)

    return_msg = {
        "message": message,
        "smart_suggestions": smart_suggestions,
        # is_question must be true, otherwise text input box will not be displayed in the chat
        "is_question": True,  # is_question,
        "status": "completed" if completed else "pause",
        "terminate_groupchat": True,
    }
    return return_msg
