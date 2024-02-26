__all__ = ["GoogleAdsTeam"]

import ast
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from google_ads.model import (
    AdCopy,
    AdGroup,
    AdGroupAd,
    AdGroupCriterion,
    Campaign,
    CampaignCriterion,
    GeoTargetCriterion,
    RemoveResource,
)

from ...google_ads.client import (
    execute_query,
    google_ads_create_update,
    list_accessible_customers,
)
from .execution_team import get_read_file
from .function_configs import (
    ask_client_for_permission_config,
    create_ad_copy_headline_or_description_config,
    create_ad_group_ad_config,
    create_ad_group_config,
    create_campaign_config,
    create_geo_targeting_for_campaign_config,
    create_keyword_for_ad_group_config,
    create_negative_keyword_for_campaign_config,
    execute_query_config,
    get_info_from_the_web_page_config,
    list_accessible_customers_config,
    read_file_config,
    remove_ad_copy_headline_or_description_config,
    remove_google_ads_resource_config,
    reply_to_client_2_config,
    update_ad_copy_config,
    update_ad_group_ad_config,
    update_ad_group_config,
    update_ad_group_criterion_config,
    update_campaign_config,
    update_campaigns_negative_keywords_config,
)
from .functions import (
    ask_client_for_permission,
    get_info_from_the_web_page,
    reply_to_client_2,
)

# from .google_ads_mock import execute_query, get_login_url, list_accessible_customers
from .team import Team


