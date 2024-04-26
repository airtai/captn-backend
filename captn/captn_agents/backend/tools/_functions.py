import ast
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

import autogen
from autogen.agentchat.contrib.web_surfer import WebSurferAgent  # noqa: E402
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator
from typing_extensions import Annotated

from ....google_ads.client import execute_query
from ...model import SmartSuggestions
from ..config import Config

__all__ = (
    "Context",
    "reply_to_client",
    "ask_client_for_permission",
    "ask_client_for_permission_description",
    "get_get_info_from_the_web_page",
    "get_info_from_the_web_page_description",
    "send_email",
    "send_email_description",
)


reply_to_client_description = """Respond to the client (answer to his task or question for additional information).
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


class WebPageSummary(BaseModel):
    url: HttpUrl
    title: str
    page_summary: str
    keywords: List[str]
    headlines: List[str]
    descriptions: List[str]


class Summary(BaseModel):
    type: Literal["SUMMARY"] = "SUMMARY"
    summary: str
    relevant_pages: List[WebPageSummary]


example = Summary(
    summary="Page content: The store offers a variety of electronic categories including Air Conditioners, Refrigerators, Kitchen Appliances, PCs & Laptops and Gadgets",
    relevant_pages=[
        WebPageSummary(
            url="https://store-eg.net/product-category/air-conditioner/",
            title="Air Conditioners",
            page_summary="Product pages for air conditioners",
            keywords=[
                "Air Conditioners",
                "Cooling",
                "HVAC",
                "Energy Efficiency",
                "Smart Features",
                "Quiet Operation",
            ],
            headlines=[
                "Cool Comfort, Anywhere",
                "Beat the Heat with Ease",
                "Stay Chill All Summer",
                "Your Cooling Solution",
                "Ultimate Climate Control",
                "AC: Your Hot Weather Ally",
            ],
            descriptions=[
                "Powerful cooling for any space",
                "Effortless control, maximum comfort",
                "Whisper-quiet operation for peace",
                "Smart features for smarter living",
            ],
        ),
        WebPageSummary(
            url="https://store-eg.net/product-category/refrigerator/",
            title="Refrigerators",
            page_summary="Product pages for refrigerators",
            keywords=[
                "Refrigerators",
                "Cooling",
                "Energy Efficiency",
                "Smart Features",
                "Freshness Preservation",
                "Style",
                "Spacious Design",
            ],
            headlines=[
                "Freshness Preserved",
                "Cool Convenience",
                "Keep it Fresh",
                "Ultimate Food Storage",
                "Smart Refrigeration",
                "Stylish Cooling",
                "Space-Saving Solutions",
            ],
            descriptions=[
                "Keep your food fresh longer",
                "Convenient control for maximum freshness",
                "Peaceful operation for your kitchen",
                "Smart features for fresher food",
            ],
        ),
    ],
)


def reply_to_client(
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

    return reply_to_client(
        message=message, completed=False, smart_suggestions=YES_OR_NO_SMART_SUGGESTIONS
    )


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


class WebUrl(BaseModel):
    url: Annotated[
        HttpUrl,
        Field(description="The url of the web page which needs to be summarized"),
    ]

    @field_validator("url", mode="before")
    def validate_url(cls, v: str) -> str:
        google_ads_url = "ads.google.com"
        if google_ads_url in v:
            raise ValueError(
                "FAILED: This function should NOT be used for scraping google ads!"
            )

        # add https if protocol is missing
        if isinstance(v, str) and not v.startswith("http"):
            return f"https://{v}"
        return v


def _create_web_surfer_navigator_system_message(task_guidelines: str) -> str:
    return f"""You are in charge of navigating the web_surfer agent to scrape the web.
web_surfer is able to CLICK on links, SCROLL down, and scrape the content of the web page. e.g. you cen tell him: "Click the 'Getting Started' result".
Each time you receive a reply from web_surfer, you need to tell him what to do next. e.g. "Click the TV link" or "Scroll down".
It is very important that you explore ONLY the page links relevant for the task!

GUIDELINES:
- {task_guidelines}
- Once you retrieve the content from the received url, you can tell web_surfer to CLICK on links, SCROLL down...
By using these capabilities, you will be able to retrieve MUCH BETTER information from the web page than by just scraping the given URL!
You MUST use these capabilities when you receive a task for a specific category/product etc.
It is recommended to Clck on MAXIMUM 10 links. Do NOT try to click all the links on the page, but only the ones which are most relevant for the task (MAX 10)!
On the other hand, do NOT try to create a summary without clicking on any link, because you will be missing a lot of information!

Examples:
"Click the 'TVs' result" - This way you will navigate to the TVs section of the page and you will find more information about TVs.
"Click 'Electronics' link" - This way you will navigate to the Electronics section of the page and you will find more information about Electronics.
"Click the 'Next' button"

- Do NOT try to click all the links on the page, but only the ones which are RELEVANT for the task! Web pages can be very long and you will be penalized if spend too much time on this task!
- Your final goal is to summarize the findings for the given task. The summary must be in English!
- Create a summary after you successfully retrieve the information from the web page.
- It is useful to include in the summary relevant links where more information can be found.
e.g. If the page is offering to sell TVs, you can include a link to the TV section of the page.
- If you get some 40x error, please do NOT give up immediately, but try to navigate to another page and continue with the task.
Give up only if you get 40x error on ALL the pages which you tried to navigate to.


FINAL MESSAGE:
If successful, your last message MUST be JSON-encoded summary according to the following JSON schema:
{example.model_json_schema()}

