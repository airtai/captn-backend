import ast
import datetime
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

import autogen
import requests
from annotated_types import Len
from autogen.agentchat import AssistantAgent
from autogen.agentchat.contrib.web_surfer import WebSurferAgent  # noqa: E402
from autogen.cache import Cache
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
    "get_webpage_status_code",
    "LAST_MESSAGE_BEGINNING",
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
    keywords: Annotated[List[str], Len(min_length=1)]
    headlines: Annotated[List[str], Len(min_length=3, max_length=15)]
    descriptions: Annotated[List[str], Len(min_length=2, max_length=4)]


class Summary(BaseModel):
    type: Literal["SUMMARY"] = "SUMMARY"
    summary: str
    relevant_pages: Annotated[List[WebPageSummary], Len(min_length=1)]


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
    message: Annotated[
        str,
        "Message for the client. The message MUST use the Markdown format for the text!",
    ],
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
Ad Group 'ag1' contains 5 keywords. The keywords are 'k1', 'k2', 'k3', 'k4' and 'k5'.

The message MUST use the Markdown format for the text!"""

proposed_changes_description = """Explains which changes you want to make and why you want to make them.
I suggest adding new headline 'new-h' because it can increase the CTR and the number of conversions.
You MUST also tell about all the fields which will be effected by the changes, e.g.:
'status' will be changed from 'ENABLED' to 'PAUSED'
Budget will be set to 2$ ('cpc_bid_micros' will be changed from '1000000' to '2000000')

e.g. for AdGroupAd:
'final_url' will be set to 'https://my-web-page.com'
Hedlines will be extended with a list 'hedlines' ['h1', 'h2', 'h3', 'new-h']

Do you approve the changes? To approve the changes, please answer 'Yes' and nothing else.

The message MUST use the Markdown format for the text!"""

BENCHMARKING = False


def init_chat_and_get_last_message(
    client_system_message: str,
    message: str,
    cache: Optional[Cache] = None,
) -> str:
    # This agent is used only to send the message to the client
    sender = AssistantAgent(
        name="assistant",
        is_termination_msg=lambda x: True,  # Once the client replies, the sender will terminate the conversation
    )

    config_list = Config().config_list_gpt_4

    client = AssistantAgent(
        name="client",
        system_message=client_system_message,
        llm_config={
            "config_list": config_list,
            "temperature": 0,
        },
    )

    sender.initiate_chat(client, message=message, cache=cache)
    # last_message is the last message sent by the client
    last_message = client.chat_messages[sender][-1]["content"]
    return last_message  # type: ignore[no-any-return]


def _ask_client_for_permission_mock(
    resource_details: str,
    proposed_changes: str,
    context: Context,
) -> str:
    customer_to_update = (
        "We propose changes for the following customer: 'IKEA' (ID: 1111)"
    )

    message = f"{customer_to_update}\n\n{resource_details}\n\n{proposed_changes}"

    client_system_message = """We are creating a new Google Ads campaign (ad groups, ads etc).
We are in the middle of the process and we need your permission.

If the proposed changes make sense, Please answer 'Yes' and nothing else.
Otherwise, ask for more information or suggest changes.
But do NOT answer with 'No' if you are not sure. Ask for more information instead.
"""
    # clients_answer = "yes"
    clients_answer = init_chat_and_get_last_message(
        client_system_message=client_system_message,
        message=message,
    )

    # In real ask_client_for_permission, we would append (message, None)
    # and we would update the clients_question_answer_list with the clients_answer in the continue_conversation function
    context.clients_question_answer_list.append((message, clients_answer))
    return clients_answer


def ask_client_for_permission(
    customer_id: Annotated[str, "Id of the customer for whom the changes will be made"],
    resource_details: Annotated[str, resource_details_description],
    proposed_changes: Annotated[str, proposed_changes_description],
    context: Context,
) -> str:
    if BENCHMARKING:
        return _ask_client_for_permission_mock(
            resource_details=resource_details,
            proposed_changes=proposed_changes,
            context=context,
        )
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


def get_llm_config_gpt_4() -> Dict[str, Any]:
    config = Config()

    return {
        "config_list": config.config_list_gpt_4,
        "temperature": 0,
    }


def get_llm_config_gpt_3_5() -> Dict[str, Any]:
    config = Config()

    return {
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
- do NOT try to create a summary without clicking on any link, because you will be missing a lot of information!

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
Once you have retrieved he wanted information, you MUST create JSON-encoded string according to the following JSON schema:
{example.model_json_schema()}

You MUST not include any other text or formatting in the message, only JSON-encoded string!

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

You MUST always reply to the last message from the web_surfer agent! Your reply can NOT be empty message!
"""


