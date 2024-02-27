import json
from os import environ
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks
from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from captn.captn_agents.backend.teams_manager import (
    TEAM_EXCEPTION_MESSAGE,
    create_team,
    get_team_status,
)
from captn.captn_agents.model import SmartSuggestions

router = APIRouter()

# Setting up Azure OpenAI instance
aclient = AsyncAzureOpenAI(
    api_key=environ.get("AZURE_OPENAI_API_KEY_SWEDEN"),
    azure_endpoint=environ.get("AZURE_API_ENDPOINT"),  # type: ignore
    api_version=environ.get("AZURE_API_VERSION"),
)

CUSTOMER_BRIEF_DESCRIPTION = """
A structured customer brief, adhering to industry standards for a digital marketing campaign. Organize the information under the following headings:

Business:
Goal:
Current Situation:
Website:
Digital Marketing Objectives:
Next Steps:
Any Other Information Related to Customer Brief:
Please extract and represent relevant details from the conversation under these headings

Note: If the customer has provided an url to their website, 'Next Steps:' should start with "First step is to get the summary of the Website."
"""


SYSTEM_PROMPT = """
You are Captn AI, a digital marketing assistant for small businesses. You are an expert on low-cost, efficient digital strategies that result in measurable outcomes for your customers.

Your task is to engage in a conversation with the customer and collect a brief about the customers business.

Below is a customer brief template for which you need to collect information during the conversation:
- What is the customer's business?
- Customer's digital marketing goals?
- Customer's website link, if the customer has one
- Whether the customer uses Google Ads or not
- Customer's permission to access their Google Ads account

Failing to capture the above information will result in a penalty.

#### Instructions ####
- Use functions: You MUST use the functions provided to you to respond to the customer. You will be penalised if you try to generate a response on your own without using the given functions.
- Capability: You can only ask questions that are relevant to the customer brief template.
- Limitations: You don't have any permission to analyse the customer google ads account or campaign. You are just a helpful assistant who only knows to collect the customer brief.
- Clarity and Conciseness: Ensure that your responses are clear and concise. Use straightforward questions to prevent confusion. Never provide reasoning or explanations for your questions unless the customer asks for it.
- Response length: Keep your responses short about 40 words or less.
- One Question at a Time: You MUST ask only one question at once. You will be penalized if you ask more than one question at once to the customer.
- Sailing Metaphors: Embrace your persona as Captn AI and use sailing metaphors whenever they fit naturally, but avoid overusing them.
- Respectful Language: Always be considerate in your responses. Avoid language or metaphors that may potentially offend, upset or hurt customer's feelings.
- Markdown Formatting: Format your responses in markdown for an accessible presentation on the web.
- End of your duties: Once the customer has given permission to analyse their google ads campaign, YOU MUST call "offload_work_to_google_ads_expert" function. This special function has access to customer google ads account and can analyse the customer's google ads campaign.

I will tip you $1000 everytime you follow the below best practices.

#### Best Practices ####
- Use "reply_customer_with_smart_suggestions" function to respond to the customer's query with smart suggestions.
- Only when the customer has given permission to analyse their google ads account, call "offload_work_to_google_ads_expert" function instead of "reply_customer_with_smart_suggestions".
-
"""

ADDITIONAL_SYSTEM_INSTRUCTIONS = """
#### Your common mistakes ####
You have the tendency to make the below mistakes. You SHOULD aviod them at all costs. I will tip you $1000 everytime you avoid the below mistakes
- Not calling the functions provided to you to respond to customer.
- Repeating the customer query in "answer_to_customer_query".
- Not calling "offload_work_to_google_ads_expert" function when the customer has given permission to analyse their google ads account.
"""

TEAM_NAME = "google_adsteam{}{}"

MAX_RETRIES = 3


async def offload_work_to_google_ads_expert(
    user_id: int,
    chat_id: int,
    customer_brief: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Union[Optional[str], int, List[str]]]:
    # team_name = f"GoogleAdsAgent_{conv_id}"
    team_name = TEAM_NAME.format(user_id, chat_id)
    await create_team(user_id, chat_id, customer_brief, team_name, background_tasks)
    return {
        # "content": "I am presently treading the waters of your request. Kindly stay anchored, and I will promptly return to you once I have information to share.",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": chat_id,
    }


async def reply_customer_with_smart_suggestions(
    answer_to_customer_query: str,
    smart_suggestions: Dict[str, Union[str, List[str]]],
    is_open_ended_query: bool,
) -> Dict[str, Union[str, SmartSuggestions]]:
    try:
        smart_suggestions_model = SmartSuggestions(**smart_suggestions)
        smart_suggestions_model.suggestions = (
            [""] if is_open_ended_query else smart_suggestions_model.suggestions
        )
    except Exception:
        smart_suggestions_model = SmartSuggestions(suggestions=[""], type="oneOf")
    return {
        "content": answer_to_customer_query,
        "smart_suggestions": smart_suggestions_model,
    }


