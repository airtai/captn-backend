import ast
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import autogen
from autogen.agentchat.contrib.web_surfer import WebSurferAgent  # noqa: E402
from pydantic import BaseModel
from typing_extensions import Annotated

from ....google_ads.client import execute_query
from ...model import SmartSuggestions
from ..config import Config

__all__ = (
    "Context",
    "reply_to_client_2",
    "ask_client_for_permission",
    "ask_client_for_permission_description",
    "get_info_from_the_web_page",
    "get_info_from_the_web_page_description",
    "send_email",
    "send_email_description",
)


reply_to_client_2_description = """Respond to the client (answer to his task or question for additional information).
Use 'smart_suggestions' parameter to suggest the next steps to the client when ever it is possible, or you will be penalized!
Do NOT just copy half of the message which you are sending and use it as a smart suggestion!
Smart suggestions are used to suggest the next steps to the client. It will be displayed as quick replies in the chat so make them short and clear!
Do NOT use smart suggestions when you are sending login url to the client!"""

smart_suggestions_description = """Quick replies which the client can use for replying to the 'message' which we are sending to him.
This parameter must be dictionary with two keys: 'suggestions': List[str] (a list of suggestions) and 'type': Literal["oneOf", "manyOf"] (option which indicates if the client can select only one or multiple suggestions).
It is neccecery that the Pydantic model SmartSuggestions can be generated from this dictionary (SmartSuggestions(**smart_suggestions))!"""


class TeamResponse(BaseModel):
    message: str
    smart_suggestions: Dict[str, Union[List[str], str]]
    is_question: bool
    status: str
    terminate_groupchat: bool


def reply_to_client_2(
    message: Annotated[str, "Message for the client"],
    completed: Annotated[
        bool, "Has the team completed the task or are they waiting for additional info"
    ],
    smart_suggestions: Annotated[
        Optional[Dict[str, Union[str, List[str]]]], smart_suggestions_description
    ] = None,
) -> str:
    if smart_suggestions:
        smart_suggestions_model = SmartSuggestions(**smart_suggestions)
        smart_suggestions = smart_suggestions_model.model_dump()
    else:
        smart_suggestions = {"suggestions": [""], "type": ""}

    return_msg = TeamResponse(
        message=message,
        smart_suggestions=smart_suggestions,
        is_question=True,
        status="completed" if completed else "pause",
        terminate_groupchat=True,
    )

    return return_msg.model_dump_json()


YES_OR_NO_SMART_SUGGESTIONS = SmartSuggestions(
    suggestions=["Yes", "No"], type="oneOf"
).model_dump()


@dataclass
class Context:
    user_id: int
    conv_id: int
    clients_question_answer_list: List[Tuple[str, Optional[str]]]
    get_only_non_manager_accounts: bool = False


ask_client_for_permission_description = """Ask the client for permission to make the changes. Use this method before calling any of the modification methods!
Use 'resource_details' to describe in detail the resource which you want to modify (all the current details of the resource) and 'proposed_changes' to describe the changes which you want to make.
Do NOT use this method before you have all the information about the resource and the changes which you want to make!
This method should ONLY be used when you know the exact resource and exact changes which you want to make and NOT for the general questions like: 'Do you want to update keywords?'.
Also, propose one change at a time. If you want to make multiple changes, ask the client for the permission for each change separately i.e. before each modification, use this method to ask the client for the permission.
At the end of the message, inform the client that the modifications will be made ONLY if he answers explicitly 'Yes'."""

resource_details_description = """Make sure you add all the information which the client needs to know, because the client does NOT see the internal team messages!
You MUST also describe to the client the current situation for that resource.
If you want to modify the Ad Copy, you MUST provide the current Ad Copy details, e.g:
The current Ad Copy contains 3 headlines and 2 descriptions. The headlines are 'h1', 'h2' and 'h3'. The descriptions are 'd1' and 'd2'.

If you want to modify the keywords, you MUST provide the current keywords details, e.g:
Ad Group 'ag1' contains 5 keywords. The keywords are 'k1', 'k2', 'k3', 'k4' and 'k5'."""

