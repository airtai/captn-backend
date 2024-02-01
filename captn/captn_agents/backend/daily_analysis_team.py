__all__ = ["DailyAnalysisTeam"]

import ast
import json
import unittest
from datetime import datetime
from os import environ
from typing import Any, Callable, Dict, List, Optional, Union

import requests
from pydantic import BaseModel

from ...email.send_email import send_email as send_email_infobip
from ...google_ads.client import (
    execute_query,
    get_user_ids_and_emails,
    list_accessible_customers,
)
from .function_configs import (
    execute_query_config,
    get_daily_report_config,
    get_info_from_the_web_page_config,
    list_accessible_customers_config,
    send_email_config,
)
from .functions import get_info_from_the_web_page, send_email
from .team import Team


class Campaign(BaseModel):
    id: str
    name: str


class AdGroup(BaseModel):
    id: str
    name: str


class Metrics(BaseModel):
    impressions: int
    clicks: int
    interactions: int
    conversions: int
    cost_micros: int


class AdGroupAd(BaseModel):
    ad_id: str
    campaign: Campaign
    ad_group: AdGroup
    metrics: Metrics


class DailyCampaignReport(BaseModel):
    campaign_id: str
    campaign_name: str
    impressions: int
    clicks: int
    interactions: int
    conversions: int
    cost_micros: int
    date: str


class DailyCustomerReport(BaseModel):
    customer_id: str
    daily_ad_group_ads_report: List[AdGroupAd]


class DailyReport(BaseModel):
    daily_customer_reports: List[DailyCustomerReport]


def get_daily_ad_group_ads_report(
    user_id: int, conv_id: int, customer_id: str, date: str
) -> List[AdGroupAd]:
    query = f"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_ad.ad.id, metrics.impressions, metrics.clicks, metrics.interactions, metrics.conversions, metrics.cost_micros FROM ad_group_ad WHERE segments.date = '{date}' AND campaign.status != 'REMOVED' AND ad_group.status != 'REMOVED' AND ad_group_ad.status != 'REMOVED'"  # nosec: [B608]
    query_result = execute_query(
        user_id=user_id, conv_id=conv_id, customer_ids=[customer_id], query=query
    )
    customer_results = ast.literal_eval(query_result)[customer_id]  # type: ignore

    ad_group_ads = []
    for customer_result in customer_results:
        campaign = customer_result["campaign"]
        ad_group = customer_result["adGroup"]
        ad_group_ad = customer_result["adGroupAd"]["ad"]
        metrics = customer_result["metrics"]

        ad_group_ad = AdGroupAd(
            ad_id=customer_result["adGroupAd"]["ad"]["id"],
            campaign=Campaign(
                id=campaign["id"],
                name=campaign["name"],
            ),
            ad_group=AdGroup(
                id=ad_group["id"],
                name=ad_group["name"],
            ),
            metrics=Metrics(
                impressions=metrics["impressions"],
                clicks=metrics["clicks"],
                interactions=metrics["interactions"],
                conversions=metrics["conversions"],
                cost_micros=metrics["costMicros"],
            ),
        )

        ad_group_ads.append(ad_group_ad)
    return ad_group_ads


def get_daily_report_for_customer(
    user_id: int, conv_id: int, customer_id: str, date: str
) -> DailyCustomerReport:
    daily_ad_group_ads_report = get_daily_ad_group_ads_report(
        user_id=user_id, conv_id=conv_id, customer_id=customer_id, date=date
    )

    return DailyCustomerReport(
        customer_id=customer_id,
        daily_ad_group_ads_report=daily_ad_group_ads_report,
    )


def get_daily_report(date: Optional[str] = None, *, user_id: int, conv_id: int) -> str:
    if date is None:
        date = datetime.today().date().isoformat()

    customer_ids: List[str] = list_accessible_customers(
        user_id=user_id, conv_id=conv_id
    )  # type: ignore
    daily_customer_reports = [
        get_daily_report_for_customer(
            user_id=user_id, conv_id=conv_id, customer_id=customer_id, date=date
        )
        for customer_id in customer_ids
    ]
    return DailyReport(daily_customer_reports=daily_customer_reports).model_dump_json(
        indent=2
    )


