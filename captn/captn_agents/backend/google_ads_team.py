__all__ = ["GoogleAdsTeam"]

import ast
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from google_ads.model import (
    AdGroup,
    AdGroupAd,
    AdGroupCriterion,
    Campaign,
    CampaignCriterion,
)

from ...google_ads.client import (
    execute_query,
    google_ads_create_update,
    list_accessible_customers,
)
from .execution_team import get_read_file
from .function_configs import (
    create_negative_keywords_config,
    execute_query_config,
    list_accessible_customers_config,
    read_file_config,
    reply_to_client_2_config,
    update_ad_config,
    update_ad_group_config,
    update_ad_group_criterion_config,
    update_campaign_config,
)
from .functions import reply_to_client_2

# from .google_ads_mock import execute_query, get_login_url, list_accessible_customers
from .team import Team


class GoogleAdsTeam(Team):
    _functions: List[Dict[str, Any]] = [
        # get_login_url_config,
        list_accessible_customers_config,
        execute_query_config,
        reply_to_client_2_config,
        # analyze_query_response_config,
        read_file_config,
        update_ad_config,
        update_ad_group_config,
        update_campaign_config,
        update_ad_group_criterion_config,
        create_negative_keywords_config,
    ]

    _shared_system_message = (
        "You have a strong SQL knowladge (and very experienced with PostgresSQL)."
        "If the client does not explicitly tell you which updates to make, you must double check with him before you make any changes!"
        "When replying to the client, give him a report of the information you retreived / changes that you have made."
        "Send him all the findings you have and do NOT try to summarize the finding (too much info is better then too little), it will help him understand the problem and make decisions."
    )

    _default_roles = [
        {
            "Name": "Google_ads_specialist",
            "Description": f"""{_shared_system_message}
Your job is to suggest and execute the command from the '## Commands' section when you are asked to""",
        },
        {
            "Name": "Copywriter",
            "Description": "You are a Copywriter in the digital agency",
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
'reply_to_client'. Once the permission is granted, please instruct the team to execute the plan. Once the proposed solution
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
        function_map: Dict[str, Callable[[Any], Any]] = _get_function_map(
            user_id=user_id,
            conv_id=conv_id,
            work_dir=work_dir,
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
1. Before solving the current task given to you, carefully write down all assumptions and ask any clarification
questions using the 'reply_to_client' function.
2. Once you have all the information you need, you must create a detailed step-by-step plan on how to solve the task.
3. If you receive login url, forward it to the client by using the 'reply_to_client' function.
4. Account_manager is responsible for coordinating all the team members and making sure the task is completed on time.
5. Please be concise and clear in your messages. As agents implemented by LLM, save context by making your answers as short as possible.
Don't repeat your self and others and do not use any filler words.
6. Before asking for additional information about the Ad campaigns try using 'execute_query' command for finding the neccessary informations.
7. Do not give advice on campaign improvement before you fetch all the important information about it by using 'execute_query' command.
8. Do NOT use 'reply_to_client' command for asking the questions on how to Google Ads API.
Your team is in charge of using the Google Ads API and no one elce does NOT know how to use it.
9. Do NOT ask the client questions about the information which you can get by using Google Ads API (keywords, clikcks etc.)
10. Before making any changes (with budgets, keywords, etc.) ask the client if he approves.
Also, make sure that you explicitly tell the client which changes you want to make.
11. Always suggest one change at the time (do NOT work on multiple things at the same time)
12. Never repeat the content from (received) previous messages
13. When using "execute_query" command, if 'FROM campaign' query filter returns empty responses,
try to use 'FROM ad_group' query filter.
14. The client can NOT see your conversation, he only receives the message which you send him by using the
'reply_to_client' command
15. Whenever you use a 'reply_to_client' command, the your team is on the break until you get the response from the client.
So use this command only when you have a question or some result for the client
16. If it seems like the converation with the client is over (He sends you "Thank you", "ok" etc.),
use 'reply_to_client' command with the following message: "If there are any other tasks or questions, we are ready to assist."
17. Do not overthing for general questions about the Google Ads, the team can discuss the task a bit,
but client demands a quick response. He probably just wants to know what are the best practices.
18. Do not analyze the clients Google Ads data for the general questions about the Google Ads.
19. There is a list of commands which you are able to execute in the 'Commands' section.
You can NOT execute anything else, so do not suggest changes which you can NOT perform.
20. Always double check with the client for which customer/campaign/ad-group/ad the updates needs to be done
21. Here is a list of thing which you can and can NOT do:
- You CAN retrieve the information about your campaigns, ad groups, ads, keywords etc.
- You CAN update the status (ENABLED / PAUSED) of the campaign, ad group and ad
- You CAN create new NEGATIVE keywords (but you can NOT update them)
- You can NOT create/update new (regular) keywords
- You can NOT delete/remove ANYTHING
22. When retreiving keywords, also retieve NEGATIVE keywords (currently they are VERY important)
you can retrieve negative keywords from the 'campaign_criterion' table (so do not just check the
'ad_group_criterion' table and give up if there are not in that table)
23. NEVER suggest making changes which you can NOT perform!
24. When ever you want to make some permenent changes (create/update/delete) you need to ask the client
for the permission! You must tell the client exactly what changes you will make and wait for the permission!
25. If the client does not explicitly tell you which updates to make, you must double check with him
before you make any changes! e.g. if you receive "optimize campaigns" task, you should analyse what can be done
and suggest it to the client. If the client approves your suggestion, only then you can perform the updates.
Also, when you propose suggestion, you need to explain why you want to make these changes (and give the client the report about the information you retreived)
26. Do not try to retrive to much information at once for the clients task, instead of that,
ask the client subquestions and give him the report of the current work and things you have learned about
his Google Ads data
27. If you retrieve IDs of the campaigna/ad groups/ads etc., create clickable link in the markdown format which will create a NEW tab in the Google Ads UI
link example: <a href="https://ads.google.com/aw/campaigns?campaignId=1212121212" target="_blank">1212121212</a>
IMPORTANT: ALWAYS add target="_blank" because the page MUST be opened in the NEW Tab!
28. Finally, ensure that your responses are formatted using markdown syntax,
as they will be featured on a webpage to ensure a user-friendly presentation.


VERY IMPORTANT NOTE:
Currently we are in a demo phase and clients need to see what we are CURRENTLY able to do.
So you do NOT need to suggest optimal Google Ads solutions, just suggest making some changes
which we can do right away.
"""

    @property
    def _commands(self) -> str:
        return """## Commands
Never use functions.function_name(...) because functions module does not exist.
Just suggest calling function 'function_name'.

All team members have access to the following command:
1. reply_to_client: Ask the client for additional information, params: (message: string, is_question: bool, completed: bool)
The 'message' parameter must contain all information useful to the client, because the client does not see your team's conversation (only the information sent in the 'message' parameter)

2. read_file: Read an existing file, params: (filename: string)

ONLY Google ads specialist can suggest following commands:
1. 'list_accessible_customers': List all the customers accessible to the client, no input params: ()
2. 'execute_query': Query Google ads API for the campaign information. Both input parameters are optional. params: (customer_ids: Optional[List[str]], query: Optional[str])
Example of customer_ids parameter: ["12", "44", "111"]
You can use optional parameter 'query' for writing SQL queries. e.g.:
"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name
FROM keyword_view WHERE segments.date DURING LAST_30_DAYS"

Suggestion: keyword_view table is a good place to start digging for info.

If you want to get negative keywords, use "WHERE campaign_criterion.negative=TRUE" for filtering.

3. 'update_ad': Update the Google Ad, params: (customer_id: string, ad_group_id: string, ad_id: string,
client_has_approved: bool, cpc_bid_micros: Optional[int], status: Optional[Literal["ENABLED", "PAUSED"]])
This command can only update ads cpc_bid_micros and status

Before executing the 'update_ad' command, you can easily get the needed parameters customer_id, ad_group_id and ad_id
with the 'execute_query' command and the following 'query':
"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_ad.ad.id FROM ad_group_ad"

4. 'update_ad_group': Update the Google Ads Grooup, params: (customer_id: string, ad_group_id: string, ad_id: Optional[string],
client_has_approved: bool, name: Optional[str], cpc_bid_micros: Optional[int], status: Optional[Literal["ENABLED", "PAUSED"]])
This command can only update ad groups name, cpc_bid_micros and status

5. 'update_campaign': Update the Google Ads Campaign, params: (customer_id: string, campaign_id: string,
client_has_approved: bool, name: Optional[str], status: Optional[Literal["ENABLED", "PAUSED"]])
This command can only update campaigns name and status


6. 'update_ad_group_criterion': Update the Google Ads Group Criterion, params: (customer_id: string, ad_group_id: string,
criterion_id: string, client_has_approved: bool, name: Optional[str], status: Optional[Literal["ENABLED", "PAUSED"]],
cpc_bid_micros: Optional[int])
This command can only update ad group criterion name and status

7. 'create_negative_keywords': Creates Negative keywords (CampaignCriterion), params: (customer_id: string, campaign_id: string,
client_has_approved: bool, keyword_match_type: string, keyword_text: string, negative: Optional[boolean], bid_modifier: Optional[float],
status: Optional[Literal["ENABLED", "PAUSED"]])
This command can ONLY create NEGATIVE keywords


Commands starting with 'update' can only be used for updating and commands starting with 'create' can only be used for creating
a new item. Do NOT try to use 'create' for updating or 'update' for creating a new item.
We do not support any delete/remove commands yet.
For the actions which we do not support currently, tell the client that you currently do NOT support the wanted action,
but if it is important to the client, you can give an advice on how to do it manually within the Google Ads UI.
"""


def analyze_query_response(work_dir: str, file_name: str) -> str:
    #     return """For customer_id = 2324127278, we have the following aggregated statistics:
    # - metrics.clicks: 3731.0
    # - metrics.conversions': 0.0
    # - metrics.impressions': 3660371.0
    # """
    # retval = {'metrics.clicks': 3731.0,
    #     'metrics.conversions': 0.0,
    #     'metrics.impressions': 3660371.0}

    # return retval

    retval = {
        "2324127278": {
            "metrics.clicks": 3731.0,
            "metrics.conversions": 0.0,
            "metrics.impressions": 3660371.0,
        }
    }

    return json.dumps(retval)

    # fixture_path = Path("fixtures/test_query.parquet")
    # assert fixture_path.exists()

    # df = pd.read_parquet()

    # def agregate_by_customer_id(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    #     agg = df.groupby("customer_id")[["metrics.clicks", "metrics.conversions", "metrics.impressions"]].sum()
    #     return agg.to_dict(orient="index")

    # return agregate_by_customer_id(df)


#     path = Path(work_dir) / file_name

#     with open(path) as json_file:
#         data = json.load(json_file)

#     # if len(str(data)) > 5000:
#     summary = "Here is the summary of the executed query:\n"
#     clicks = 23
#     impressions = 9
#     for customer_id in data.keys():
#         summary += f"""customer_id: {customer_id}
# - 'name': 'Website traffic-Search-{customer_id}'
# - 'metrics': 'clicks': {clicks}, 'impressions': {impressions} 'conversions': 0.15
# - 'text': 'fast api tutorial'\n"""
#         clicks += 12
#         impressions += 3
#     return summary

# return data  # type: ignore[no-any-return]


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
        # "analyze_query_response": lambda file_name: analyze_query_response(
        #     work_dir=work_dir, file_name=file_name
        # ),
        "read_file": read_file,
        "update_ad": lambda customer_id, ad_group_id, ad_id, client_has_approved=False, cpc_bid_micros=None, status=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            client_has_approved=client_has_approved,
            ad=AdGroupAd(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                ad_id=ad_id,
                cpc_bid_micros=cpc_bid_micros,
                status=status,
            ),
            endpoint="/update-ad",
        ),
        "update_ad_group": lambda customer_id, ad_group_id, ad_id=None, client_has_approved=False, name=None, cpc_bid_micros=None, status=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            client_has_approved=client_has_approved,
            ad=AdGroup(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                ad_id=ad_id,
                name=name,
                cpc_bid_micros=cpc_bid_micros,
                status=status,
            ),
            endpoint="/update-ad-group",
        ),
        "update_campaign": lambda customer_id, campaign_id, client_has_approved=False, name=None, status=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            client_has_approved=client_has_approved,
            ad=Campaign(
                customer_id=customer_id,
                campaign_id=campaign_id,
                name=name,
                status=status,
            ),
            endpoint="/update-campaign",
        ),
        "update_ad_group_criterion": lambda customer_id, ad_group_id, criterion_id, client_has_approved=False, name=None, status=None, cpc_bid_micros=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            client_has_approved=client_has_approved,
            ad=AdGroupCriterion(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                criterion_id=criterion_id,
                name=name,
                status=status,
                cpc_bid_micros=cpc_bid_micros,
            ),
            endpoint="/update-ad-group-criterion",
        ),
        "create_negative_keywords": lambda customer_id, campaign_id, keyword_text, keyword_match_type, client_has_approved=False, status=None, negative=None, bid_modifier=None: google_ads_create_update(
            user_id=user_id,
            conv_id=conv_id,
            client_has_approved=client_has_approved,
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
    }

    return function_map


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
    google_ads_team: GoogleAdsTeam = Team.get_team(team_name)  # type: ignore

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
