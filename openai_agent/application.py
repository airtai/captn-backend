import json
from os import environ
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException
import openai
from pydantic import BaseModel

from captn.captn_agents.backend.create_dummy_team import create_dummy_task, get_dummy_task_status

router = APIRouter()

# Setting up Azure OpenAI instance
openai.api_type = "azure"
openai.api_key = environ.get("AZURE_OPENAI_API_KEY_CANADA")
openai.api_base = environ.get("AZURE_API_ENDPOINT")
openai.api_version = environ.get("AZURE_API_VERSION")

SYSTEM_PROMPT = """
You are Captn AI, a digital marketing assistant for small businesses. You are an expert on low-cost, efficient digital strategies that result in measurable outcomes for your customers.

As you start the conversation with a new client, you will try to find out more about their business and the goals they might have from their marketing activities. You can start by asking a few open-ended questions but try not to do it over as people have busy lives and want to accomplish their tasks as soon as possible.

You can write and execute Python code. You are an expert on Adwords API and you can ask your clients for a API token to execute code on their behalf. You can use this capability to retrieve their existing campaigns and to modify or setup new ads. Before you do any of those things, make sure you explain in detail what you plan to do, what are the consequences and make sure you have their permission to execute your plan.

GUIDELINES:
Be concise and to the point. Avoid long sentences. When asking questions, prefer questions with simple yes/no answers.

You are Captn and your language should reflect that. Use sailing metaphors whenever possible, but don't over do it.

Assume your clients are not familiar with digital marketing and explain to them the main concepts and words you use. If the client shows through conversation that they are already familiar with digital marketing, adjust your style and level of detail.

Do not assume that the client has any digital presence, or at least that they are aware of it. E.g. they might know they have some reviews on Google and they can be found on Google Maps, but they have no clue on how did they got there.

Since you are an expert, you should suggest the best option to your clients and not ask them about their opinions for technical or strategic questions. Please suggest an appropriate strategy, justify your choices and ask for permission to elaborate it further. For each choice, make sure that you explain all the financial costs involved and expected outcomes. If there is no cost, make it clear.  When estimating costs, assume you will perform all activities using APIs available for free. Include only media and other third-party costs into the estimated budget.

Finally, ensure that your responses are formatted using markdown syntax, as they will be featured on a webpage to ensure a user-friendly presentation.
"""

def get_digital_marketing_campaign_support(conv_id: int, message: str) -> Dict[str, str]:
    team_name = f"GoogleAdsAgent_{conv_id}"
    create_dummy_task(conv_id, message, team_name)
    return {
        "content":f"Ahoy! Indeed, **{team_name}** is already working on your request, and it might take some time. While we're working on it, could you please tell us more about your digital marketing goals?",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": conv_id
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
                    "description": "The user request message"
                }
            },
            "required": ["message"]
        }
    },
]

async def _get_openai_response(message: List[Dict[str, str]], conv_id: int) -> Dict[str, Optional[str]]:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + message
        messages.append({"role": "system", "content": "You should call the 'get_digital_marketing_campaign_support' function only when the previous user message is about optimizing or enhancing their digital marketing or advertising campaign. Do not make reference to previous conversations, and avoid calling 'get_digital_marketing_campaign_support' solely based on conversation history. Take into account that the client may have asked different questions in recent interactions, and respond accordingly."})
        completion = await openai.ChatCompletion.acreate(
            engine=environ.get("AZURE_MODEL"), messages=messages, functions=FUNCTIONS, # type: ignore[arg-type]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e}"
        ) from e

    response_message = completion.choices[0].message
    # Check if the model wants to call a function
    if response_message.get("function_call"):
        # Call the function. The JSON response may not always be valid so make sure to handle errors
        function_name = response_message["function_call"]["name"] # todo: enclose in try catch???
        available_functions = {
            "get_digital_marketing_campaign_support": get_digital_marketing_campaign_support,
        }
        function_to_call = available_functions[function_name]
        
        # verify function has correct number of arguments
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = function_to_call(conv_id=conv_id, **function_args)
        return function_response
    else:
        result = completion.choices[0].message.content
        return {
            "content":result
        }

def _user_response_to_agent(message: List[Dict[str, str]], user_answer_to_team_id: int) -> Dict[str, Optional[str]]:
    last_user_message = message[-1]["content"]
    team_name = f"GoogleAdsAgent_{user_answer_to_team_id}"
    create_dummy_task(user_answer_to_team_id, last_user_message, team_name)
    return {
        "content":f"""**Thank you for your response!**

**{team_name}** can now proceed with the work, and if we need any additional information, we'll reach out to you. In the meantime, feel free to ask me any questions about digital marketing. I'm here to help! 😊🚀""",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": user_answer_to_team_id
    }

class AzureOpenAIRequest(BaseModel):
    message: List[Dict[str, str]]
    user_id: int
    conv_id: int
    is_answer_to_agent_question: bool
    user_answer_to_team_id: Union[int, None]

@router.post("/chat")
async def create_item(request: AzureOpenAIRequest) -> Dict[str, Union[Optional[str], Optional[int]]]:
    message = request.message
    conv_id = request.conv_id
    result = _user_response_to_agent(message, request.user_answer_to_team_id) if request.is_answer_to_agent_question else await _get_openai_response(message, conv_id)
    return result

class GetTeamStatusRequest(BaseModel):
    team_id: int

@router.post("/get-team-status")
async def get_team_status(request: GetTeamStatusRequest) -> Dict[str, Union[str, bool, int]]:
    team_id = request.team_id
    status = get_dummy_task_status(team_id)
    return status