LAST_MESSAGE_BEGINNING = "Here is a summary of the information you requested:"


def _format_last_message(summary: Summary) -> str:
    summary_response = f"""{LAST_MESSAGE_BEGINNING}

{summary.summary}

Relevant Pages:
"""

    for i, page in enumerate(summary.relevant_pages):
        summary_response += f"""
{i+1}. {page.title}:
    URL: {page.url}
    Summary: {page.page_summary}
    Keywords: {str(page.keywords)[1:-1]}
    Headlines: {str(page.headlines)[1:-1]}
    Descriptions: {str(page.descriptions)[1:-1]}
"""

    return summary_response


def _is_termination_msg(x: Dict[str, Optional[str]]) -> bool:
    content = x.get("content")
    if content is None or not isinstance(content, str):
        return False
    return (
        content.startswith('{"type":"SUMMARY"')
        or content.startswith('{"type": "SUMMARY"')
        or "TERMINATE" in content
        or "```json" in content
        or "I GIVE UP" in content
    )


def get_webpage_status_code(url: str) -> Optional[int]:
    if "http" not in url:
        url = f"https://{url}"
    try:
        status_code = requests.head(url, allow_redirects=True, timeout=10).status_code
        return status_code
    except requests.ConnectionError:
        return None


_task = """We are tasked with creating a new Google Ads campaign for the website.
In order to create the campaign, we need to understand the website and its products/services.
Our task is to provide a summary of the website, including the products/services offered and any unique selling points.
This is the first step in creating the Google Ads campaign so please gather as much information as possible.
Visit the most likely pages to be advertised, such as the homepage, product pages, and any other relevant pages.
Please provide a detailed summary of the website as JSON-encoded string as instructed in the guidelines.

AFTER visiting the home page, create a step-by-step plan BEFORE visiting the other pages.
e.g.
"Here is a list of the links we will visit:
1. Click the 'Products' link
2. Click the 'Electronics' link
3. Click the 'TVs' link

Now, let's start with the task:
Click no. 1 - Click the 'Products' link"

You can click on MAXIMUM 10 links. Do NOT try to click all the links on the page, but only the ones which are most relevant for the task (MAX 10)!
When clicking on a link, add a comment "Click no. X (I can click MAX 10 links, but I will click only the most relevant ones, once I am done, I need to generate JSON-encoded string)" to the message.
"""

_task_guidelines = "Please provide a summary of the website, including the products/services offered and any unique selling points."


def _constuct_retry_message(
    new_message: str,
    give_up_message: str,
    current_retries: int,
    max_retires_before_give_up_message: int,
) -> str:
    if current_retries < max_retires_before_give_up_message:
        return new_message

    return f"""{new_message}

{give_up_message}
"""