You MUST not include any other text or formatting in the message, only JSON-encoded summary!

This is an example of correctly formatted JSON (unrelated to the task):
```json
{example.model_dump_json()}
```

TERMINATION:
When you are finished, write a single 'TERMINATE' to end the task.

VERY IMPORTANT:
- each headline must have LESS than 30 characters and each description must have LESS than 90 characters
- generate EXACTLY 15 headlines and 4 descriptions for EACH link which you think is relevant for the Google Ads campaign!
- if not explicitly told, do NOT include links like 'About Us', 'Contact Us' etc. in the summary.
We are interested ONLY in the products/services which the page is offering.
- NEVER include in the summary links which return 40x error!

If you are NOT able to retrieve ANY information from the web page, your last message needs to start with "FAILED:" and then you need to write the reason why you failed.
If some links are not working, try navigating to the previous page or the home page and continue with the task.
If you are able to retrieve any information, create a summary and do NOT return FAILED message!
A message should NEVER contain both "FAILED:" and "SUMMARY:"!
"""


def get_get_info_from_the_web_page(
    outer_retries: int = 3,
    inner_retries: int = 10,
    summarizer_llm_config: Dict[str, Any] = llm_config_gpt_3_5,
    websurfer_llm_config: Dict[str, Any] = llm_config_gpt_4,
    websurfer_navigator_llm_config: Dict[str, Any] = llm_config_gpt_3_5,
    timestamp: Optional[str] = None,
) -> Callable[[str, str, str], str]:
    def get_info_from_the_web_page(
        url: Annotated[str, "The url of the web page which needs to be summarized"],
        task: Annotated[
            str,
            """Task which needs to be solved.
    The focus of the task is usually retrieving the information from the web page e.g.: categories, products, services etc.
    e.g. I need website summary which will help me create Google Ads ad groups, ads, and keywords for the website.
    """,
        ],
        task_guidelines: Annotated[
            str,
            """Guidelines which will help you to solve the task. What information are we looking for, what questions need to be answered, etc.
    e.g. Please provide a summary of the website, including the products/services offered. The summary will be used to create Google Ads resources based on the information you provide.""",
        ],
    ) -> str:
        web_surfer_navigator_system_message = (
            _create_web_surfer_navigator_system_message(task_guidelines=task_guidelines)
        )
        # validate url, error will be raised if url is invalid
        # Append https if protocol is missing
        url = str(WebUrl(url=url).url)

        last_message = ""
        failure_message = ""
        for _ in range(outer_retries):
            try:
                web_surfer = WebSurferAgent(
                    "web_surfer",
                    llm_config=websurfer_llm_config,
                    summarizer_llm_config=summarizer_llm_config,
                    browser_config={"viewport_size": 4096, "bing_api_key": None},
                    is_termination_msg=lambda x: x["content"].startswith(
                        '{"type":"SUMMARY"'
                    )
                    or x["content"].startswith('{"type": "SUMMARY"')
                    or "TERMINATE" in x["content"]
                    or x["content"].startswith("```json"),
                    # or "FAILED" in x["content"],
                    human_input_mode="NEVER",
                )

                web_surfer_navigator = autogen.AssistantAgent(
                    "web_surfer_navigator",
                    llm_config=websurfer_navigator_llm_config,
                    system_message=web_surfer_navigator_system_message,
                )

                # initial_message = f"""Time now is {datetime.datetime.now().isoformat()}.
                initial_message = f"Time now is {timestamp}." if timestamp else ""
                initial_message += f"""
URL: {url}
TASK: {task}
"""

                web_surfer_navigator.initiate_chat(web_surfer, message=initial_message)

                for _ in range(inner_retries):
                    last_message = str(web_surfer_navigator.last_message()["content"])
                    # print(last_message)
                    try:
                        if "TERMINATE" in last_message:
                            web_surfer.send(
                                "Before terminating, you must provide JSON-encoded summary without any other text or formatting in a message.",
                                recipient=web_surfer_navigator,
                            )
                            continue
                        match = re.search(
                            r"```json\n(.*)\n```", last_message, re.DOTALL
                        )
                        # print(f"{match=}")
                        if match:
                            last_message = match.group(1)
                            # print(f"After match: {last_message=}")
                        summary = Summary.model_validate_json(last_message)
                        if len(summary.relevant_pages) < 3:
                            web_surfer.send(
                                f"FAILED: The summary must include AT LEAST 3 or more relevant pages. You have provided only {len(summary.relevant_pages)} pages. Please try again.",
                                recipient=web_surfer_navigator,
                            )
                            continue
                        print(f"Summary validated: {summary}")
                        return last_message
                    except ValidationError as e:
                        print("Validation error")
                        print(e)
                        web_surfer.send(
                            f"""FAILED to decode provided JSON:
{str(e.errors())}

Please create a new JSON-encoded summary according to the following schema:
{Summary.model_json_schema()}

Example of correctly formatted JSON (unrelated to the task):
```json
{example.model_dump_json()}
```
""",
                            recipient=web_surfer_navigator,
                        )

                    except Exception as e:
                        print("Regular exception")
                        print(e)
                        web_surfer.send(
                            f"FAILED: {str(e)}", recipient=web_surfer_navigator
                        )
            except Exception as e:
                # todo: log the exception
                failure_message = str(e)
                print("Exception")
                print(e)

        last_message = (
            f"This is the best we could do: {last_message}"
            if len(last_message) > 0
            else last_message
        )
        return f"""FAILED: Could not retrieve the information from the web page.
We had the following error:
{failure_message}

{last_message}"""

    return get_info_from_the_web_page


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
