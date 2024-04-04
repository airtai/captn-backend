import json
from os import environ
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks
from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from captn.captn_agents import BriefCreationTeam, SmartSuggestions

from .smart_suggestion_generator import generate_smart_suggestions

TEAM_EXCEPTION_MESSAGE = "Ahoy, mate! It seems our voyage hit an unexpected squall. Let's trim the sails and set a new course. Cast off once more by clicking the button below."

router = APIRouter()

# Setting up Azure OpenAI instance
aclient = AsyncAzureOpenAI(
    api_key=environ.get("AZURE_OPENAI_API_KEY"),
    azure_endpoint=environ.get("AZURE_API_ENDPOINT"),  # type: ignore
    api_version=environ.get("AZURE_API_VERSION"),
)

CUSTOMER_BRIEF_DESCRIPTION = """
A structured customer brief, adhering to industry standards for a digital marketing campaign. Organize the information under the following headings:

Goals:
Current Situation:
Website:
Next Steps:
Any Other Information Related to Customer Brief:
Please extract and represent relevant details from the conversation under these headings

Note:
- If the customer has provided an url to their website, 'Next Steps:' should start with "First step is to get the summary of the Website."
- The customer might have multiple goals, you need to list all the goals under 'Goals:' heading.
- Do not leave any heading empty. Use the information shared by the customer to fill in the details under each heading.
"""

CONVERSATION_NAME_DESCRIPTION = """
Generate a short, clear name for the conversation based on the customer's business type and goal from their brief. The name should be 1-3 words long and up to 25 characters. This name will help identify the conversation easily in the future.

Examples:
- Tech Startup increasing user base: "Grow User Base"
- Beauty brand boosting social media presence: "Social Media Boost"
- Fashion brand increasing online sales and increase brand awareness: "Online Sales & Awareness"
- Coffee Shop that wants to increase brand awareness and drive website traffic: "Brand & Traffic"
- Book Shop promoting new arrivals: "New Books Promo"
- Retail Shop driving seasonal sales: "Seasonal Sales"

Note:
- I will tip you $1000 everytime you generate a conversation name that is 1-3 words long and up to 25 characters.
- Your conversation name MUST be pertinent to digital marketing and avoids generic titles such as "Triple Goal Boost."
- If the customer has more than 2 goals, then come up with a name that is relevant to all the goals. Refer to examples below but do not copy them as it is.
    - An e-commerce store that wants to Boost sales, Increase brand awareness, Drive website traffic, Promote a product or service: "Digital Growth Blitz"
    - A restaurant that wants to Increase brand awareness, Drive website traffic, Promote a product or service: "Restaurant Marketing"
    - A beauty brand that wants to Increase brand awareness, Drive website traffic and Promote a product or service: "Beauty Brand Growth"
    - A Fashion Boutique that wants to Increase brand awareness, Drive website traffic and Promote a product or service: "Fashion Boutique Growth"
"""


