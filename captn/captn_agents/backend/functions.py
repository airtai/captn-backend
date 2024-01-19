from typing import Any, Dict, List, Optional, Union

from typing_extensions import Annotated

from ..model import SmartSuggestions


def ask_for_additional_info(question: str) -> str:
    return f"QUESTION FROM ANOTHER TEAM:\n{question}\nPAUSE"


def reply_to_client(message: str) -> str:
    return f"{message}\nPAUSE"


reply_to_client_2_description = """Respond to the client (answer to his task or question for additional information).
Use 'smart_suggestions' parameter to suggest the next steps to the client when ever it is possible, or you will be penalized!
But do NOT use smart suggestions for questions which require clients input!
Do NOT just copy half of the message which you are sending and use it as a smart suggestion!"""

smart_suggestions_description = """Quick replies which the client can use for replying to the 'message' which we are sending to him.
This parameter must be dictionary with two keys: 'suggestions': List[str] and 'type': Literal["oneOf", "manyOf"].
It is neccecery that the Pydantic model SmartSuggestions can be generated from this dictionary (SmartSuggestions(**smart_suggestions))!"""


# @agent.register_for_llm(description=reply_to_client_2_desc)
def reply_to_client_2(
    message: Annotated[str, "Message for the client"],
    completed: Annotated[
        bool, "Has the team completed the task or are they waiting for additional info"
    ],
    smart_suggestions: Annotated[
        Optional[Dict[str, Union[str, List[str]]]], smart_suggestions_description
    ] = None,
) -> Dict[str, Any]:
    if smart_suggestions:
        smart_suggestions_model = SmartSuggestions(**smart_suggestions)
        smart_suggestions = smart_suggestions_model.model_dump()
    else:
        smart_suggestions = {"suggestions": [""], "type": ""}

    return_msg = {
        "message": message,
        "smart_suggestions": smart_suggestions,
        # is_question must be true, otherwise text input box will not be displayed in the chat
        "is_question": True,
        "status": "completed" if completed else "pause",
        "terminate_groupchat": True,
    }
    return return_msg