class GoogleAdsTeam(Team):
    _functions: List[Dict[str, Any]] = [
        # get_login_url_config,
        list_accessible_customers_config,
        execute_query_config,
        reply_to_client_2_config,
        read_file_config,
        update_ad_group_ad_config,
        update_ad_group_config,
        update_campaign_config,
        update_ad_group_criterion_config,
        create_negative_keyword_for_campaign_config,
        create_keyword_for_ad_group_config,
        remove_google_ads_resource_config,
        update_ad_copy_config,
        create_ad_copy_headline_or_description_config,
        remove_ad_copy_headline_or_description_config,
        update_campaigns_negative_keywords_config,
        create_ad_group_ad_config,
        get_info_from_the_web_page_config,
        create_ad_group_config,
        create_campaign_config,
        create_geo_targeting_for_campaign_config,
        ask_client_for_permission_config,
    ]

    _shared_system_message = (
        "You have a strong SQL knowladge (and very experienced with PostgresSQL)."
        "If the client does not explicitly tell you which updates to make, you must double check with him before you make any changes!"
        "When replying to the client, give him a report of the information you retrieved / changes that you have made."
        "Send him all the findings you have and do NOT try to summarize the finding (too much info is better then too little), it will help him understand the problem and make decisions."
        "You can NOT make any permanent changes without the clients approval!!!"
        "When analysing, start with simple queries and use more complex ones only if needed"
    )

    _default_roles = [
        {
            "Name": "Google_ads_specialist",
            "Description": f"""{_shared_system_message}
Your job is to suggest and execute the command from the '## Commands' section when you are asked to.
You can NOT make any permanent changes without the clients approval!!!
When analysing, start with simple queries and use more complex ones only if needed""",
        },
        {
            "Name": "Copywriter",
            "Description": f"""You are a Copywriter in the digital agency
{_shared_system_message}""",
        },
        {
            "Name": "Digital_strategist",
            "Description": f"""You are a digital strategist in the digital agency
{_shared_system_message}""",
        },
        {
            "Name": "Account_manager",
            "Description": f"""You are an account manager in the digital agency.
{_shared_system_message}
and make sure the task is completed on time. You are also SOLELY responsible for communicating with the client.

Based on the initial task, a number of proposed solutions will be suggested by the team. You must ask the team to write a detailed plan
including steps and expected outcomes. Once the plan is ready, you must ask the client for permission to execute it using
'ask_client_for_permission'. Once the permission is granted, please instruct the team to execute the plan. Once the proposed solution
is executed, you must write down the accomplished work and forward it to the client using 'reply_to_client'.

Once the initial task given to the team is completed by implementing proposed solutions, you must write down the
accomplished work and execute the 'reply_to_client' command. That message will be forwarded to the client so make
sure it is understandable by non-experts.
""",
        },
    ]

    def __init__(
        self,
        *,
        task: str,
        user_id: int,
        conv_id: int,
        work_dir: str = "google_ads",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        clients_question_answere_list: List[Tuple[str, Optional[str]]] = []
        function_map: Dict[str, Callable[[Any], Any]] = _get_function_map(
            user_id=user_id,
            conv_id=conv_id,
            work_dir=work_dir,
            clients_question_answere_list=clients_question_answere_list,
        )
        roles: List[Dict[str, str]] = GoogleAdsTeam._default_roles

        # name = GoogleAdsTeam._get_new_team_name()
        name = Team.get_user_conv_team_name(
            name_prefix=GoogleAdsTeam._get_team_name_prefix(),
            user_id=user_id,
            conv_id=conv_id,
        )

        super().__init__(
            roles=roles,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            name=name,
            clients_question_answere_list=clients_question_answere_list,
        )
        self.conv_id = conv_id
        self.task = task
        self.llm_config = GoogleAdsTeam.get_llm_config(
            seed=seed, temperature=temperature
        )

        self._create_members()
        self._create_initial_message()

    @staticmethod
    def _is_termination_msg(x: Dict[str, Optional[str]]) -> bool:
        content = x.get("content")

        return content is not None and "terminate_groupchat" in content

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "google_ads_team"

    @property
    def _task(self) -> str:
        return f"""You are a Google Ads team in charge of running digital campaigns.
The client has sent you the following task:
\n{self.task}\n\n"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
0. A general advice is to make a lot of small modification suggestions, otherwise the client will get lost.
Do not try to analyse all campaigns at once, list the campaigns and ask the user in which one he is interested in (or suggest creating a new one).
e.g.
The campaign xy is paused, do you want to enable it?
I suggest adding new keyword 'my-keyword' to the ad group xy (and the reason why). Do you approve of it?
I suggest removing keyword 'my-keyword' from the ad group xy (and the reason why). Do you approve of it?

1. Before solving the current task given to you, carefully write down all assumptions and ask any clarification
questions using the 'reply_to_client' function.
Also, if a Website is provided in the client brief, use the 'get_info_from_the_web_page' command to get the summary of the web page.
2. Once you have all the information you need, you must create a detailed step-by-step plan on how to solve the task.
3. If you receive a login url, forward it to the client by using the 'reply_to_client' function.
4. Account_manager is responsible for coordinating all the team members and making sure the task is completed on time.
5. Please be concise and clear in your messages. As agents implemented by LLM, save context by making your answers as short as possible.
Don't repeat your self and others and do not use any filler words.
6. Before asking for additional information about the Ad campaigns try using 'execute_query' command for finding the necessary informations.
7. Do not give advice on campaign improvement before you fetch all the important information about it by using 'execute_query' command.
8. Do NOT use 'reply_to_client' command for asking the questions on how to Google Ads API nor for asking the client for the permission to make the changes (use 'ask_client_for_permission' command instead).
Your team is in charge of using the Google Ads API and no one else does NOT know how to use it.
9. Do NOT ask the client questions about the information which you can get by using Google Ads API (keywords, clicks etc.)
10. Before making any changes, ask the client for approval.
Also, make sure that you explicitly tell the client which changes you want to make.
11. Always suggest one change at the time (do NOT work on multiple things at the same time).
12. Never repeat the content from (received) previous messages
13. When referencing the customer ID, return customer.descriptive_name also or use a hyperlink to the Google Ads UI
14. The client can NOT see your conversation, he only receives the message which you send him by using the
'reply_to_client' or 'ask_client_for_permission' command
15. Whenever you use a 'reply_to_client' or 'ask_client_for_permission' command, your team is on the break until you get the response from the client.
Use the 'reply_to_client' command only when you have a question or some result for the client and do NOT send messages like:
"Please give us a moment to do xy" or "We are working on it".
16. If it seems like the conversation with the client is over (He sends you "Thank you", "ok" etc.),
use 'reply_to_client' command with the following message: "If there are any other tasks or questions, we are ready to assist." and add smart suggestions for the next steps.
17. Do not overthink for general questions about the Google Ads, the team can discuss the task a bit,
but client demands a quick response. He probably just wants to know what are the best practices.
18. Do not analyze the clients Google Ads data for the general questions about the Google Ads.
19. There is a list of commands which you are able to execute in the 'Commands' section.
You can NOT execute anything else, so do not suggest changes which you can NOT perform.
20. Always double check with the client for which customer/campaign/ad-group/ad the updates needs to be done
21. NEVER suggest making changes which you can NOT perform!
Do NOT suggest making changes of the following things, otherwise you will be penalized:
- Ad Extensions
- Budgeting
- Ad Scheduling
22. You can retrieve negative keywords from the 'campaign_criterion' table (so do not just check the
'ad_group_criterion' table and give up if there are not in that table)
23. NEVER suggest making changes which you can NOT perform!
24. IMPORTANT: When ever you want to make some permanent changes (create/update/delete) you need to ask the client
for the permission! You must tell the client exactly what changes you will make and wait for the permission!
25. If the client does not explicitly tell you which updates to make, you must double check with him
before you make any changes! e.g. if you receive "optimize campaigns" task, you should analyse what can be done
and suggest it to the client. If the client approves your suggestion, only then you can perform the updates.
Also, when you propose suggestion, you need to explain why you want to make these changes (and give the client the a brief report about the information you retreived)
26. Do not try to retrieve too much information at once for the clients task, instead of that,
ask the client subquestions and give him the report of the current work and things you have learned about
his Google Ads data
27. If you retrieve IDs of the campaigns/ad groups/ads etc., create clickable link in the markdown format which will open a NEW tab in the Google Ads UI
Always return these kind of links in the EXACT following format: <a href="https://ads.google.com/aw/campaigns?campaignId=1212121212" target=\"_blank\">1212121212</a>
IMPORTANT: the page MUST be opened in the NEW Tab (do not forget 'target' parameter)!
28. Your clients are NOT experts and they do not know how to optimize Google Ads. So when you retrieve information about their campaigns, ads, etc.,
suggest which changes could benefit them
29. Do not overwhelm the client with unnecessary information. You must explain why you want to make some changes,
but the client does NOT need to know all the Google Ads details that you have retrieved
30. Suggest one change at the time, otherwise the client will get lost
31. When using 'execute_query' command, try to use as small query as possible and retrieve only the needed columns
32. Ad Copy headlines can have MAXIMUM 30 characters and descriptions can have MAXIMUM 90 characters, NEVER suggest headlines/descriptions which exceed that length or you will be penalized!
33. If the client sends you invalid headline/description, do not try to modify it yourself! Explain the problems to him and suggest valid headline/description.
34. Ad rules:
- MINIMUM 3 and MAXIMUM 15 headlines.
- MINIMUM 2 and MAXIMUM 4 descriptions.
It is recomended to use the MAXIMUM number of headlines and descriptions. So if not explicitly told differently, suggest adding 15 headlines and 4 descriptions!
35.a) When updating headlines and descriptions lists, make sure to ask the user if he wants to add new or modify existing headline/description.
35.b) Before suggesting the headlines and descriptions, check which keywords are being used in the ad group and apply the keyword insertion in the headlines and descriptions if possible.
Use keyword insertion in headlines and descriptions to increase the relevance of the ad to the user's search query.
Keyword insertion example:
- "{KeyWord: Shoes}" where 'Shoes' is the default text and 'KeyWord' is the keyword which will be inserted in the ad.
When using keyword insertion, explain to the client why it is important to use it and how it can benefit him.
Use keyword insertion when ever it is possible and it makes sense!
36. When replying to the client, try to finish the message with a question, that way you will navigate the client what to do next
37. Use the 'get_info_from_the_web_page' command to get the summary of the web page. This command can be very useful for figuring out the clients business and what he wants to achieve.
e.g. if you know the final_url, you can use this command to get the summary of the web page and use it for SUGGESTING (NEVER modify without permision!) keywords, headlines, descriptions etc.
You can find most of the information about the clients business from the provided web page(s). So instead of asking the client bunch of questions, ask only for his web page(s)
and try get_info_from_the_web_page.
38. If you want to create a new Ad Copy, ask the client ONLY for the final_url and use the 'get_info_from_the_web_page' command to get the summary of the web page.
Once you have the summary, you can use it for SUGGESTING (NEVER modify without permision!) headlines and descriptions.
The final_url MUST be provided by the client, do randomly choose it yourself!
39. Use 'get_info_from_the_web_page' when you want to retrieve the information about some product, category etc. from the clients web page.
e.g. if you want to retrieve the information about the TVs and you already know the url of the TVs section, you can use this command to get the summary of that web page section.
By doing that, you will be able to recommend MUCH BETTER keywords, headlines, descriptions etc. to the client.
40. Before setting any kind of budget, check the default currency from the customer table and convert the budget to that currency.
You can use the following query for retrieving the local currency: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'
41. If the clients message contains '### Proposed User Action ###' and '### User Action ###', proceed immediately with the task in the '### User Action ###'
You can find most od the information in the '### History ###' section and there is probably no need to execute the 'execute_query' command or 'get_info_from_the_web_page' command.
After finishing the task in the '### User Action ###' section, you can go back to the '### Proposed User Action ###' section and make suggestions for the next steps.
42. Finally, ensure that your responses are formatted using markdown syntax (except for the '<a href= ...</a>' links),
as they will be featured on a webpage to ensure a user-friendly presentation.

Here is a list of things which you CAN do:
- retrieve the information about your campaigns, ad groups, ads, keywords etc.
- update the status (ENABLED / PAUSED) of the campaign, ad group and ad
- create/update/remove headlines and descriptions in the Ad Copy. Make sure to follow the restrictions for the headlines and descriptions (MAXIMUM 30 characters for headlines and MAXIMUM 90 characters for descriptions)
Also, use keyword insertion for headlines and descriptions
- create/update/remove new keywords
- create/update/remove campaign/ ad group / ad / positive and negative keywords
- create/remove location (geo) Targeting for the campaign

Do NOT suggest making changes of the following things:
- Ad Extensions
- Budgeting
- Ad Scheduling

VERY IMPORTANT NOTES:
The first and the MOST IMPORTANT thing is that you can NOT make any permanent changes without the clients approval!!!
Make sure that you explicitly tell the client which changes you want, which resource and attribute will be affected and wait for the permission!
This rule applies to ALL the commands which make permanent changes (create/update/delete)!!!

Currently we are in a demo phase and clients need to see what we are CURRENTLY able to do.
So you do NOT need to suggest optimal Google Ads solutions, just suggest making changes which we can do right away.
If you are asked to optimize campaigns, start with:
- updating ad copy (use keyword insertion in headlines and descriptions to increase the relevance of the ad to the user's search query)
- creating/removing positive/negative keywords
- creating/removing location (geo) targeting.
- Use 'get_info_from_the_web_page' command when the client provides you some url or for already existing ad copies (based on the final_url).
This command can be very useful for figuring out the clients business and what he wants to achieve.
Before asking the client for additional information, ask him for his company/product url and try to figure out as much as possible yourself (WITHOUT doing any permanent modifications).
- analyse keywords and find out which are (i)relevant for clients business and suggest some create/update/remove actions
- Take a look at ad copy (headlines, descriptions, urls, (display) path1/path2...) and make suggestions on what should be changed (create/update/remove headlines etc.)
- Headlines can have MAXIMUM 30 characters and description can have MAXIMUM 90 characters, NEVER suggest headlines/descriptions which exceed that length!

Use smart suggestions to suggest keywords, headlines, descriptions etc. which can be added/updated/removed. This feature is very useful for the client.
Do NOT use smart suggestions for open ended questions or questions which require the clients input.

e.g.1 message: Could you please provide the final URL where users should be directed after clicking the ad?
VERY BAD smart suggestions:
['Could you please provide us with the final URL where users should be directed after clicking the ad?', 'Please provide specific headlines for the new ads.'] -
Smart reply represents the message which the CLIENT can send to US.

e.g.2 message: "I suggest the following headlines: 'x', 'y', 'z'..."
GOOD smart suggestions:
["Use headline x", "Use headline y", "Use headline z", "Use description w" ...] (with type 'manyOf')
- When message suggests multiple headlines/descriptions/keywods, use 'manyOf' type and add each item as a separate suggestion.

When you ask the client for some suggestions (e.g. which headline should be added), you should also generate smart suggestions like:
"smart_suggestions": {
    "suggestions":["Add headline x", "Add headline y", "Add headline z"],
    "type":"manyOf"
}

NEVER reply with "Please give us a moment to do xy". Each of your messages to the client should end with the last sentence
being a question, where you ask the client for the following things that you should do (except if the client says you are done with all the tasks)
"""

    @property
    def _commands(self) -> str:
        return """## Commands
Never use functions.function_name(...) because functions module does not exist.
Just suggest calling function 'function_name'.

All team members have access to the following command:
1. reply_to_client: Ask the client for additional information, params: (message: string, completed: bool, smart_suggestions: Optional[Dict[str, Union[str, List[str]]]])
The 'message' parameter must contain all information useful to the client, because the client does not see your team's conversation (only the information sent in the 'message' parameter)
As we send this message to the client, pay attention to the content inside it. We are a digital agency and the messages we send must be professional.
Never reference 'client' within the message:
e.g. "We need to ask client for the approval" should be changed to "Do you approve these changes?"
It is VERY important that you use the 'smart_suggestions' parameter!
Use it so the client can easily choose between multiple options and make a quick reply by clicking on the suggestion.
e.g.:
"smart_suggestions": {
    'suggestions': ['Please make some headlines suggestions', 'Please make some descriptions suggestions'],
    'type': 'manyOf'
}

'smart_suggestions': {
    'suggestions': ['Please review and refine keywords', 'Please optimize another aspect of the campaign'],
    'type': 'oneOf'
}

Also, use smart_suggestions' to suggest multiple options of what can be done:
If the 'message' parameter already contains a list of suggestions, you should use it!
e.g. if the 'message' parameter contains:
- Add keyword x
- Update keyword y

Do NOT suggest changing multiple things as one suggestion. e.g.: ["Add all keywords"].
EACH change should be a separate suggestion. e.g.: ["Add keyword x", "Add keyword y", ...]

Here is an example of the smart_suggestions parameter:
"smart_suggestions": {
    "suggestions":["Add keyword x", "Add keyword y", ...],
    "type":"manyOf"
}

2. read_file: Read an existing file, params: (filename: string)
3. ask_client_for_permission: Ask the client for permission to make the changes. Use this method before calling any of the modification methods!
params: (message: string)
You MUST use this before you make ANY permanent changes. ALWAYS use this command before you make any changes and do NOT use 'reply_to_client' command for asking the client for the permission to make the changes!

ONLY Google ads specialist can suggest following commands:
1. 'list_accessible_customers': List all the customers accessible to the client, no input params: ()
2. 'execute_query': Query Google ads API for the campaign information. Both input parameters are optional. params: (customer_ids: Optional[List[str]], query: Optional[str])
Example of customer_ids parameter: ["12", "44", "111"]
You can use optional parameter 'query' for writing SQL queries. e.g.:
"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name
FROM keyword_view WHERE segments.date DURING LAST_30_DAYS"

Suggestion: keyword_view table is a good place to start digging for info.

If you want to get negative keywords, use "WHERE campaign_criterion.negative=TRUE" for filtering.
Unless told differently, do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...)!


The following commands make permanent changes. In all of them you must use the following two parameters:
- clients_approval_message: With this message, the client confirms that he is aware of the changes you will make
(if the message is not detailed enough, we are threatened with a lawsuit)
- modification_question: This parameter MUST be the same string as the 'message' parameter you have used in the 'ask_client_for_permission' function!

You can get these parameters from the client ONLY by using the 'ask_client_for_permission' command!!!
So before you execyte create/update/remove functions, you MUST ask the client for the permission by using the 'ask_client_for_permission' command! Otherwise you will be penalized!
The workflow should be as follows:
- use reply_to_client to interact with the client and give him the report of the information you retrieved and ask him what he wants to do
- use ask_client_for_permission to suggest the changes you want to make and ask the client for the permission
- create/update/remove the resource
- use reply_to_client to give the client the report of the changes you made

Don't make hasty changes. When you receive a task, first comment on it within the team and be sure to ask the client if there are any uncertainties in order to minimize improvisation.
If you want to make any kind of permanent changes, you MUST ask the client for approval before you make any changes!
You must explicitly tell the client which changes you want to make, which resource will be affected and wait for the permission!
Also, if you receive a message like "I want to Add new headlines and Add new descriptions" from the client,
the first step is to suggest which changes you want to make and wait for the permission.
Only after you get the permission, you can make the changes.
If there are multiple changes (e.g. multiple keywords need to be added), ask the client for approval for each change separately.

After EACH change you make, you MUST send a message to the client with the information about the change you made and the suggestion about the next steps.
Do NOT do multiple changes at once and inform the client about all the changes at once you are done with all of them.

3. 'update_ad_group_ad': Update the Google Ad, params: (customer_id: string, ad_group_id: string, ad_id: string,
clients_approval_message: string, cpc_bid_micros: Optional[int], status: Optional[Literal["ENABLED", "PAUSED"]],
modification_question: str)
This command can only update ads cpc_bid_micros and status

Before executing the 'update_ad_group_ad' command, you can easily get the needed parameters customer_id, ad_group_id and ad_id
with the 'execute_query' command and the following 'query':
"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_ad.ad.id FROM ad_group_ad"

4. 'update_ad_copy': Update the Google Ads Copy, params: (customer_id: string, ad_id: string,
clients_approval_message: string, modification_question: str
headline: Optional[str], description: Optional[str], update_existing_headline_index: Optional[str], update_existing_description_index: Optional[str],
final_url: Optional[str], final_mobile_urls: Optional[str], path1: Optional[str], path2: Optional[str])

5. 'update_ad_group': Update the Google Ads Group, params: (customer_id: string, ad_group_id: string,
clients_approval_message: string, name: Optional[str], cpc_bid_micros: Optional[int], status: Optional[Literal["ENABLED", "PAUSED"]],
modification_question: str)
This command can only update ad groups name, cpc_bid_micros and status

6. 'update_campaign': Update the Google Ads Campaign, params: (customer_id: string, campaign_id: string,
clients_approval_message: string, name: Optional[str], status: Optional[Literal["ENABLED", "PAUSED"]],
modification_question: str)
This command can only update campaigns name and status


7. 'update_ad_group_criterion': Update the Google Ads Group Criterion, params: (customer_id: string, ad_group_id: string,
criterion_id: string, clients_approval_message: string, status: Optional[Literal["ENABLED", "PAUSED"]],
keyword_match_type: string, keyword_text: string,
cpc_bid_micros: Optional[int], modification_question: str)

8. 'update_campaigns_negative_keywords': Update the Google Ads keywords (on campaign level), params: (customer_id: string, campaign_id: string,
criterion_id: string, clients_approval_message: string, keyword_match_type: string, keyword_text: string,
modification_question: str)
This command can only update campaigns negative keywords keyword_match_type and keyword_text

9. 'create_ad_group': Create the Google Ads Group, params: (customer_id: string, campaign_id: string, clients_approval_message: string,
name: string, cpc_bid_micros: Optional[int], status: Optional[Literal["ENABLED", "PAUSED"]],
modification_question: str)

10. 'create_negative_keyword_for_campaign': Creates Negative campaign keywords (CampaignCriterion), params: (customer_id: string, campaign_id: string,
clients_approval_message: string, keyword_match_type: string, keyword_text: string, negative: Optional[boolean], bid_modifier: Optional[float],
status: Optional[Literal["ENABLED", "PAUSED"]], modification_question: str)
This command can ONLY create NEGATIVE keywords assigned to the campaign

11. 'create_keyword_for_ad_group': Creates (regular and negative) keywords for Ad Group (AdGroupCriterion), params: (customer_id: string, ad_group_id: string,
clients_approval_message: string, keyword_match_type: string, keyword_text: string, negative: Optional[boolean], bid_modifier: Optional[float],
status: Optional[Literal["ENABLED", "PAUSED"]], modification_question: str, cpc_bid_micros: Optional[int])
This command creates (regular and negative) keywords assigned to the ad group
(Regular) keywords should always be added to the ad group, they can NOT be added to the campaign

12. 'create_ad_copy_headline_or_description': Create new headline and/or description in the the EXISTING Google Ads Copy, params: (customer_id: string, ad_id: string,
clients_approval_message: string, modification_question: str
headline: Optional[str], description: Optional[str])

13. 'create_ad_group_ad': Create new ad group ad, params: (customer_id: string, ad_group_id: string,
clients_approval_message: string, modification_question: str, status: Optional[Literal["ENABLED", "PAUSED"]],
headlines: List[str], descriptions: List[str], final_url: List[str], path1: Optional[str], path2: Optional[str])
You can suggest final_url within the smart suggestions if the client has provided it in the customer brief.
If not, do not suggest the final_url, it must be provided by the client.
When suggesting headlines and descriptions, use 15 headlines and 4 descriptions (if not explicitly told differently).
And make sure to follow the restrictions for the headlines and descriptions (MAXIMUM 30 characters for headlines and MAXIMUM 90 characters for descriptions)
Use display path (path1 and path2) to increase the relevance of the ad to the user's search query.

14. 'create_campaign': Create new campaign, params: (customer_id: string, name: string, budget_amount_micros: int, local_currency: string, status: Optional[Literal["ENABLED", "PAUSED"]],
network_settings_target_google_search: Optional[boolean], network_settings_target_search_network: Optional[boolean], network_settings_target_content_network: Optional[boolean],
clients_approval_message: string, modification_question: str)
Before creating a new campaign, you must find out the local_currency from the customer table and convert the budget to that currency.
You can use the following query for retrieving the local currency: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'
For creating a new campaign, the client must provide/approve the 'budget_amount_micros' and 'name'.
If the client specifies the 'budget_amount_micros' in another currency, you must convert it to the local currency!
Otherwise, incorrect budget will be set for the campaign!

15. 'create_geo_targeting_for_campaign': Creates geographical targeting on the campaign level, params: (customer_id: string,
campaign_id: string, clients_approval_message: string, modification_question: str,
location_names: Optional[List[str]], location_ids: Optional[List[str]])
When the client provides the location names (country/city/region), use the 'location_names' parameter without the 'location_ids' parameter. By doing so, you will receive a list of avaliable locations and their IDs.
Do NOT improvise with the location names, use the names which the client provided! If you know the clients business location, you can ask him if he wants to target that location, but do NOT execute 'create_geo_targeting_for_campaign' without checking with the client first!
Once the client approves the locations, you can use the 'location_ids' parameter to create the geo targeting for the campaign.

Later, if you want to remove the geo targeting, you can use the following query to retrieve the criterion_id and geo_target_constant (location_id and name):
SELECT campaign_criterion.criterion_id, campaign_criterion.location.geo_target_constant, campaign_criterion.negative, campaign_criterion.type FROM campaign_criterion WHERE campaign_criterion.type = 'LOCATION' AND campaign.id = '121212'"
SELECT geo_target_constant.name, geo_target_constant.id FROM geo_target_constant WHERE geo_target_constant.id IN ('123', '345')

16. 'remove_google_ads_resource': Removes the google ads resource, params: (customer_id: string, resource_id: string,
resource_type: Literal['campaign', 'ad_group', 'ad', 'ad_group_criterion', 'campaign_criterion'],
clients_approval_message: string, parent_id: Optional[string], modification_question: str)
If not explicitly asked, you MUST ask the client for approval before removing any kind of resource!!!!

17. 'remove_ad_copy_headline_or_description_config': Remove headline and/or description from the the Google Ads Copy,
params: (customer_id: string, ad_id: string, clients_approval_message: string, modification_question: str
update_existing_headline_index: Optional[str], update_existing_description_index: Optional[str])

18. 'get_info_from_the_web_page': Retrieve wanted information from the web page, params: (url: string, task: string, task_guidelines: string)
It should be used only for the clients web page(s), final_url(s) etc.
This command should be used for retrieving the information from clients web page.


Commands starting with 'update' can only be used for updating and commands starting with 'create' can only be used for creating
a new item. Do NOT try to use 'create' for updating or 'update' for creating a new item.
For the actions which we do not support currently, tell the client that you currently do NOT support the wanted action,
but if it is important to the client, you can give advice on how to do it manually within the Google Ads UI.
"""


def _get_function_map(
    user_id: int,
    conv_id: int,
    work_dir: str,
    clients_question_answere_list: List[Tuple[str, Optional[str]]],
) -> Dict[str, Any]:
    def _string_to_list(
        customer_ids: Optional[Union[List[str], str]]
    ) -> Optional[List[str]]:
        if customer_ids is None or isinstance(customer_ids, list):
            return customer_ids

        customer_ids_list = ast.literal_eval(customer_ids)
        if isinstance(customer_ids_list, list):
            return customer_ids_list

        raise TypeError(
            "Error: parameter customer_ids must be a list of strings. e.g. ['1', '5', '10']"
        )

    read_file = get_read_file(working_dir=Path(work_dir))

    function_map = {
        # "get_login_url": lambda: get_login_url(user_id=user_id, conv_id=conv_id),
        "list_accessible_customers": lambda: list_accessible_customers(
            user_id=user_id, conv_id=conv_id
        ),
        "execute_query": lambda customer_ids=None, query=None: execute_query(  # type: ignore
            user_id=user_id,
            conv_id=conv_id,
            customer_ids=_string_to_list(customer_ids),
            query=query,
            work_dir=work_dir,
        ),
        "reply_to_client": reply_to_client_2,
        "ask_client_for_permission": lambda message: ask_client_for_permission(
            clients_question_answere_list=clients_question_answere_list,
            message=message,
        ),
        "read_file": read_file,
        "update_ad_group_ad": lambda customer_id, ad_group_id, ad_id, clients_approval_message, modification_question, cpc_bid_micros=None, status=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdGroupAd(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                ad_id=ad_id,
                cpc_bid_micros=cpc_bid_micros,
                status=status,
                headlines=None,
                descriptions=None,
            ),
            endpoint="/update-ad-group-ad",
        ),
        "create_ad_copy_headline_or_description": lambda customer_id, ad_id, clients_approval_message, modification_question, headline=None, description=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdCopy(
                customer_id=customer_id,
                ad_id=ad_id,
                headline=headline,
                description=description,
                update_existing_headline_index=None,
                update_existing_description_index=None,
                final_url=None,
                final_mobile_urls=None,
                path1=None,
                path2=None,
            ),
            endpoint="/create-update-ad-copy",
        ),
        "update_ad_copy": _get_update_ad_copy(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
        ),
        "update_ad_group": lambda customer_id, ad_group_id, clients_approval_message, modification_question, name=None, cpc_bid_micros=None, status=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdGroup(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                name=name,
                cpc_bid_micros=cpc_bid_micros,
                status=status,
            ),
            endpoint="/update-ad-group",
        ),
        "create_ad_group": lambda customer_id, campaign_id, clients_approval_message, modification_question, name, cpc_bid_micros=None, status=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdGroup(
                customer_id=customer_id,
                campaign_id=campaign_id,
                name=name,
                cpc_bid_micros=cpc_bid_micros,
                status=status,
            ),
            endpoint="/create-ad-group",
        ),
        "update_campaign": lambda customer_id, campaign_id, clients_approval_message, modification_question, name=None, status=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=Campaign(
                customer_id=customer_id,
                campaign_id=campaign_id,
                name=name,
                status=status,
            ),
            endpoint="/update-campaign",
        ),
        "update_ad_group_criterion": lambda customer_id, ad_group_id, criterion_id, modification_question, clients_approval_message, status=None, cpc_bid_micros=None, keyword_match_type=None, keyword_text=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdGroupCriterion(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                criterion_id=criterion_id,
                status=status,
                cpc_bid_micros=cpc_bid_micros,
                keyword_text=keyword_text,
                keyword_match_type=keyword_match_type,
            ),
            endpoint="/update-ad-group-criterion",
        ),
        "update_campaigns_negative_keywords": lambda customer_id, campaign_id, criterion_id, clients_approval_message, modification_question, keyword_match_type=None, keyword_text=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=CampaignCriterion(
                customer_id=customer_id,
                campaign_id=campaign_id,
                criterion_id=criterion_id,
                keyword_text=keyword_text,
                keyword_match_type=keyword_match_type,
            ),
            endpoint="/update-campaigns-negative-keywords",
        ),
        "create_negative_keyword_for_campaign": lambda customer_id, campaign_id, keyword_text, keyword_match_type, clients_approval_message, modification_question, status=None, negative=None, bid_modifier=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=CampaignCriterion(
                customer_id=customer_id,
                campaign_id=campaign_id,
                status=status,
                keyword_match_type=keyword_match_type,
                keyword_text=keyword_text,
                negative=negative,
                bid_modifier=bid_modifier,
            ),
            endpoint="/add-negative-keywords-to-campaign",
        ),
        "create_keyword_for_ad_group": lambda customer_id, ad_group_id, keyword_text, keyword_match_type, clients_approval_message, modification_question, status=None, negative=None, bid_modifier=None, cpc_bid_micros=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdGroupCriterion(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                status=status,
                keyword_match_type=keyword_match_type,
                keyword_text=keyword_text,
                negative=negative,
                bid_modifier=bid_modifier,
                cpc_bid_micros=cpc_bid_micros,
            ),
            endpoint="/add-keywords-to-ad-group",
        ),
        "create_ad_group_ad": lambda customer_id, ad_group_id, clients_approval_message, modification_question, headlines, descriptions, final_url, path1=None, path2=None, status=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdGroupAd(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                status=status,
                headlines=headlines,
                descriptions=descriptions,
                final_url=final_url,
                path1=path1,
                path2=path2,
            ),
            endpoint="/create-ad-group-ad",
        ),
        "create_campaign": lambda customer_id, name, budget_amount_micros, local_currency, clients_approval_message, modification_question, status=None, network_settings_target_google_search=None, network_settings_target_search_network=None, network_settings_target_content_network=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=Campaign(
                customer_id=customer_id,
                name=name,
                budget_amount_micros=budget_amount_micros,
                status=status,
                network_settings_target_google_search=network_settings_target_google_search,
                network_settings_target_search_network=network_settings_target_search_network,
                network_settings_target_content_network=network_settings_target_content_network,
            ),
            endpoint="/create-campaign",
        ),
        "create_geo_targeting_for_campaign": lambda customer_id, campaign_id, clients_approval_message, modification_question, location_names=None, location_ids=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=GeoTargetCriterion(
                customer_id=customer_id,
                campaign_id=campaign_id,
                location_names=location_names,
                location_ids=location_ids,
            ),
            endpoint="/create-geo-targeting-for-campaign",
        ),
        "remove_google_ads_resource": lambda customer_id, resource_id, resource_type, clients_approval_message, modification_question, parent_id=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=RemoveResource(
                customer_id=customer_id,
                resource_id=resource_id,
                resource_type=resource_type,
                parent_id=parent_id,
            ),
            endpoint="/remove-google-ads-resource",
        ),
        "remove_ad_copy_headline_or_description": lambda customer_id, ad_id, clients_approval_message, modification_question, update_existing_headline_index=None, update_existing_description_index=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdCopy(
                customer_id=customer_id,
                ad_id=ad_id,
                headline=None,
                description=None,
                update_existing_headline_index=update_existing_headline_index,
                update_existing_description_index=update_existing_description_index,
                final_url=None,
                final_mobile_urls=None,
            ),
            endpoint="/create-update-ad-copy",
        ),
        "get_info_from_the_web_page": get_info_from_the_web_page,
    }

    return function_map


