from typing import Any, Dict, List, Optional, Union
from unittest.mock import patch

import autogen
from autogen.agentchat.contrib.web_surfer import WebSurferAgent  # noqa: E402
from typing_extensions import Annotated

from captn.captn_agents.backend.config import config_list_gpt_3_5, config_list_gpt_4

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


llm_config = {
    "timeout": 600,
    "config_list": config_list_gpt_4,
    "temperature": 0,
}

summarizer_llm_config = {
    "timeout": 600,
    "config_list": config_list_gpt_3_5,
    "temperature": 0,
}


# WebSurferAgent is implemented to always aks for the human input at the end of the chat.
# This patch will reply with "exit" to the input() function.
@patch("builtins.input", lambda *args: "exit")
def get_web_page_summary(url: str, summary_creation_guidelines: str) -> str:
    google_ads_url = "ads.google.com"
    if google_ads_url in url:
        return "FAILED: This function should NOT be used for scraping google ads!"

    web_surfer = WebSurferAgent(
        "web_surfer",
        llm_config=llm_config,
        summarizer_llm_config=summarizer_llm_config,
        browser_config={"viewport_size": 4096, "bing_api_key": None},
        is_termination_msg=lambda x: "SUMMARY" in x["content"]
        or "FAILED" in x["content"],
    )

    user_system_message = f"""You are in charge of navigating the web_surfer agent to scrape the web.
web_surfer is able to click on links, scroll down, and scrape the content of the web page. e.g. you cen tell him: "Click the 'Getting Started' result".
Do NOT try to click all the links on the page, but only the ones which are RELEVANT for the task!
Your final goal is to summarize the content of the scraped page. The summary must be in English!
GUIDELINES: {summary_creation_guidelines}

If successful, your last message needs to start with "SUMMARY:" and then you need to write the summary.

Otherwise, your last message needs to start with "FAILED:" and then you need to write the reason why you failed.
"""
    user_proxy = autogen.UserProxyAgent(
        "user_proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
        llm_config=llm_config,
        system_message=user_system_message,
    )

    task1 = f"Get all info from the {url}"
    user_proxy.initiate_chat(web_surfer, message=task1)

    return str(user_proxy.last_message()["content"])