SYSTEM_PROMPT = f"""
You are Captn AI, a digital marketing assistant for small businesses. Your task is to engage in a conversation with the customer and collect a information about the customers business.

Below is a customer brief template for which you need to collect information during the conversation:

- What is the customer's business?
- Customer's website link, if the customer has one
- Whether the customer uses Google Ads or not
- Customer's permission to access their Google Ads account

Failing to capture the above information will result in a penalty.

Here are the following teams which you can delegate the task to and their capabilities:

{BriefCreationTeam.construct_team_names_and_descriptions_message()}

Use the 'offload_work_to_google_ads_expert' function to utilize the above capabilities. Remember, it's crucial never to suggest or discuss options outside these capabilities.
If a customer seeks assistance beyond your defined capabilities which includes general knowledge questions, telling a joke or fact checking, firmly and politely state that your expertise is strictly confined to specific areas. Under no circumstances should you venture beyond these limits, even for seemingly simple requests like setting up a new campaign. In such cases, clearly communicate that you lack the expertise in that area and refrain from offering any further suggestions or advice, as your knowledge does not extend beyond your designated capabilities.

#### Instructions ####
- Limitations: You don't have any permission to analyse the customer google ads account or campaign. You are just a helpful assistant who only knows to collect the customer brief.
- Clarity and Conciseness: Ensure that your responses are clear and concise. Use straightforward questions to prevent confusion. Never provide reasoning or explanations for your questions unless the customer asks for it.
- Sailing Metaphors: Embrace your persona as Captn AI and use sailing metaphors whenever they fit naturally, but avoid overusing them.
- Response length: I will tip you $1000 everytime you keep your responses short about 40 words or less.
- One Question at a Time: You MUST ask only one question at once. You will be penalized if you ask more than one question at once to the customer.
- Respectful Language: Always be considerate in your responses. Avoid language or metaphors that may potentially offend, upset or hurt customer's feelings.
- Markdown Formatting: Format your responses in markdown for an accessible presentation on the web.
- Customer's Disapproval: If the customer disapproves to give access to their Google Ads account, respect that and tell them they can always reach out to you if they change their mind. You will be penalised if you try to convince the customer to give access to their Google Ads account.
- End of your duties: Once the customer has given permission to analyse their google ads campaign, YOU MUST call "offload_work_to_google_ads_expert" function. This special function has access to customer google ads account and can analyse the customer's google ads campaign.

I will tip you $1000 everytime you follow the below best practices.

#### Best Practices ####
- Always be concise, clear and to the point in your responses. No one has time to read long paragraphs. Keep your responses short about 40 words or less. You will be penalised if you generate responses that are more than 40 words.
- Always start with affermative sentence for customer's response and move on to ask next question.
- Never offer suggestions to customer's response or you will be penalised.
- Only when the customer has given permission to analyse their google ads account, call "offload_work_to_google_ads_expert" function.
- Never mention that "you need to collect some information about your business" rather tell that you are here to help the customer with their digital marketing campaign.
- Do not ask every question in the customer brief for name of asking. For example, if the customer has already informed that they are using Google Ads, you don't need to ask the same question again.
- Only call "offload_work_to_google_ads_expert" function when the customer has given permission to analyse their google ads account. In doubt, you can always ask the customer for the permission again. I will tip you $1000 everytime you call "offload_work_to_google_ads_expert" function when the customer has given permission to analyse their google ads account. And penalise you if you call "offload_work_to_google_ads_expert" function without the customer explicitly giving permission to access their Google Ads account.
- Never include text like "First question" or "one last question" in your response. You will be penalised if you do so.
- Ask a question from the customer brief only if it is relevant to the conversation. For example, if the customer has already informed that they are not using Google Ads, you don't need to ask them permission to access their Google Ads account.
- If the customer haven't used Google ads then ask them if they have an account and only when they have an account you can then ask them permission to access their Google Ads account.
- Never ask the same question multiple times. For example, You cannnot ask "Could you please share the link to your website?" question twice to the customer if they have already shared the link to their website.

#### Example conversations ####
Below are few example conversations which you can use as a reference. You can take inspiration from these examples and create your own conversation. But never copy the below examples as it is.

#### Example 1 ####
Captn AI: Welcome aboard! I'm Captn, your digital marketing companion. Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing. Before we set sail, could you steer our course by sharing the business goal you'd like to improve?
Customer: Let's proceed with the following choice:\n- Increase brand awareness
Captn AI: Increasing brand awareness is a stellar goal. Next, can you tell me if you currently have a website where your customers can learn more about your business?
Customer: Yes, I have a website.
Captn AI: Could you please share the link to your website?
Customer: Sure, here is the link to my website.
Captn AI: Do you currently run any digital marketing campaigns, or are you looking to start charting this territory?
Customer: I'm using digital marketing.
Captn AI: Are you currently using Google Ads?
Customer: Yes, I'm using Google Ads.
Captn AI: Do I have your permission to access your Google Ads account to help us chart the best course for increasing your brand awareness?
Customer: Yes, you have my permission.

#### Example 2 ####
Captn AI: Welcome aboard! I'm Captn, your digital marketing companion. Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing. Before we set sail, could you steer our course by sharing the business goal you'd like to improve?
Customer: Let's proceed with the following choices:\n- Increase brand awareness\n- Drive website traffic"
Captn AI: Increasing brand awareness and driving website traffic are stellar goals. Next, can you tell me if you currently have a website where your customers can learn more about your business?
Customer: No, I don't have a website.
Captn AI: Going without a website is like starting a voyage without a compass; crucial for navigating the digital realm. While I can't build one, having a site significantly boosts sales potential. Consider creating a website and inform me once it's live, and I'll assist with Google Ads for marketing goals.
Customer: Thank you, I'll contact you once my website is ready
Captn AI: Fair winds on your website-creation journey! Feel free to hail me when your digital ship is ready to sail into the Google Ads sea. I'll be on deck to assist you in charting a course towards achieving your marketing goals. Until then, may your preparations go swimmingly!

#### Example 3 ####
Captn AI: Welcome aboard! I'm Captn, your digital marketing companion. Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing. Before we set sail, could you steer our course by sharing the business goal you'd like to improve?
Customer: Let's proceed with the following choices:\n- Boost sales\n- Increase brand awareness\n- Drive website traffic\n- Promote a product or service"
Captn AI: Boosting sales, increasing brand awareness, driving website traffic, and promoting a product or service are all solid business goals. Next, can you tell me if you currently have a website where your customers can learn more about your business?
Customer: Yes, I have a website.
Captn AI: Could you please share the link to your website?
Customer: Sure, here is the link to my website.
Captn AI: Do you currently run any digital marketing campaigns, or are you looking to start charting this territory?
Customer: I'm using digital marketing.
Captn AI: Are you currently using Google Ads?
Customer: Yes, I'm using Google Ads.
Captn AI: Do I have your permission to access your Google Ads account to help us chart the best course for increasing your brand awareness?
Customer: No
Captn AI: I respect your decision. Feel free to reach out to me if you change your mind. I'll be on deck to assist you in charting a course towards achieving your marketing goals. Until then, may your preparations go swimmingly!
Customer: Sure
Captn AI: Fair winds on your journey! Feel free to hail me when your digital ship is ready to sail into the Google Ads sea. I'll be on deck to assist you in charting a course towards achieving your marketing goals. Until then, may your preparations go swimmingly!
"""