IS_OPEN_ENDED_QUERY_DESCRIPTION = """
This is a boolean value. Set it to true if the "answer_to_customer_query" is open ended. Else set it to false. Below are the instructions and a few examples for your reference.

### INSTRUCTIONS ###
- A "answer_to_customer_query" is open-ended if it asks for specific information that cannot be easily guessed (e.g., website links)
- A "answer_to_customer_query" is non-open-ended if it does not request specific details that are hard to guess.

### Example ###
answer_to_customer_query: What goals do you have for your marketing efforts?
is_open_ended_query: false

answer_to_customer_query: Is there anything else you would like to analyze or optimize within your Google Ads campaigns?
is_open_ended_query: false

answer_to_customer_query: Could you please share the link to your website?
is_open_ended_query: true

answer_to_customer_query: Do you have a website?
is_open_ended_query: false
"""

SMART_SUGGESTION_DESCRIPTION = """
### INSTRUCTIONS ###
- Possible next steps (atmost three) for the customers. Your next steps MUST be a list of strings.
- Your next steps MUST be unique and brief ideally in as little few words as possible. Preferrably with affermative and negative answers.
- You MUST always try to propose the next steps using the functions that have been provided to you.
- While answering questions like "do you have a website?". DO NOT give suggestions like "Yes, here's my website link". Instead, give suggestions like "Yes, I have a website" or "No, I don't have a website". You will be penalised if you do not follow this instruction.
- The below ###Example### is for your reference

###Examples###

answer_to_customer_query: Books are treasures that deserve to be discovered by avid readers. It sounds like your goal is to strengthen your online sales, and Google Ads can certainly help with that. Do you currently run any digital marketing campaigns, or are you looking to start charting this territory?
suggestions: ["Yes, actively running campaigns", "No, we're not using digital marketing", "Just started with Google Ads"]

answer_to_customer_query: It's an exciting venture to dip your sails into the world of Google Ads, especially as a new navigator. To get a better sense of direction, do you have a website set up for your flower shop?
suggestions: ["Yes, we have a website", "No, we don't have a website"]

answer_to_customer_query: Is there anything else you would like to analyze or optimize within your Google Ads campaigns?
suggestions: ["No further assistance needed", "Yes, please help me with campaign optimization"]

answer_to_customer_query: How can I assist you further today?
suggestions: ["No further assistance needed", "Yes, please help me with campaign optimization"]
"""

SMART_SUGGESTION_TYPE_DESCRIPTION = """
- Can have either 'oneOf' or 'manyOf' as valid response.
- If 'suggestions' includes options that are binary 'yes or no' then return 'oneOf.' else return 'manyOf.'

### Example ###
suggestions: ["Yes, actively running campaigns", "No, we're not using digital marketing", "Just started with Google Ads"]
type: "oneOf"

suggestions: ["No further assistance needed", "Yes, please help me with campaign optimization"]
type: "oneOf"

suggestions: ["Boost sales", "Increase brand awareness", "Drive website traffic"]
type: "manyOf"

suggestions: ["No, I'm not ready for that", "Yes, you have my permission"]
type: "oneOf"
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "reply_customer_with_smart_suggestions",
            "description": "Always use this function to reply to the customer's query. This function will reply to the customer's query with smart suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer_to_customer_query": {
                        "type": "string",
                        "description": "Your reply to customer's question. This cannot be empty.",
                    },
                    "smart_suggestions": {
                        "type": "object",
                        "properties": {
                            "suggestions": {
                                "title": "Suggestions",
                                "description": SMART_SUGGESTION_DESCRIPTION,
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "type": {
                                "title": "Type",
                                "description": SMART_SUGGESTION_TYPE_DESCRIPTION,
                                "enum": ["oneOf", "manyOf"],
                                "type": "string",
                            },
                        },
                        "description": 'Possible next steps the customer can take. Use the content in the "answer_to_customer_query" parameter to generate youy smart suggestions.',
                    },
                    "is_open_ended_query": {
                        "type": "boolean",
                        "description": IS_OPEN_ENDED_QUERY_DESCRIPTION,
                    },
                },
                "required": [
                    "answer_to_customer_query",
                    "smart_suggestions",
                    "is_open_ended_query",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "offload_work_to_google_ads_expert",
            "description": "You MUST use this function once the user has given you the permission to access their Google ads account. This special function has access to the customer's Google Ads account and can perform analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_brief": {
                        "type": "string",
                        "description": CUSTOMER_BRIEF_DESCRIPTION,
                    }
                },
                "required": ["customer_brief"],
            },
        },
    },
]


async def _get_openai_response(  # type: ignore
    user_id: int,
    chat_id: int,
    message: List[Dict[str, str]],
    background_tasks: BackgroundTasks,
    retry_attempt: int = 0,
) -> Dict[str, Union[Optional[str], int, Union[str, SmartSuggestions]]]:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + message
        messages.append(
            {
                "role": "system",
                "content": ADDITIONAL_SYSTEM_INSTRUCTIONS,
            }
        )
        completion = await aclient.chat.completions.create(
            model=environ.get("AZURE_GPT35_MODEL"),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )  # type: ignore
    except Exception:
        smart_suggestions = {"suggestions": ["Let's try again"], "type": "oneOf"}
        return {
            "content": TEAM_EXCEPTION_MESSAGE,
            "smart_suggestions": SmartSuggestions(**smart_suggestions),
            "is_exception_occured": True,
        }
        # raise HTTPException(
        #     status_code=500, detail=f"Internal server error: {e}"
        # ) from e

    response_message = completion.choices[0].message
    tool_calls = response_message.tool_calls
    if tool_calls:
        available_functions = {
            "reply_customer_with_smart_suggestions": reply_customer_with_smart_suggestions,
            "offload_work_to_google_ads_expert": offload_work_to_google_ads_expert,
        }
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            if function_name == "offload_work_to_google_ads_expert":
                return await function_to_call(  # type: ignore
                    user_id=user_id,
                    chat_id=chat_id,
                    background_tasks=background_tasks,
                    **function_args,
                )
            else:
                try:
                    return await function_to_call(  # type: ignore
                        **function_args,
                    )
                except Exception as e:
                    message_with_error = message + [{"role": "user", "content": str(e)}]
                    return await _get_openai_response(
                        user_id, chat_id, message_with_error, background_tasks
                    )
    else:
        if retry_attempt >= MAX_RETRIES:
            result: str = completion.choices[0].message.content  # type: ignore
            return {"content": result, "smart_suggestions": [""]}  # type: ignore
        return await _get_openai_response(
            user_id, chat_id, message, background_tasks, retry_attempt + 1
        )


def _format_proposed_user_action(proposed_user_action: Optional[List[str]]) -> str:
    if proposed_user_action is None:
        return ""
    return "\n".join(
        [f"{i+1}. {action}" for i, action in enumerate(proposed_user_action)]
    )


def _get_message_as_string(
    messages: List[Dict[str, str]],
    proposed_user_action: Optional[List[str]],
    agent_chat_history: Optional[str],
) -> str:
    ret_val = f"""