def get_get_info_from_the_web_page(
    outer_retries: int = 3,
    inner_retries: int = 10,
    summarizer_llm_config: Optional[Dict[str, Any]] = None,
    websurfer_llm_config: Optional[Dict[str, Any]] = None,
    websurfer_navigator_llm_config: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
    min_relevant_pages: int = 3,
    max_retires_before_give_up_message: int = 7,
) -> Callable[[str], str]:
    fx = summarizer_llm_config, websurfer_llm_config, websurfer_navigator_llm_config

    give_up_message = f"""ONLY if you are 100% sure that you can NOT retrieve any information for at least {min_relevant_pages} relevant pages,
write 'I GIVE UP' and the reason why you gave up.

But before giving up, please try to navigate to another page and continue with the task. Give up ONLY if you are sure that you can NOT retrieve any information!"""

    def get_info_from_the_web_page(
        url: Annotated[str, "The url of the web page which needs to be summarized"],
    ) -> str:
        summarizer_llm_config, websurfer_llm_config, websurfer_navigator_llm_config = fx

        if summarizer_llm_config is None:
            summarizer_llm_config = get_llm_config_gpt_3_5()
        if websurfer_llm_config is None:
            websurfer_llm_config = get_llm_config_gpt_4()
        if websurfer_navigator_llm_config is None:
            websurfer_navigator_llm_config = get_llm_config_gpt_4()

        timestamp_copy = (
            datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            if timestamp is None
            else timestamp
        )
        web_surfer_navigator_system_message = (
            _create_web_surfer_navigator_system_message(
                task_guidelines=_task_guidelines
            )
        )
        # validate url, error will be raised if url is invalid
        # Append https if protocol is missing
        url = str(WebUrl(url=url).url)
        status_code = get_webpage_status_code(url)
        if status_code is None:
            return "FAILED: The URL is invalid. Please provide a valid URL."
        elif status_code < 200 or status_code >= 400:
            return f"FAILED: The URL returned status code {status_code}. Please provide a valid URL."

        last_message: str = ""
        failure_message: str = ""
        min_relevant_pages_msg = f"The summary must include AT LEAST {min_relevant_pages} or more relevant pages."
        for _ in range(outer_retries):
            last_message = ""
            failure_message = ""
            try:
                web_surfer = WebSurferAgent(
                    "web_surfer",
                    llm_config=websurfer_llm_config,
                    summarizer_llm_config=summarizer_llm_config,
                    browser_config={"viewport_size": 4096, "bing_api_key": None},
                    is_termination_msg=_is_termination_msg,
                    human_input_mode="NEVER",
                )

                web_surfer_navigator = autogen.AssistantAgent(
                    "web_surfer_navigator",
                    llm_config=websurfer_navigator_llm_config,
                    system_message=web_surfer_navigator_system_message,
                    # is_termination_msg=_is_termination_msg,
                )

                initial_message = (
                    f"Time now is {timestamp_copy}." if timestamp_copy else ""
                )
                initial_message += f"""
URL: {url}
TASK: {_task}
The JSON-encoded string must contain at least {min_relevant_pages} relevant pages!
"""

                web_surfer_navigator.initiate_chat(web_surfer, message=initial_message)

                for i in range(inner_retries):
                    print(f"Inner retry {i + 1}/{inner_retries}")
                    last_message = str(web_surfer_navigator.last_message()["content"])

                    try:
                        if "I GIVE UP" in last_message:
                            failure_message = ""
                            break
                        if (
                            "TERMINATE" in last_message
                            and "```json" not in last_message
                        ):
                            retry_message = _constuct_retry_message(
                                new_message=f"Before terminating, you must provide JSON-encoded string without any other text or formatting in a message. {min_relevant_pages_msg}",
                                give_up_message=give_up_message,
                                current_retries=i,
                                max_retires_before_give_up_message=max_retires_before_give_up_message,
                            )
                            web_surfer.send(
                                retry_message,
                                recipient=web_surfer_navigator,
                            )
                            continue
                        match = re.search(
                            r"```json\n(.*)\n```", last_message, re.DOTALL
                        )
                        if match:
                            last_message = match.group(1)

                        summary = Summary.model_validate_json(last_message)
                        if len(summary.relevant_pages) < min_relevant_pages:
                            retry_message = _constuct_retry_message(
                                new_message=f"FAILED: {min_relevant_pages_msg} You have provided only {len(summary.relevant_pages)} pages. Please try again.",
                                give_up_message=give_up_message,
                                current_retries=i,
                                max_retires_before_give_up_message=max_retires_before_give_up_message,
                            )
                            web_surfer.send(
                                retry_message,
                                recipient=web_surfer_navigator,
                            )
                            continue
                        last_message = _format_last_message(summary)
                        return last_message
                    except ValidationError as e:
                        retry_message = _constuct_retry_message(
                            new_message=f"""FAILED to decode provided JSON:
{str(e.errors())}

Please create a new JSON-encoded string according to the following schema:
{Summary.model_json_schema()}

Example of correctly formatted JSON (unrelated to the task):
```json
{example.model_dump_json()}
```
""",
                            give_up_message=give_up_message,
                            current_retries=i,
                            max_retires_before_give_up_message=max_retires_before_give_up_message,
                        )
                        web_surfer.send(
                            retry_message,
                            recipient=web_surfer_navigator,
                        )

                    except Exception as e:
                        retry_message = _constuct_retry_message(
                            new_message=f"FAILED: {str(e)}",
                            give_up_message=give_up_message,
                            current_retries=i,
                            max_retires_before_give_up_message=max_retires_before_give_up_message,
                        )
                        web_surfer.send(retry_message, recipient=web_surfer_navigator)
            except Exception as e:
                # todo: log the exception
                failure_message = str(e)
                print("Exception:")
                print(e)
            finally:
                if timestamp_copy:
                    # reset the timestamp (because of the autogen cache)
                    timestamp_copy = time.strftime("%Y-%m-%dT%H:%M:%S")

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
        "subject": "Capt’n.ai Weekly Analysis",
        "email_content": "<html></html>",
        "proposed_user_action": proposed_user_actions,
        "terminate_groupchat": True,
    }
    return return_msg