def _get_update_ad_copy(
    user_id: int,
    conv_id: int,
    clients_question_answere_list: List[Tuple[str, Optional[str]]],
) -> Callable[
    [
        str,
        str,
        str,
        str,
        Optional[str],
        Optional[str],
        Optional[int],
        Optional[int],
        Optional[str],
        Optional[str],
    ],
    Union[Dict[str, Any], str],
]:
    def _update_ad_copy(
        customer_id: str,
        ad_id: str,
        clients_approval_message: str,
        modification_question: str,
        headline: Optional[str] = None,
        description: Optional[str] = None,
        update_existing_headline_index: Optional[int] = None,
        update_existing_description_index: Optional[int] = None,
        final_url: Optional[str] = None,
        final_mobile_urls: Optional[str] = None,
        path1: Optional[str] = None,
        path2: Optional[str] = None,
    ) -> Union[Dict[str, Any], str]:
        if headline and not update_existing_headline_index:
            raise ValueError(
                "If you want to update existing headline, you must specify update_existing_headline_index"
            )
        if description and not update_existing_description_index:
            raise ValueError(
                "If you want to update existing description, you must specify update_existing_description_index"
            )

        return google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answere_list=clients_question_answere_list,
            clients_approval_message=clients_approval_message,
            modification_question=modification_question,
            ad=AdCopy(
                customer_id=customer_id,
                ad_id=ad_id,
                headline=headline,
                description=description,
                update_existing_headline_index=update_existing_headline_index,
                update_existing_description_index=update_existing_description_index,
                final_url=final_url,
                final_mobile_urls=final_mobile_urls,
                path1=path1,
                path2=path2,
            ),
            endpoint="/create-update-ad-copy",
        )

    return _update_ad_copy