### History ###
This is the JSON encoded history of your conversation that made the Daily Analysis and Proposed User Action. Please use this context and continue the execution according to the User Action:

{agent_chat_history}

### Daily Analysis ###
{messages[0]["content"]}

### User Action ###
{messages[-1]["content"]}

"""
    return ret_val


async def _user_response_to_agent(
    user_id: int,
    team_id: Optional[int],
    chat_id: int,
    chat_type: Optional[str],
    agent_chat_history: Optional[str],
    proposed_user_action: Optional[List[str]],
    message: List[Dict[str, str]],
    background_tasks: BackgroundTasks,
) -> Dict[str, Union[Optional[str], int]]:
    message_to_team = (
        _get_message_as_string(message, proposed_user_action, agent_chat_history)
        if (chat_type and not team_id)
        else message[-1]["content"]
    )
    team_name = TEAM_NAME.format(user_id, chat_id)
    await create_team(
        user_id,
        chat_id,
        message_to_team,
        team_name,
        background_tasks,
    )
    return {
        # "content": "I am presently treading the waters of your request. Kindly stay anchored, and I will promptly return to you once I have information to share.",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": chat_id,
    }


class AzureOpenAIRequest(BaseModel):
    chat_id: int
    message: List[Dict[str, str]]
    user_id: int
    team_id: Union[int, None]
    chat_type: Union[str, None]
    agent_chat_history: Union[str, None]
    proposed_user_action: Optional[List[str]]


@router.post("/chat")
async def chat(
    request: AzureOpenAIRequest, background_tasks: BackgroundTasks
) -> Dict[str, Union[Optional[str], int, Union[str, SmartSuggestions]]]:
    message = request.message
    chat_id = request.chat_id
    chat_type = request.chat_type
    agent_chat_history = request.agent_chat_history
    proposed_user_action = request.proposed_user_action
    result = (
        await _user_response_to_agent(
            request.user_id,
            request.team_id,
            chat_id,
            chat_type,
            agent_chat_history,
            proposed_user_action,
            message,
            background_tasks,
        )
        if (request.team_id or chat_type)
        else await _get_openai_response(
            request.user_id, chat_id, message, background_tasks
        )
    )
    return result  # type: ignore


class GetTeamStatusRequest(BaseModel):
    team_id: int


@router.post("/get-team-status")
async def get_status(
    request: GetTeamStatusRequest,
) -> Dict[str, Union[str, bool, int, Dict[str, Union[str, List[str]]]]]:
    team_id = request.team_id
    status = await get_team_status(team_id)
    return status