class DailyAnalysisTeam(Team):
    _functions: List[Dict[str, Any]] = [
        list_accessible_customers_config,
        execute_query_config,
        send_email_config,
        get_info_from_the_web_page_config,
        get_daily_report_config,
    ]

    _shared_system_message = (
        "You have a strong SQL knowladge (and very experienced with PostgresSQL)."
        "When sending an email, include all the findings you have and do NOT try to summarize the finding (too much info is better then too little), it will help the client to understand the problem and make decisions."
        "When analysing, start with simple queries and use more complex ones only if needed"
    )

    _default_roles = [
        {
            "Name": "Google_ads_specialist",
            "Description": f"""{_shared_system_message}
Your job is to suggest and execute the command from the '## Commands' section when you are asked to.""",
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
'send_email'.

Once the initial task given to the team is completed by implementing proposed solutions, you must write down the
accomplished work and execute the 'send_email' command. That message will be forwarded to the client so make
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
        work_dir: str = "daily_analysis",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        function_map: Dict[str, Callable[[Any], Any]] = _get_function_map(
            user_id=user_id,
            conv_id=conv_id,
            work_dir=work_dir,
        )
        roles: List[Dict[str, str]] = DailyAnalysisTeam._default_roles

        name = Team.get_user_conv_team_name(
            name_prefix=DailyAnalysisTeam._get_team_name_prefix(),
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
        )
        self.conv_id = conv_id
        self.task = task
        self.llm_config = DailyAnalysisTeam.get_llm_config(
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
        return "daily_analysis_team"

    @property
    def _task(self) -> str:
        return f"""You are a Google Ads team in charge of running daily analysis for the digital campaigns.
The client has sent you the following task:
\n{self.task}\n\n"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. Before solving the current task given to you, carefully write down all assumptions and discuss them within the team.
2. Once you have all the information you need, you must create a detailed step-by-step plan on how to solve the task.
3. If you receive a login url, forward it to the client by using the 'send_email' function.
If the user isn't logged in, we will NOT be able to access the Google Ads API.
4. Account_manager is responsible for coordinating all the team members and making sure the task is completed on time.
5. Please be concise and clear in your messages. As agents implemented by LLM, save context by making your answers as short as possible.
Don't repeat your self and others and do not use any filler words.
6. Before doing anything else, get the daily report for the campaigns from the previous day by using the 'get_daily_report' command.
Use ONLY the 'get_daily_report' command for retrieving Google Ads metrics (impressions, clicks, conversions, cost_micros etc.).
DO NOT USE execute_query command for retrieving Google Ads metrics! Otherwise you will be penalized!
7. Use the 'execute_query' command for finding the necessary informations about the campaigns, ad groups, ads, keywords etc.
Do NOT use 'execute_query' command for retrieving Google Ads metrics (impressions, clicks, conversions, cost_micros etc.)!

7. Do not give advice on campaign improvement before you fetch all the important information about it by using 'execute_query' command.
8. You can NOT ask the client anything!
9. Never repeat the content from (received) previous messages
10. When referencing the customer ID, return customer.descriptive_name also or use a hyperlink to the Google Ads UI.
11. The client can NOT see your conversation, he only receives the message which you send him by using the
'send_email' command
Here an example on how to use the 'send_email' command:
{
    "daily_analysis": "Below is your daily analysis of your Google Ads campaigns for the date 2024-01-27.
    Campaign - Furniture, Ad Group - Living room, Ad (https://ads.google.com/aw/ads/edit/search?adId=1221212&adGroupIdForAd=44545454)
    Clicks:          124 clicks (+3.12% since last week)
    Conversions:     $6.54 USD  (-1.12% since last week)
    Cost per click:  $0.05 USD  (+12.00% since last week)
    ",
    "proposed_user_actions": ["Remove 'Free' keyword because it is not performing well", "Increase budget from $10/day to $20/day",
    "Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'", "Select some or all of them"]
}

propose_user_actions should NOT be general, but specific.
'proposed_user_actions' BAD EXAMPLES:
"Review the negative keywords in the campaigns to ensure they are not overly restrictive." is NOT specific enough.
"Conduct a keyword analysis to check if the current keywords are too restrictive or irrelevant, which could be leading to low ad visibility" is NOT specific enough.
"Consider enabling paused ad groups and ads if they are relevant and could contribute to campaign performance." is NOT specific enough.

propose_user_actions should never suggest to the client "Analyze" or "Review" something, because that is what we are doing! Based on our analysis, we should suggest to the client what to do!
These suggestions should be specific and actionable.
'proposed_user_actions' GOOD EXAMPLES:
"Remove 'Free' keyword because it is not performing well" is specific enough.
"Remove the headline 'New product' and replace it with 'Very New product' in the 'Adgroup 1'" is specific enough.



12. There is a list of commands which you are able to execute in the 'Commands' section.
You can NOT execute anything else, so do not suggest changes which you can NOT perform.

Do NOT suggest making changes of the following things, otherwise you will be penalized:
- Targeting settings
- Ad Extensions
- Budgeting
- Ad Scheduling

14. You can retrieve negative keywords from the 'campaign_criterion' table (so do not just check the
'ad_group_criterion' table and give up if there are not in that table)
15. Whenever you want to mention the ID of some resource (campaign, ad group, ad, keyword etc.), you must also mention the name of that resource.
e.g. "The campaign with ID 1234567890 and name 'Campaign 1' has ...". Otherwise, the client will not know which resource you are talking about!
16. Your clients are NOT experts and they do not know how to optimize Google Ads. So when you retrieve information about their campaigns, ads, etc.,
suggest which changes could benefit them
17. Do not overwhelm the client with unnecessary information. You must explain why you want to make some changes,
but the client does NOT need to know all the Google Ads details that you have retrieved
18. When using 'execute_query' command, try to use as small query as possible and retrieve only the needed columns
19. Ad Copy headlines can have MAXIMUM 30 characters and descriptions can have MAXIMUM 90 characters, NEVER suggest headlines/descriptions which exceed that length or you will be penalized!
20. Ad rules:
- MINIMUM 3 and MAXIMUM 15 headlines.
- MINIMUM 2 and MAXIMUM 4 descriptions.
It is recomended to use the MAXIMUM number of headlines and descriptions. So if not explicitly told differently, suggest adding 15 headlines and 4 descriptions!
21. Use the 'get_info_from_the_web_page' command to get the summary of the web page. This command can be very useful for figuring out the clients business and what he wants to achieve.
e.g. if you know the final_url, you can use this command to get the summary of the web page and use it for SUGGESTING keywords, headlines, descriptions etc.
You can find most of the information about the clients business from the provided web page(s). So instead of asking the client bunch of questions, ask only for his web page(s)
and try get_info_from_the_web_page.
22. Use 'get_info_from_the_web_page' when you want to retrieve the information about some product, category etc. from the clients web page.
e.g. if you want to retrieve the information about the TVs and you already know the url of the TVs section, you can use this command to get the summary of that web page section.
By doing that, you will be able to recommend MUCH BETTER keywords, headlines, descriptions etc. to the client.
21. Before suggesting any kind of budget, check the default currency from the customer table and convert the budget to that currency.
You can use the following query for retrieving the local currency: SELECT customer.currency_code FROM customer WHERE customer.id = '1212121212'
22. Ensure that your responses are formatted using markdown syntax (except for the '<a href= ...</a>' links),
as they will be featured on a webpage to ensure a user-friendly presentation.
23. Once you have completed daily analysis, you must send a summary of the work done to the client by using the 'send_email' command.

Here is a list of things which you CAN do after the client responds to your email.
So please recommend some of these changes to the client by using the 'proposed_user_actions' parameter in the 'send_email' command:
- update the status (ENABLED / PAUSED) of the campaign, ad group and ad
- create/update/remove headlines and descriptions in the Ad Copy. Make sure to follow the restrictions for the headlines and descriptions (MAXIMUM 30 characters for headlines and MAXIMUM 90 characters for descriptions)
- create/update/remove new keywords
- create/update/remove campaign/ ad group / ad / positive and negative keywords

Do NOT suggest making changes of the following things:
- Targeting settings
- Ad Extensions
- Budget updates (increase/decrease)
- Ad Scheduling

VERY IMPORTANT NOTES:
Make sure that you explicitly tell the client which changes you want, which resource and attribute will be affected.
This rule applies to ALL the commands which make permanent changes (create/update/delete)!!!

Try to figure out as much as possible before sending the email to the client. If you do not know something, ask the team members for help.
- analyse keywords and find out which are (i)relevant for clients business and suggest some create/update/remove actions
- Take a look at ad copy (headlines, descriptions, urls...) and make suggestions on what should be changed (create/update/remove headlines etc.)
- Headlines can have MAXIMUM 30 characters and description can have MAXIMUM 90 characters, NEVER suggest headlines/descriptions which exceed that length!
"""

    @property
    def _commands(self) -> str:
        return """## Commands
Never use functions.function_name(...) because functions module does not exist.
Just suggest calling function 'function_name'.

All team members have access to the following command:
1. send_email: Send email to the client, params: (daily_analysis: string, proposed_user_actions: List[str]])
The 'message' parameter must contain all information useful to the client, because the client does not see your team's conversation (only the information sent in the 'message' parameter)
As we send this message to the client, pay attention to the content inside it. We are a digital agency and the messages we send must be professional.
2. 'get_info_from_the_web_page': Retrieve wanted information from the web page, params: (url: string, task: string, task_guidelines: string)
It should be used only for the clients web page(s), final_url(s) etc.
This command should be used for retrieving the information from clients web page.

ONLY Google ads specialist can suggest following commands:
1. 'list_accessible_customers': List all the customers accessible to the client, no input params: ()
2. 'execute_query': Query Google ads API for the campaign information. Both input parameters are optional. params: (customer_ids: Optional[List[str]], query: Optional[str])
Example of customer_ids parameter: ["12", "44", "111"]
You can use optional parameter 'query' for writing SQL queries.
Do NOT try to JOIN tables, otherwise you will be penalized!
Do NOT try to use multiple tables in the FROM clause (e.g. FROM ad_group_ad, ad_group, campaign), otherwise you will be penalized!

If you want to get negative keywords, use "WHERE campaign_criterion.negative=TRUE" for filtering.
Do NOT retrieve information about the REMOVED resources (campaigns, ad groups, ads...)!
Always add the following condition to your query: "WHERE campaign.status != 'REMOVED' AND ad_group.status != 'REMOVED' AND ad_group_ad.status != 'REMOVED'"
Here is few useful queries:
SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_ad.ad.id FROM ad_group_ad
SELECT ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.negative FROM ad_group_criterion WHERE ad_group_criterion.ad_group = 'customers/2324127278/adGroups/161283342474'
SELECT campaign_criterion.criterion_id, campaign_criterion.type, campaign_criterion.keyword.text, campaign_criterion.negative FROM campaign_criterion WHERE campaign_criterion.campaign = 'customers/2324127278/campaigns/20978334367' AND campaign_criterion.negative=TRUE"

NEVER USE 'JOIN' in your queries, otherwise you will be penalized!

3. 'get_daily_report': Retrieve daily report for the campaigns, params: (date: str)
"""


def _get_function_map(user_id: int, conv_id: int, work_dir: str) -> Dict[str, Any]:
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

    function_map = {
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
        "send_email": lambda daily_analysis, proposed_user_actions: send_email(
            daily_analysis=daily_analysis,
            proposed_user_actions=proposed_user_actions,
        ),
        "get_info_from_the_web_page": get_info_from_the_web_page,
        "get_daily_report": lambda date: get_daily_report(
            date=date, user_id=user_id, conv_id=conv_id
        ),
    }

    return function_map


REACT_APP_API_URL = environ.get("REACT_APP_API_URL", "http://localhost:3001")
REDIRECT_DOMAIN = environ.get("REDIRECT_DOMAIN", "https://captn.ai")


def _get_conv_id_and_send_email(
    user_id: int,
    client_email: str,
    messages: str,
    initial_message_in_chat: str,
    proposed_user_action: List[str],
) -> int:
    data = {
        "userId": user_id,
        "messages": messages,
        "initial_message_in_chat": initial_message_in_chat,
        "email_content": "<html></html>",
        "proposed_user_action": proposed_user_action,
    }
    response = requests.post(
        f"{REACT_APP_API_URL}/captn-daily-analysis-webhook", json=data, timeout=60
    )

    if response.status_code != 200:
        raise ValueError(response.content)

    final_message = "Daily Analysis:\n" + initial_message_in_chat + "\n\n"

    conv_id = response.json()["chatID"]
    proposed_user_actions_paragraph = "Proposed User Actions:\n"
    for i, action in enumerate(proposed_user_action):
        proposed_user_actions_paragraph += f"{i+1}. {action} ({REDIRECT_DOMAIN}/chat/{conv_id}?selected_user_action={i+1})\n"

    final_message += proposed_user_actions_paragraph

    send_email_infobip(
        to_email=client_email,
        from_email="info@airt.ai",
        subject="Captn.ai Daily Analysis",
        body_text=final_message,
    )

    return conv_id  # type: ignore


def execute_daily_analysis(task: Optional[str] = None) -> None:
    print("Starting daily analysis.")
    id_email_dict = json.loads(get_user_ids_and_emails())

    send_only_to_emails = ["robert@airt.ai", "harish@airt.ai"]
    for user_id, email in id_email_dict.items():
        if email not in send_only_to_emails:
            print(
                f"Skipping user_id: {user_id} - email {email} (current implementation)"
            )
            continue
        current_date = datetime.today().strftime("%Y-%m-%d")
        if task is None:
            task = f"""
        Current date is: {current_date}.
        You need compare the ads performance between yesterday and the same day of the previous week (-7 days).
        - Clicks
        - Conversions
        - Cost per click (display in customer local currency)

        Check which ads have the highest cost and which have the highest number of conversions.
        If for some reason thera are no recorded impressions/clicks/interactions/conversions for any of the ads across all campaigns try to identify the reason (bad positive/negative keywords etc).
        At the end of the analysis, you need to suggest the next steps to the client. Usually, the next steps are:
        - pause the ads with the highest cost and the lowest number of conversions.
        - keywords analysis (add negative keywords, add positive keywords, change match type etc).
        - ad copy analysis (change the ad copy, add more ads etc).
            """

        conv_id = 100
        daily_analysis_team = DailyAnalysisTeam(
            task=task,
            user_id=user_id,
            conv_id=conv_id,
        )
        try:
            # REMOVE THE MOCK AFTER DEMO
            with unittest.mock.patch(
                "captn.captn_agents.backend.daily_analysis_team.get_daily_report"
            ) as mock_daily_report:
                return_value1 = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "2324127278",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 402,\n            "clicks": 121,\n            "interactions": 129,\n            "conversions": 15,\n            "cost_micros": 129000\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 53,\n            "clicks": 9,\n            "interactions": 9,\n            "conversions": 2,\n            "cost_micros": 1000\n          }\n        }\n      ]\n    }\n  ]\n}'
                return_value2 = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "2324127278",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 433,\n            "clicks": 129,\n            "interactions": 135,\n            "conversions": 21,\n            "cost_micros": 153000\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 22,\n            "clicks": 3,\n            "interactions": 4,\n            "conversions": 1,\n            "cost_micros": 800\n          }\n        }\n      ]\n    }\n  ]\n}'

                mock_daily_report.side_effect = [return_value1, return_value2]
                # ===============
                daily_analysis_team.initiate_chat()
            last_message = daily_analysis_team.get_last_message(add_prefix=False)

            messages_list = daily_analysis_team.groupchat.messages
            check_if_send_email = messages_list[-2]
            if (
                "function_call" in check_if_send_email
                and check_if_send_email["function_call"]["name"] == "send_email"
            ):
                if len(messages_list) < 3:
                    messages = "[]"
                else:
                    # Don't include the first message (task) and the last message (send_email)
                    messages = json.dumps(messages_list[1:-1])
                last_message_json = ast.literal_eval(last_message)
                _get_conv_id_and_send_email(
                    user_id=user_id,
                    client_email=email,
                    messages=messages,
                    initial_message_in_chat=last_message_json[
                        "initial_message_in_chat"
                    ],
                    proposed_user_action=last_message_json["proposed_user_action"],
                )
            else:
                raise ValueError(
                    f"Send email function is not called for user_id: {user_id} - email {email}!"
                )
        finally:
            Team.pop_team(team_name=daily_analysis_team.name)
    print("Daily analysis completed.")