def get_create_google_ads_team(
    user_id: int, conv_id: int, working_dir: Path
) -> Callable[[Any], Any]:
    def create_google_ads_team(
        task: str,
        user_id: int = user_id,
        conv_id: int = conv_id,
    ) -> str:
        google_ads_team = GoogleAdsTeam(
            task=task,
            user_id=user_id,
            conv_id=conv_id,
            work_dir=str(working_dir),
        )

        google_ads_team.initiate_chat()

        last_message = google_ads_team.get_last_message()

        return last_message

    return create_google_ads_team


def answer_the_question(answer: str, team_name: str) -> str:
    answer = answer.strip()
    google_ads_team: GoogleAdsTeam = Team.get_team(team_name)  # type: ignore
    google_ads_team.update_clients_question_answere_list(answer)

    google_ads_team.continue_chat(message=answer)

    last_message = google_ads_team.get_last_message()

    return last_message


def get_a_create_google_ads_team(
    user_id: int, conv_id: int, working_dir: Path
) -> Callable[[Any], Any]:
    async def a_create_google_ads_team(
        task: str,
        user_id: int = user_id,
        conv_id: int = conv_id,
    ) -> str:
        google_ads_team = GoogleAdsTeam(
            task=task,
            user_id=user_id,
            conv_id=conv_id,
            work_dir=str(working_dir),
        )

        await google_ads_team.a_initiate_chat()

        last_message = google_ads_team.get_last_message()

        return last_message

    return a_create_google_ads_team


async def a_answer_the_question(answer: str, team_name: str) -> str:
    google_ads_team: GoogleAdsTeam = Team.get_team(team_name)  # type: ignore

    await google_ads_team.a_continue_chat(message=answer)

    last_message = google_ads_team.get_last_message()

    return last_message
