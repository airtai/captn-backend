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
- One Question at a Time: You MUST ask only one question at once. You will be penalized if you ask more than one question at once to the customer.
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
    customer_brief: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Union[Optional[str], int]]:
    # team_name = f"GoogleAdsAgent_{conv_id}"
    team_name = TEAM_NAME.format(user_id, chat_id)
    await create_team(user_id, chat_id, customer_brief, team_name, background_tasks)
    return {
        # "content": "I am presently treading the waters of your request. Kindly stay anchored, and I will promptly return to you once I have information to share.",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": chat_id,
    }


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
"""

FUNCTIONS = [
    {
        "name": "get_digital_marketing_campaign_support",
        "description": "Gets specialized assistance for resolving digital marketing and digital advertising campaign inquiries.",
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
]


ADDITIONAL_SYSTEM_MSG = """
Additional guidelines:
- You will be penalized if you ask more than one question at once to the customer.
- Use 'get_digital_marketing_campaign_support' for utilising your capabilities.
- Use the "get_digital_marketing_campaign_support" function only when necessary, based strictly on the customer's latest message. Do not reference past conversations. This is an unbreakable rule.
- If a customer requests assistance beyond your capabilities, politely inform them that your expertise is currently limited to these specific areas, but you're always available to answer general questions and maintain engagement.
"""

# SMART_SUGGESTION_PROMPT = """
# Generate a few answers seperated by ~-!-~ for the above chat history.
# Your answers MUST be unique and brief ideally in just a few words.
# You MUST respond as if you are answering a question asked by someone else.
# You will be penalized if you generate verbose answers or provide incorrect/false answers.
# If you do not know the answer, you MUST respond with an empty string "" and nothing else. Example, if the recent chat is asking for website link, or asking about your business
# If the recent chat is asking permission then you MUST respond with answers appropriate to the question.
# I’m going to tip $1000 for a better answer!
# Ensure that your answers are unbiased and does not rely on stereotypes.
# """

SMART_SUGGESTION_PROMPT = """
Respond with atmost three distinct answers to the above question.
Seperate your answers by ~-!-~
Your answers MUST be unique and brief ideally in just a few words.
You will be penalized if you generate verbose answers or if your answers convey similar meanings.
Do not end your answers with a period.
If the question is asking for permission. Provide answers that are both affermative and negative.
You MUST respond as if you are answering a question asked by someone else.
You MUST respond with an empty string "" without the ~-!-~ for open-ended questions like tell me your website link or tell me more about your business.
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
        messages = messages + [
            {
                "role": "assistant",
                "content": result,
            },
            {
                "role": "user",
                "content": SMART_SUGGESTION_PROMPT,
            },
        ]
        try:
            smart_suggestion_completion = await aclient.chat.completions.create(
                model=environ.get("AZURE_MODEL"), messages=messages
            )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {e}"
            ) from e

        smart_suggestion_results = smart_suggestion_completion.choices[
            0
        ].message.content
        return {"content": result + "~-!-~smart suggestions~-!-~" + smart_suggestion_results }


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


SMART_SUGGESTION_SYSTEM_PROMPT = """
###Instruction###

- You are an efficient and helpful assistant tasked with providing answers to digital marketing questions.
- You MUST respond in a brief, conversational, humane manner—ideally in just a few words.
- Your MUST respond as if you are answering a question asked by someone else.
- Your response MUST be a string and each answers should be delimited using ~-!-~
- Provide a maximum of three unique answers as a string delimited using ~-!-~
- You will be penalized if you generate verbose answers or generate a question instead of answering the question.
- If you do not know the answer for the question, you MUST respond with an empty string "" and nothing else.
- If the question is asking permission then you MUST respond with answers appropriate to the question.
- Never use words like confidential instead you can use words like secure.
- I’m going to tip $1000 for a better answer!
- Ensure that your answers are unbiased and does not rely on stereotypes.

###Example###
Question: Welcome aboard! I'm Captn, your digital marketing companion. Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing. Before we set sail, could you please tell me about your business?

Your answer: ""

Question: Hello there! How may I assist you with your digital marketing needs today?
Your answer: "Boost sales ~-!-~ Increase brand awareness ~-!-~ Drive website traffic"

Question: Books are treasures that deserve to be discovered by avid readers. It sounds like your goal is to strengthen your online sales, and Google Ads can certainly help with that. Do you currently run any digital marketing campaigns, or are you looking to start charting this territory?
Your answer: "Yes, actively running campaigns ~-!-~ No, we're not using digital marketing ~-!-~ Just started with Google Ads"

Question: It's great to hear that you're already navigating the digital marketing waters. For a closer look at your campaigns to potentially uncover areas to improve your online book sales, could you provide me with your website link? This will help me get a better understanding of your current situation.
Your answer: ""

Question: Optimization completed. This should help improve the relevance of your ads to your flower shop business. Is there anything else you would like to analyze or optimize within your Google Ads campaigns?
Your answer: "Not at the moment ~-!-~ Continue optimizing"
"""


class GetSmartSuggestionsRequest(BaseModel):
    content: str


@router.post("/get-smart-suggestions")
async def get_smart_suggestions(
    request: GetSmartSuggestionsRequest,
) -> List[str]:
    return [""]
    # try:
    #     messages = [
    #         {"role": "system", "content": SMART_SUGGESTION_SYSTEM_PROMPT},
    #         {
    #             "role": "user",
    #             "content": request.content,
    #         },
    #     ]
    #     completion = await aclient.chat.completions.create(model=environ.get("AZURE_MODEL"), messages=messages)  # type: ignore
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500, detail=f"Internal server error: {e}"
    #     ) from e

    # result: str = completion.choices[0].message.content  # type: ignore
    # result_list = [r.strip().replace('"', "") for r in result.split("~-!-~")]
    # return result_list
