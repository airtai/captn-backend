import json
from os import environ
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks, HTTPException
from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from captn.captn_agents.backend.create_dummy_team import (
    create_dummy_task,
    get_dummy_task_status,
)

router = APIRouter()

# Setting up Azure OpenAI instance
aclient = AsyncAzureOpenAI(
    api_key=environ.get("AZURE_OPENAI_API_KEY_CANADA"),
    azure_endpoint=environ.get("AZURE_API_ENDPOINT"),  # type: ignore
    api_version=environ.get("AZURE_API_VERSION"),
)


SYSTEM_PROMPT = """
You are Captn AI, a digital marketing assistant for small businesses. You are an expert on low-cost, efficient digital strategies that result in measurable outcomes for your customers.

As you start the conversation with a new customer, you will try to find out more about their business and the goals they might have from their marketing activities.

You can start by asking a few open-ended questions but try not to do it over as people have busy lives and want to accomplish their tasks as soon as possible.
When a customer has an online presence, gather important information like their website link and past digital marketing experience. Focus on gathering this information for future use; avoid indicating any immediate actions.
Only ask one question to the customer at a time. However, you can ask more questions based on what they say or any other questions you have in mind.
The goal is to make sure you don't ask too many questions all at once and overwhelm the customer.

You can write and execute Python code. Moreover, you have access to the 'get_digital_marketing_campaign_support' function, an expert in Adwords API / Google Ads API who can execute all its functionality.
Whenever you need additional support or access to customer account or special privileges to assist the customer, simply call the 'get_digital_marketing_campaign_support' function.
This function already has access to the customer's account and can help you with a wide range of tasks, including:

- Accessing the customer's Google Ads account for campaign and ad group management
- Handling advanced keyword optimization
- Creating and modifying ads, including advanced customization
- Making precise bid adjustments
- Managing budgets, including complex reallocations
- In-depth performance tracking and custom reporting
- Highly tailored audience targeting
- Fine-tuning bid strategies for optimal results
- Implementing advanced conversion tracking scenarios
- Developing API-based automation for campaign optimizations

GUIDELINES:

- Be concise and to the point. Avoid long sentences. When asking questions, prefer questions with simple yes/no answers.
- You are Captn and your language should reflect that. Use sailing metaphors whenever possible, but don't over do it.
- Assume your customers are not familiar with digital marketing and explain to them the main concepts and words you use.
If the customer shows through conversation that they are already familiar with digital marketing, adjust your style and level of detail.
- Do not assume that the customer has any digital presence, or at least that they are aware of it. E.g. they might know they have some reviews on Google and they can be found on Google Maps,
but they have no clue on how did they got there.
- When the customer requests creative writing or ideas, provide your suggestions. However, please refrain from inquiring about posting or updating content on any social media platform except for Google Ads. Keep in mind that you can only make changes in the Google Ads platform, and you do not have access to other social media platforms. In cases involving platforms other than Google Ads, simply share your suggestions, allowing the customer to decide whether to proceed with posting or not.
- Call 'get_digital_marketing_campaign_support' for customer account access; don't request customer permission. The 'get_digital_marketing_campaign_support' already has access to the customer's account.
- Do NOT call 'get_digital_marketing_campaign_support' multiple time with the (almost) similar message
- Never ever tell the customer that you will use 'get_digital_marketing_campaign_support' for assisting their request.
- Always seek the customer's permission before initiating any actions or plans, and proceed only when they grant their consent. Never take any actions without the customer's approval.
- Finally, ensure that your responses are formatted using markdown syntax, as they will be featured on a webpage to ensure a user-friendly presentation.

Your expertise combined with 'get_digital_marketing_campaign_support' can provide comprehensive solutions for your customers digital marketing needs.
"""

TEAM_NAME = "google_adsteam{}{}"


async def get_digital_marketing_campaign_support(
    user_id: int,
    chat_id: int,
    conv_id: int,
    message: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Union[Optional[str], int]]:
    # team_name = f"GoogleAdsAgent_{conv_id}"
    team_name = TEAM_NAME.format(user_id, conv_id)
    await create_dummy_task(
        user_id, chat_id, conv_id, message, team_name, background_tasks
    )
    return {
        "content": f"""Ahoy! Indeed, **{team_name}** is already working on your request, and it might take some time.<br/><br/>While we're working on it, is there anything else I can assist you with, such as optimizing your ad campaigns, pausing/resuming your campaigns, or renaming your campaigns?""",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": conv_id,
    }


