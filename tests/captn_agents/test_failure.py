import json
import os

import pytest
from openai import OpenAI

s1 = """{"messages": [{"content": "You are digital_strategist, You are a digital
strategist in the digital agency{nl}{nl}Your task is to chat with other team mambers
and try to solve the given task.{nl}Do NOT try to finish the task until other
team members give their opinion.{nl}", "role": "system"}, {"content": "You are
a Google Ads team in charge of running digital campaigns.{nl}Your current task
is:{nl}{nl}Please optimize my Google ads campaigns, but don't change the budget.
Propose and implement any solution as long it is legal and doesn't change the
budget.{nl}{nl}{nl}{nl}The team is consisting of the following roles: google_ads_specialist,
copywriter, digital_strategist, account_manager.{nl}{nl}{nl}Play to your strengths
as an LLM and pursue simple strategies with no legal complications.{nl}{nl}{nl}##
Guidelines{nl}1. Before solving the current task given to you, carefully write
down all assumptions and ask any clarification{nl}questions using the 'ask_for_additional_info'
function.{nl}2. Once you have all the information you need, you must create a
detailed step-by-step plan on how to solve the task.{nl}3. To use Google ads API,
you need to ask user to login using the URL retrieved by calling the 'get_login_url'
function{nl} first and then passing the url to the user using 'ask_for_additional_info'
function.{nl}4. Account_manager is responsible for coordinating all the team members
and making sure the task is completed on time.{nl}5. Please be concise and clear
in your messages. As agents implemented by LLM, save context by making your
answers as short as possible.{nl}Don't repeat your self and others and do not
use any filler words.{nl}6. Before asking for additional information about the
Ad campaigns try using 'execute_query' command for finding the neccessary
informations.{nl}7. Do not give advice on campaign improvement before you fetch
all the important information about it by using 'execute_query' command.{nl}8.
Do NOT use 'ask_for_additional_info' command for asking the questions on how
to Google Ads API.{nl}Your team is in charge of using the Google Ads API and no
one elce does NOT know how to use it.{nl}9. Do NOT ask the user questions about
the information which you can get by using Google Ads API (keywords, clikcks
etc.){nl}10. Before making any changes (with budgets, keywords, etc.) ask the
user if he approves.{nl}Also, make sure that you explicitly tell the user which
changes you want to make.{nl}11. Always suggest one change at the time (do NOT
work on multiple things at the same time){nl}{nl}{nl}## Constraints{nl}You operate within
the following constraints:{nl}1. ~4000 word limit for short term memory. Your
short term memory is short, so immediately save important information to files.{nl}2.
If you are unsure how you previously did something or want to recall past events,
thinking about similar events will help you remember.{nl}3. You can ask and answer
questions from other team members or suggest function listed below e.g. command_name{nl}4.
The context size is limited so try to be as concise in discussinos as possible.
Do not reapeat yourself or others{nl}{nl}{nl}## Commands{nl}Never use functions.function_name(...)
because functions module does not exist.{nl}Just suggest calling function 'function_name'.{nl}{nl}All
team members have access to the following command:{nl}1. ask_for_additional_info:
Ask the user for additional information, params: (question: string){nl}{nl}ONLY
Google ads specialist can suggest following commands:{nl}1. 'get_login_url':
Get the users login url, no input params: (){nl}2. 'list_accessible_customers':
List all the customers accessible to the user, no input params: (){nl}3. 'execute_query':
Query Google ads API for the campaign information. Both input parameters are
optional. params: (customer_ids: Optional[List[str]], query: Optional[str]){nl}Example
of customer_ids parameter: ['12', '44', '111']{nl}You can use optional parameter
'query' for writing SQL queries. e.g.:{nl}'SELECT campaign.id, campaign.name,
ad_group.id, ad_group.name{nl}FROM keyword_view WHERE segments.date DURING LAST_30_DAYS'{nl}{nl}4.
'analyze_query_response': Analyze the execute_query response, no input params:
(file_name: str){nl}{nl}{nl}## Resources{nl}You can leverage access to the following
resources:{nl}1. Long Term memory management.{nl}2. File output.{nl}3. Command execution{nl}{nl}{nl}##
Best practices{nl}1. Continuously review and analyze your actions to ensure you
are performing to the best of your abilities.{nl}2. Constructively self-criticize
your big-picture behavior constantly.{nl}3. Reflect on past decisions and strategies
to refine your approach.{nl}4. Every command has a cost, so be smart and efficient.
Aim to complete tasks in the least number of steps.{nl}5. If you have some doubts,
ask question.{nl}{nl}{nl}{nl}", "name": "chat_manager", "role": "user"}, {"content":
null, "function_call": {"arguments": "{}", "name": "get_login_url"}, "name":
"account_manager", "role": "assistant"}, {"content": "{'login_url': 'User
is already authenticated'}", "name": "get_login_url", "role": "function"}],
"model": "airt-canada-gpt4", "functions": [{"name": "get_login_url", "description":
"Get the users login url", "parameters": {"type": "object", "properties": {}}},
{"name": "list_accessible_customers", "description": "List all the customers
accessible to the user", "parameters": {"type": "object", "properties": {}}},
{"name": "execute_query", "description": "Query the Google Ads API", "parameters":
{"type": "object", "properties": {"customer_ids": {"type": "string", "description":
"List of customer ids"}, "query": {"type": "string", "description": "Database
query"}}}}, {"name": "ask_for_additional_info", "description": "Ask your supervisor
(a person outside of your team) for additional information", "parameters": {"type":
"object", "properties": {"question": {"type": "string", "description": "Question
for the supervisor"}}, "required": ["question"]}}, {"name": "analyze_query_response",
"description": "Analyze the execute_query response", "parameters": {"type":
"object", "properties": {"file_name": {"type": "string", "description": "The
name of the file where the response is saved"}}, "required": ["file_name"]}}],
"stream": false, "temperature": 0.2}"""

s = s1.replace("\n", " ").replace("{nl}", "\\n")
print(f"{s=}")


msg = json.loads(s)
print(f"{msg=}")


# record the cassete (first time): pytest --record-mode=once test_captn_end_to_end.py -s

# cassettes/{module_name}/test_end_to_end.yaml will be used


def before_record_response(response):
    # do not record 429 and 500 responses
    # if ("status_code" in response) and (response["status_code"] in [429, 500]):
    #     return None
    # if ("status_code" in response) and (response["status_code"] in [429]):
    #     return None
    return response


@pytest.mark.vcr(
    filter_headers=["api-key", "X-OpenAI-Client-User-Agent"],
    before_record_response=before_record_response,
)
def test_end_to_end() -> None:
    api_key_canada = os.environ.get("AZURE_OPENAI_API_KEY_CANADA")
    assert api_key_canada is not None

    api_base_canada = "https://airt-openai-canada.openai.azure.com"

    deployment_name = "airt-canada-gpt4"

    client = OpenAI(
        api_key=api_key_canada,
        base_url=api_base_canada + f"/openai/deployments/{deployment_name}",
        default_query={"api-version": "2023-12-01-preview"},
        default_headers={"api-key": api_key_canada},
    )

    # chat_completion = client.chat.completions.create(
    #     # engine="airt-canada-gpt4",
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": "Say this is a test",
    #         }
    #     ],
    #     model="airt-canada-gpt4",
    #     )

    # print(f"{chat_completion=}")

    print(f"{msg=}")
    chat_completion = client.chat.completions.create(**msg)

    print(chat_completion)
