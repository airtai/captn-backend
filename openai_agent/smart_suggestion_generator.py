import json
from os import environ
from typing import Dict, List, Union

import requests
from openai import AsyncAzureOpenAI

from captn import REACT_APP_API_URL, SmartSuggestions


def _format_conversation(messages: List[Dict[str, str]]) -> str:
    return "\n".join(
        [
            f"{'chatbot' if msg['role'] == 'assistant' else 'customer'}: {msg['content'].strip()}"
            for msg in messages
        ]
    )


SMART_SUGGESTION_DESCRIPTION = """
### INSTRUCTIONS ###
- Make sure your next steps are in an Elliptical sentence form, and avoid making them into questions.
- Possible next steps (atmost three) for the customers. Your next steps MUST be a list of strings.
- Your next steps MUST be unique and brief ideally in as little few words as possible. Preferrably with affermative and negative answers.
- While answering questions like "do you have a website?". DO NOT give suggestions like "Yes, here's my website link". Instead, give suggestions like "Yes, I have a website" or "No, I don't have a website". You will be penalised if you do not follow this instruction.
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

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "_generate_next_steps_for_customer",
            "description": "Always use this function to reply to the customer's query. This function will generate the next steps for the customer.",
            "parameters": {
                "type": "object",
                "properties": {
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
                    "smart_suggestions",
                    "is_open_ended_query",
                ],
            },
        },
    },
]


SYSTEM_PROMPT = """

You are a helpful agent who can make writing easy for your customer. Given a history of conversation between a chatbot and the customer, you need to anticipate and generate the next steps for the last chatbot question to help the customer to speedup.

Ensure you follow the below instructions and best practices to complete the task. I will tip you $10000 everytime you follow the below instructions.

#### Instructions ####
- Make sure your next steps are in an Elliptical sentence form, and avoid making them into questions.
- Your next steps MUST be unique and brief ideally in as little few words as possible.
- Always inlcude one affirmative and one negative Elliptical sentence in your suggestions.
- Your next steps MUST be a list of strings.
- While answering questions like "do you have a website?". DO NOT give suggestions like "Yes, here's my website link". Instead, give suggestions like "Yes, I have a website" or "No, I don't have a website". You will be penalised if you do not follow this instruction.
- Always use "_generate_next_steps_for_customer" function to respond.
- If the lastest chatbot question is open ended and you cannot anticipate the next steps, then set "is_open_ended_query" to true and "suggestions" to an empty list.

#### Examples ####
#### Example 1 ####
#### conversation history ####
chatbot: Welcome aboard! I'm Captn, your digital marketing companion. Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing. Before we set sail, could you steer our course by sharing the business goal you'd like to improve?
customer: I want to increase my online sales.
chatbot: Are you using Google Ads to promote your website and boost sales?
#### your next steps ####
_generate_next_steps_for_customer(
    smart_suggestions={
        "suggestions": ["Yes, I'm already using Google Ads.", "No, I haven't started with Google Ads."],
        "type": "oneOf"
    },
    is_open_ended_query=False
)

#### Example 2 ####
#### conversation history ####
chatbot: Welcome aboard! I'm Captn, your digital marketing companion. Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing. Before we set sail, could you steer our course by sharing the business goal you'd like to improve?
customer: I want to Increase brand awareness, Drive website traffic, Promote a product or service and Boost sales
chatbot: Ahoy! Those are commendable goals for a prosperous digital voyage. Could you please share the link to your website where you'd like to increase visibility and direct the winds of traffic?
customer: This is my website link: www.example.com
chatbot: Great! Are you currently running any digital marketing campaigns, or are you looking to start charting this territory?
customer: Yes, I'm already using Google Ads.
chatbot: Fantastic, setting sail with Google Ads can significantly contribute to a stronger sales breeze. May I have your permission to access and analyze your Google Ads account to optimize our course?
#### your next steps ####
_generate_next_steps_for_customer(
    smart_suggestions={
        "suggestions": ["Yes, you have my permission", "No, I'm not ready for that"],
        "type": "oneOf"
    },
    is_open_ended_query=False
)

