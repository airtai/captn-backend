from typing import Any, Dict, List

from ..model import SmartSuggestions


def ask_for_additional_info(question: str) -> str:
    return f"QUESTION FROM ANOTHER TEAM:\n{question}\nPAUSE"


def reply_to_client(message: str) -> str:
    return f"{message}\nPAUSE"


def reply_to_client_2(
    message: str,
    completed: bool,
    smart_suggestions_list: List[str],
    suggestions_type: str,
) -> Dict[str, Any]:
    smart_suggestions = SmartSuggestions(
        suggestions=smart_suggestions_list, suggestions_type=suggestions_type
    )
    print(f"smart_suggestions: {smart_suggestions}")

    return_msg = {
        "message": message,
        "smart_suggestions_new": smart_suggestions.model_dump(),
        "smart_suggestions": smart_suggestions_list,
        # is_question must be true, otherwise text input box will not be displayed in the chat
        "is_question": True,
        "status": "completed" if completed else "pause",
        "terminate_groupchat": True,
    }
    return return_msg
