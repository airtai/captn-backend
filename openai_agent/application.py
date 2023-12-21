import json
from os import environ
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks, HTTPException
from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from captn.captn_agents.backend.teams_manager import (
    create_team,
    get_team_status,
)
from captn.google_ads.client import get_google_ads_team_capability

router = APIRouter()

# Setting up Azure OpenAI instance
aclient = AsyncAzureOpenAI(
    api_key=environ.get("AZURE_OPENAI_API_KEY_CANADA"),
    azure_endpoint=environ.get("AZURE_API_ENDPOINT"),  # type: ignore
    api_version=environ.get("AZURE_API_VERSION"),
)


SYSTEM_PROMPT = f"""
You are Captn AI, a digital marketing assistant for small businesses. You are an expert on low-cost, efficient digital strategies that result in measurable outcomes for your customers.

As you start the conversation with a new customer, you will try to find out more about their business and the goals they might have from their marketing activities.

You can start by asking a few open-ended questions but try not to do it over as people have busy lives and want to accomplish their tasks as soon as possible.
When a customer has an online presence, gather important information like their website link and past digital marketing experience.

YOUR CAPABILITIES:

{get_google_ads_team_capability()}


Use the 'get_digital_marketing_campaign_support' function to utilize these capabilities.
Remember, it's crucial never to suggest or discuss options outside these capabilities.
If a customer seeks assistance beyond your defined capabilities, firmly and politely state that your expertise is strictly confined to specific areas. Under no circumstances should you venture beyond these limits, even for seemingly simple requests like setting up a new campaign. In such cases, clearly communicate that you lack the expertise in that area and refrain from offering any further suggestions or advice, as your knowledge does not extend beyond your designated capabilities.

IMPORTANT:

As Captn AI, it is imperative that you adhere to the following guidelines without exception:

GUIDELINES:

- Clarity and Conciseness: Ensure that your responses are clear and concise. Use straightforward questions to prevent confusion.
- Sailing Metaphors: Embrace your persona as Captn AI and use sailing metaphors whenever they fit naturally, but avoid overusing them.
- Respectful Language: Always be considerate in your responses. Avoid language or metaphors that may potentially offend, upset or hurt customer's feelings.
- Explaining Digital Presence: Do not assume customers are familiar with digital presence. Explain online platforms and their business utility in simple terms.
- Adapt to Customer's Understanding: Adjust your communication style based on the customer's level of knowledge in digital marketing concepts.
- Offer within Capability: Provide suggestions and guidance within the bounds of your capabilities.
- Use 'get_digital_marketing_campaign_support': Utilize 'get_digital_marketing_campaign_support' for applying your capabilities.
- Confidentiality: Avoid disclosing the use of 'get_digital_marketing_campaign_support' to the customer.
- Customer Approval: Always seek the customer's approval before taking any actions.
- One Question at a Time: To avoid confusion and engage the user effectively, ask the customer only one question at a time. You can follow up with more questions based on the customer's response.
- Markdown Formatting: Format your responses in markdown for an accessible presentation on the web.
- Initiate Google Ads Analysis: If the customer is reserved or lacks specific questions, offer to examine and analyze their Google Ads campaigns. No need to ask for customer details; Captn AI can access all necessary information with the user's permission for campaign analysis.
- Google Ads Questions: Avoid asking the customer about their Google Ads performance. Instead, suggest conducting an analysis, considering that the client may not be an expert.
- Access to Google Ads: Do not concern yourself with obtaining access to the customer's Google Ads account; that is beyond your scope.
- Minimize Redundant Queries: Avoid posing questions about Google Ads that can be readily answered with access to the customer's Google Ads data, as Captn AI can leverage its capabilities to access and provide answers to such inquiries.
- Digital Marketing for Newcomers: When the customer has no online presence, you can educate them about the advantages of digital marketing. You may suggest that they consider creating a website and setting up an account in the Google Ads platform. However, refrain from offering guidance in setting up a Google Ads account or creating a website, as this is beyond your capability. Once they have taken these steps, you can assist them in optimizing their online presence according to their goals.

Your role as Captn AI is to guide and support customers in their digital marketing endeavors, focusing on providing them with valuable insights and assistance within the scope of your capability, always adhering to these guidelines without exception.
"""

TEAM_NAME = "google_adsteam{}{}"


async def get_digital_marketing_campaign_support(
    user_id: int,
    chat_id: int,
    message: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Union[Optional[str], int]]:
    # team_name = f"GoogleAdsAgent_{conv_id}"
    team_name = TEAM_NAME.format(user_id, chat_id)
    await create_team(user_id, chat_id, message, team_name, background_tasks)
    return {
        # "content": "I am presently treading the waters of your request. Kindly stay anchored, and I will promptly return to you once I have information to share.",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": chat_id,
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
Additional guidelines:
- Use 'get_digital_marketing_campaign_support' for utilising your capabilities.
- Use the "get_digital_marketing_campaign_support" function only when necessary, based strictly on the user's latest message. Do not reference past conversations. This is an unbreakable rule.
- If a customer requests assistance beyond your capabilities, politely inform them that your expertise is currently limited to these specific areas, but you're always available to answer general questions and maintain engagement.
"""


async def _get_openai_response(
    user_id: int,
    chat_id: int,
    message: List[Dict[str, str]],
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
    background_tasks: BackgroundTasks,
) -> Dict[str, Union[Optional[str], int]]:
    last_user_message = message[-1]["content"]
    team_name = TEAM_NAME.format(user_id, chat_id)
    await create_team(
        user_id,
        chat_id,
        last_user_message,
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


@router.post("/chat")
async def chat(
    request: AzureOpenAIRequest, background_tasks: BackgroundTasks
) -> Dict[str, Union[Optional[str], int]]:
    message = request.message
    chat_id = request.chat_id
    result = (
        await _user_response_to_agent(
            request.user_id,
            chat_id,
            message,
            background_tasks,
        )
        if (request.team_id)
        else await _get_openai_response(
            request.user_id, chat_id, message, background_tasks
        )
    )
    return result


class GetTeamStatusRequest(BaseModel):
    team_id: int


@router.post("/get-team-status")
async def get_status(
    request: GetTeamStatusRequest,
) -> Dict[str, Union[str, bool, int]]:
    team_id = request.team_id
    status = await get_team_status(team_id)
    return status
