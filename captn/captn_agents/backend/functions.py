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


llm_config_gpt_4 = {
    "timeout": 600,
    "config_list": config_list_gpt_4,
    "temperature": 0,
}

llm_config_gpt_3_5 = {
    "timeout": 600,
    "config_list": config_list_gpt_3_5,
    "temperature": 0,
}


# WebSurferAgent is implemented to always aks for the human input at the end of the chat.
# This patch will reply with "exit" to the input() function.
@patch("builtins.input", lambda *args: "exit")
def get_info_from_the_web_page(url: str, task: str, task_guidelines: str) -> str:
    google_ads_url = "ads.google.com"
    if google_ads_url in url:
        return "FAILED: This function should NOT be used for scraping google ads!"

    web_surfer = WebSurferAgent(
        "web_surfer",
        llm_config=llm_config_gpt_4,
        summarizer_llm_config=llm_config_gpt_3_5,
        browser_config={"viewport_size": 4096, "bing_api_key": None},
        is_termination_msg=lambda x: "SUMMARY" in x["content"]
        or "FAILED" in x["content"],
    )

    user_system_message = f"""You are in charge of navigating the web_surfer agent to scrape the web.
web_surfer is able to CLICK on links, SCROLL down, and scrape the content of the web page. e.g. you cen tell him: "Click the 'Getting Started' result".
Each time you receive a reply from web_surfer, you need to tell him what to do next. e.g. "Click the TV link" or "Scroll down".
It is very important that you explore ALL the page links relevant for the task!

GUIDELINES:
- {task_guidelines}
- Once you retrieve the content from the received url, you can tell web_surfer to CLICK on links, SCROLL down...
By using these capabilities, you will be able to retrieve MUCH BETTER information from the web page than by just scraping the given URL!
You MUST use these capabilities when you receive a task for a specific category/product etc.
Examples:
"Click the 'TVs' result" - This way you will navigate to the TVs section of the page and you will find more information about TVs.
"Click 'Electronics' link" - This way you will navigate to the Electronics section of the page and you will find more information about Electronics.
"Cick the 'Next' button"

- Do NOT try to click all the links on the page, but only the ones which are RELEVANT for the task! Web pages can be very long and you will be penalized if spend too much time on this task!
- Your final goal is to summarize the findings for the given task. The summary must be in English!
- Create a summary after you have retrieved ALL the relevant information from ALL the pages which you think are relevant for the task!
- It is also useful to include in the summary relevant links where more information can be found.
e.g. If the page is offering to sell TVs, you can include a link to the TV section of the page.
- If you get some 40x error, please do NOT give up immediately, but try to navigate to another page and continue with the task. Give up only if you get 40x error on ALL the pages which you tried to navigate to.


FINAL MESSAGE:
If successful, your last message needs to start with "SUMMARY:" and then you need to write the summary.
Note: NEVER suggest the next steps in the summary! It is NOT your job to do that!

Suggest 15 relevant headlines where each headline has MAXIMUM 30 characters (including spaces). (headlines are often similar to keywords)
Suggest 4 relevant descriptions where each description has MAXIMUM 90 characters (including spaces).

Example
'''
SUMMARY:

Page content: The store offers a variety of electronic categories including Air Conditioners, Kitchen Appliances, PCs & Laptops, Gadgets, Smart Home devices, Home Appliances, Audio & Video equipment, and Refrigerators.
Relevant links:
- Air Conditioners: https://store-eg.net/product-category/air-conditioner/
- Kitchen Appliances: https://store-eg.net/product-category/kitchen-appliances/
- PCs & Laptops: https://store-eg.net/product-category/pcs-laptop/
- Gadgets: https://store-eg.net/product-category/gadgets/
- Smart Home: https://store-eg.net/product-category/smart-home/
- Home Appliances: https://store-eg.net/product-category/home-appliances/
- Audio & Video: https://store-eg.net/product-category/audio-video/
- Refrigerators: https://store-eg.net/product-category/refrigerator/
- New Arrivals: https://store-eg.net/new-arrivals/

## Keywords: store, electronic, Air Conditioners, Kitchen Appliances, PCs & Laptops, Gadgets, Smart Home devices, Home Appliances, Audio & Video equipment, Refrigerators
## Headlines (MAX 30 char each): store, electronic, Air Conditioners, Kitchen Appliances, PCs & Laptops, Gadgets, Smart Home devices, Home Appliances, Audio & Video equipment, Refrigerators, New Arrivals
## Descriptions (MAX 90 char each): Best store for electronic devices in Europe, Buy electronic devices online, Save 20% on electronic devices, Top quality electronic devices
(VERY IMPORTANT: each headline has LESS than 30 characters and each description has LESS than 90 characters)

Use these information to SUGGEST the next steps to the client, but do NOT make any permanent changes without the client's approval!
'''

Otherwise, your last message needs to start with "FAILED:" and then you need to write the reason why you failed.
If some links are not working, try navigating to the previous page or the home page and continue with the task.
You shold respond with 'FAILED' ONLY if you were NOT able to retrieve ANY information from the web page! Otherwise, you should respond with 'SUMMARY' and the summary of your findings.
"""
    user_proxy = autogen.UserProxyAgent(
        "user_proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
        llm_config=llm_config_gpt_3_5,
        system_message=user_system_message,
    )

    initial_message = f"URL: {url}\nTASK: {task}"
    user_proxy.initiate_chat(web_surfer, message=initial_message)

    return str(user_proxy.last_message()["content"])


def send_email(
    client_email: str,
    daily_analysis: str,
    proposed_user_actions: List[str],
) -> Dict[str, Any]:
    final_message = "Daily Analysis:\n" + daily_analysis + "\n\n"

    conv_id = 409
    proposed_user_actions_paragraph = "Proposed User Actions:\n"
    for i, action in enumerate(proposed_user_actions):
        proposed_user_actions_paragraph += f"{i+1}. {action} (https://captn.ai/chat/{conv_id}?selected_user_action={i+1})\n"

    final_message += proposed_user_actions_paragraph

    print(final_message)
    return_msg = {
        "final_message": final_message,
        "terminate_groupchat": True,
    }
    return return_msg