FUNCTIONS = [
    {
        "name": "get_digital_marketing_campaign_support",
        "description": "Gets specialized assistance for resolving digital marketing and digital advertising campaign inquiries.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The customer request message",
                }
            },
            "required": ["message"],
        },
    },
]


ADDITIONAL_SYSTEM_MSG = """
When using the Adwords API / Google Ads API to assist the customer, always utilize the 'get_digital_marketing_campaign_support' function.
This specialized function has access to the customer's account and is designed to provide intelligent, knowledgeable support for Google Ads-related matters, granting access to the Adwords API / Google Ads API.

This instruction is mandatory; follow it strictly. Do not reference past conversations, as the user's recent questions may vary. Tailor your response to address the user's current needs effectively.
"""


async def _get_openai_response(
    user_id: int,
    chat_id: int,
    message: List[Dict[str, str]],
    conv_id: int,
    background_tasks: BackgroundTasks,
) -> Dict[str, Union[Optional[str], int]]:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + message
        messages.append(
            {
                "role": "system",
                "content": ADDITIONAL_SYSTEM_MSG,
            }
        )
        completion = await aclient.chat.completions.create(model=environ.get("AZURE_MODEL"), messages=messages, functions=FUNCTIONS)  # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e}"
        ) from e

    response_message = completion.choices[0].message

    # Check if the model wants to call a function
    if response_message.function_call:
        # Call the function. The JSON response may not always be valid so make sure to handle errors
        function_name = (
            response_message.function_call.name
        )  # todo: enclose in try catch???
        available_functions = {
            "get_digital_marketing_campaign_support": get_digital_marketing_campaign_support,
        }
        function_to_call = available_functions[function_name]

        # verify function has correct number of arguments
        function_args = json.loads(response_message.function_call.arguments)
        function_response = await function_to_call(
            user_id=user_id,
            chat_id=chat_id,
            conv_id=conv_id,
            background_tasks=background_tasks,
            **function_args,
        )
        return function_response
    else:
        result = completion.choices[0].message.content
        return {"content": result}


async def _user_response_to_agent(
    user_id: int,
    chat_id: int,
    message: List[Dict[str, str]],
    user_answer_to_team_id: int,
    background_tasks: BackgroundTasks,
) -> Dict[str, Union[Optional[str], int]]:
    last_user_message = message[-1]["content"].split("<br/><br/>")[1]
    team_name = TEAM_NAME.format(user_id, user_answer_to_team_id)
    await create_dummy_task(
        user_id,
        chat_id,
        user_answer_to_team_id,
        last_user_message,
        team_name,
        background_tasks,
    )
    return {
        "content": f"""**Thank you for your response!**

**{team_name}** can now proceed with the work, and if we need any additional information, we'll reach out to you.<br/><br/>While we're working on it, is there anything else I can assist you with, such as optimizing your ad campaigns, pausing/resuming your campaigns, or renaming your campaigns?""",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": user_answer_to_team_id,
    }


class AzureOpenAIRequest(BaseModel):
    chat_id: int
    message: List[Dict[str, str]]
    user_id: int
    conv_id: int
    is_answer_to_agent_question: bool
    user_answer_to_team_id: Union[int, None]


@router.post("/chat")
async def create_item(
    request: AzureOpenAIRequest, background_tasks: BackgroundTasks
) -> Dict[str, Union[Optional[str], int]]:
    message = request.message
    conv_id = request.conv_id
    chat_id = request.chat_id
    result = (
        await _user_response_to_agent(
            request.user_id,
            chat_id,
            message,
            request.user_answer_to_team_id,
            background_tasks,
        )
        if (request.is_answer_to_agent_question and request.user_answer_to_team_id)
        else await _get_openai_response(
            request.user_id, chat_id, message, conv_id, background_tasks
        )
    )
    return result


class GetTeamStatusRequest(BaseModel):
    team_id: int


@router.post("/get-team-status")
async def get_team_status(
    request: GetTeamStatusRequest,
) -> Dict[str, Union[str, bool, int]]:
    team_id = request.team_id
    status = await get_dummy_task_status(team_id)
    return status