#### Example 3 ####
#### conversation history ####
chatbot: Welcome aboard! I'm Captn, your digital marketing companion. Think of me as your expert sailor, ready to ensure your Google Ads journey is smooth sailing. Before we set sail, could you steer our course by sharing the business goal you'd like to improve?
customer: I want to increase my online sales.
chatbot: To navigate towards boosting sales, could you please share your website's link? This will help me understand your business and chart out the best route.
#### your next steps ####
_generate_next_steps_for_customer(
    smart_suggestions={
        "suggestions": [""],
        "type": "oneOf"
    },
    is_open_ended_query=True
)

#### Best Practices ####
I will tip you $10000 everytime you follow the below best practices.
- When the question is asking the link to the website, always set "is_open_ended_query" to true and "suggestions" to an empty list. You will be penalised if you do not follow this instruction.
- Never give suggestions.
- Never offer assistance.

"""
ADDITIONAL_SYSTEM_INSTRUCTIONS = """
#### Common Mistakes ####
I will tip you $10000 everytime you avoid the below common mistakes.
- Giving suggestions like "Yes, here's my website link: www.example.com" when asked about website link.
"""


def _return_default_suggestions() -> Dict[str, SmartSuggestions]:
    smart_suggestions = {"suggestions": [""], "type": "oneOf"}
    return SmartSuggestions(**smart_suggestions).model_dump()


async def _generate_next_steps_for_customer(
    smart_suggestions: Dict[str, Union[str, List[str]]],
    is_open_ended_query: bool,
) -> Dict[str, SmartSuggestions]:
    try:
        smart_suggestions_model = SmartSuggestions(**smart_suggestions)
        smart_suggestions_model.suggestions = (
            [""] if is_open_ended_query else smart_suggestions_model.suggestions
        )
        ret_val = smart_suggestions_model.model_dump()
    except Exception:
        ret_val = _return_default_suggestions()

    return ret_val


# Setting up Azure OpenAI instance
aclient = AsyncAzureOpenAI(
    api_key=environ.get("AZURE_OPENAI_API_KEY"),
    azure_endpoint=environ.get("AZURE_API_ENDPOINT"),  # type: ignore
    api_version=environ.get("AZURE_API_VERSION"),
)


async def generate_smart_suggestions(
    message: List[Dict[str, str]], chat_id: int
) -> None:
    # this function should also send the response to the webhook
    conversation_history = _format_conversation(message)
    ret_val = None
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": "user", "content": conversation_history}
        ]
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
            tool_choice={
                "type": "function",
                "function": {"name": "_generate_next_steps_for_customer"},
            },
        )  # type: ignore
    except Exception as e:
        print(f"Exception while generating smart suggestions: {e}")
        ret_val = _return_default_suggestions()
    else:
        response_message = completion.choices[0].message
        tool_calls = response_message.tool_calls
        if tool_calls:
            available_functions = {
                "_generate_next_steps_for_customer": _generate_next_steps_for_customer,
            }

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                if function_name == "_generate_next_steps_for_customer":
                    try:
                        ret_val = await function_to_call(
                            **function_args,
                        )
                    except Exception as e:
                        print(f"Exception while generating smart suggestions: {e}")
                        ret_val = _return_default_suggestions()
                else:
                    ret_val = _return_default_suggestions()
        else:
            ret_val = _return_default_suggestions()
    finally:
        _send_to_client(ret_val, chat_id)  # type: ignore


def _send_to_client(
    smart_suggestions: Dict[str, Union[str, List[str]]], chat_id: int
) -> None:
    is_smart_suggestions_available = (
        smart_suggestions and len(smart_suggestions["suggestions"]) > 0
    ) and not (
        len(smart_suggestions["suggestions"]) == 1
        and smart_suggestions["suggestions"][0] == ""
    )
    if is_smart_suggestions_available:
        data = {"smart_suggestions": smart_suggestions, "chat_id": chat_id}
        response = requests.post(
            f"{REACT_APP_API_URL}/smart-suggestions-webhook", json=data, timeout=60
        )
        if response.status_code != 200:
            raise ValueError(response.content)