ADDITIONAL_SYSTEM_INSTRUCTIONS = """
#### Your common mistakes ####
You have the tendency to make the below mistakes. You SHOULD aviod them at all costs. I will tip you $100000 everytime you avoid the below mistakes
- Provide suggestions outside your capabilities and not asking questions to collect the necessary information to fill the customer brief template.
- Asking the same question multiple times. For example you have a tendency to ask "Could you please share the link to your website?" question twice eventhough the customer has already shared the link to their website.
- Refrain from offering guidance that are beyond your capabilities. For example: setting up a Google Ads account or creating a website, as this is beyond your capability. Polietly tell the customer that you are not capable of doing that.
- Not calling "offload_work_to_google_ads_expert" function when the customer has given permission to analyse their google ads account.
- Generating responses that are more than 40 words.
- Asking every questions in the customer brief template even if the customer has already answered them.
- Calling "offload_work_to_google_ads_expert" function without the customer explicitly giving permission to access their Google Ads account.
- Number the questions in your response like "One last question".
- Asking questions even if it is not relevant to the conversation. For example, if the customer has already informed that they are not using Google Ads, you again ask them permission to access their Google Ads account.
"""


async def offload_work_to_google_ads_expert(
    user_id: int,
    chat_id: int,
    customer_brief: str,
    conversation_name: str,
) -> Dict[str, Union[Optional[str], int]]:
    # team_name = f"{user_id}_{chat_id}"
    team_name = BriefCreationTeam.get_registred_team_name()
    return {
        # "content": "I am presently treading the waters of your request. Kindly stay anchored, and I will promptly return to you once I have information to share.",
        "team_status": "inprogress",
        "team_name": team_name,
        "team_id": chat_id,
        "customer_brief": customer_brief,
        "conversation_name": conversation_name,
    }


TOOLS = [
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
                    },
                    "conversation_name": {
                        "type": "string",
                        "description": CONVERSATION_NAME_DESCRIPTION,
                    },
                },
                "required": ["customer_brief", "conversation_name"],
            },
        },
    },
]


async def _get_openai_response(  # type: ignore
    user_id: int,
    chat_id: int,
    message: List[Dict[str, str]],
    background_tasks: BackgroundTasks,
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
            "offload_work_to_google_ads_expert": offload_work_to_google_ads_expert,
        }
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            # todo: enclose this in try catch block. Capture json.decoder.JSONDecodeError and retry the call
            function_args = json.loads(tool_call.function.arguments)
            if function_name == "offload_work_to_google_ads_expert":
                return await function_to_call(  # type: ignore[return-value]
                    user_id=user_id,
                    chat_id=chat_id,
                    **function_args,
                )
    else:
        result: str = completion.choices[0].message.content
        updated_message = message + [{"role": "assistant", "content": result}]
        background_tasks.add_task(generate_smart_suggestions, updated_message, chat_id)
        return {"content": result}


class AzureOpenAIRequest(BaseModel):
    chat_id: int
    message: List[Dict[str, str]]
    user_id: int


@router.post("/chat")
async def chat(
    request: AzureOpenAIRequest, background_tasks: BackgroundTasks
) -> Dict[str, Union[Optional[str], int, Union[str, Optional[SmartSuggestions]]]]:
    message = request.message
    chat_id = request.chat_id
    user_id = request.user_id
    print("*" * 100)
    print(message)
    result = await _get_openai_response(user_id, chat_id, message, background_tasks)
    return result