proposed_changes_description = """Explains which changes you want to make and why you want to make them.
I suggest adding new headline 'new-h' because it can increase the CTR and the number of conversions.
You MUST also tell about all the fields which will be effected by the changes, e.g.:
'status' will be changed from 'ENABLED' to 'PAUSED'
Budget will be set to 2$ ('cpc_bid_micros' will be changed from '1000000' to '2000000')

e.g. for AdGroupAd:
'final_url' will be set to 'https://my-web-page.com'
Hedlines will be extended with a list 'hedlines' ['h1', 'h2', 'h3', 'new-h']

Do you approve the changes? To approve the changes, please answer 'Yes' and nothing else."""


def ask_client_for_permission(
    customer_id: Annotated[str, "Id of the customer for whom the changes will be made"],
    resource_details: Annotated[str, resource_details_description],
    proposed_changes: Annotated[str, proposed_changes_description],
    context: Context,
) -> str:
    user_id = context.user_id
    conv_id = context.conv_id
    clients_question_answer_list = context.clients_question_answer_list

    query = f"SELECT customer.descriptive_name FROM customer WHERE customer.id = '{customer_id}'"  # nosec: [B608]
    query_result = execute_query(
        user_id=user_id, conv_id=conv_id, customer_ids=[customer_id], query=query
    )
    descriptiveName = ast.literal_eval(query_result)[customer_id][0]["customer"][  # type: ignore
        "descriptiveName"
    ]

    customer_to_update = f"We propose changes for the following customer: '{descriptiveName}' (ID: {customer_id})"
    message = f"{customer_to_update}\n\n{resource_details}\n\n{proposed_changes}"

    clients_question_answer_list.append((message, None))

    return reply_to_client_2(
        message=message, completed=False, smart_suggestions=YES_OR_NO_SMART_SUGGESTIONS
    )


config = Config()

llm_config_gpt_4 = {
    "timeout": 600,
    "config_list": config.config_list_gpt_4,
    "temperature": 0,
}

llm_config_gpt_3_5 = {
    "timeout": 600,
    "config_list": config.config_list_gpt_3_5,
    "temperature": 0,
}

get_info_from_the_web_page_description = """Retrieve wanted information from the web page.
There is no need to test this function (by sending url: https://www.example.com).
NEVER use this function for scraping Google Ads pages (e.g. https://ads.google.com/aw/campaigns?campaignId=1212121212)
"""


def get_info_from_the_web_page(
    url: Annotated[str, "The url of the web page which needs to be summarized"],
    task: Annotated[
        str,
        """Task which needs to be solved.
This parameter should NOT mention that we are working on some Google Ads task.
The focus of the task is usually retrieving the information from the web page e.g.: categories, products, services etc.
""",
    ],
    task_guidelines: Annotated[
        str,
        """Guidelines which will help you to solve the task. What information are we looking for, what questions need to be answered, etc.
This parameter should NOT mention that we are working on some Google Ads task.
""",
    ],
) -> str:
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
        human_input_mode="NEVER",
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
"Click the 'Next' button"

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
You should respond with 'FAILED' ONLY if you were NOT able to retrieve ANY information from the web page! Otherwise, you should respond with 'SUMMARY' and the summary of your findings.
"""
    user_proxy = autogen.AssistantAgent(
        "user_proxy",
        # human_input_mode="NEVER",
        # code_execution_config=False,
        llm_config=llm_config_gpt_3_5,
        system_message=user_system_message,
    )

    initial_message = f"URL: {url}\nTASK: {task}"
    user_proxy.initiate_chat(web_surfer, message=initial_message)

    return str(user_proxy.last_message()["content"])


send_email_description = "Send email to the client."


def send_email(
    proposed_user_actions: Annotated[List[str], "List of proposed user actions"],
) -> Dict[str, Any]:
    return_msg = {
        "subject": "Capt’n.ai Daily Analysis",
        "email_content": "<html></html>",
        "proposed_user_action": proposed_user_actions,
        "terminate_groupchat": True,
    }
    return return_msg
