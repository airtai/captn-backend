__all__ = ["GoogleAdsTeam"]

import ast
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ...google_ads.client import (
    execute_query,
    list_accessible_customers,
    update_campaign_or_group_or_ad,
)
from ...model import AdGroupAd
from .execution_team import get_read_file
from .function_configs import (
    ask_for_additional_info_config,
    execute_query_config,
    list_accessible_customers_config,
    read_file_config,
    update_ad_config,
)
from .functions import ask_for_additional_info

# from .google_ads_mock import execute_query, get_login_url, list_accessible_customers
from .team import Team


class GoogleAdsTeam(Team):
    _functions: List[Dict[str, Any]] = [
        # get_login_url_config,
        list_accessible_customers_config,
        execute_query_config,
        ask_for_additional_info_config,
        # analyze_query_response_config,
        read_file_config,
        update_ad_config,
    ]

    _default_roles = [
        {
            "Name": "Google_ads_specialist",
            "Description": "Your job is to suggest and execute the command from the '## Commands' section when you are asked to",
        },
        {
            "Name": "Copywriter",
            "Description": "You are a Copywriter in the digital agency",
        },
        {
            "Name": "Digital_strategist",
            "Description": "You are a digital strategist in the digital agency",
        },
        {
            "Name": "Account_manager",
            "Description": """You are an account manager in the digital agency. Your job is to coordinate all the team members
and make sure the task is completed on time. You are also SOLELY responsible for communicating with the client.

Based on the initial task, a number of proposed solutions will be suggested by the team. You must ask the team to write a detailed plan
including steps and expected outcomes. Once the plan is ready, you must summarize it and ask the user for permission to execute it using
'ask_for_additional_info'. Once the permission is granted, please instruct the team to execute the plan. Once the proposed solution
is executed, you must write a short summary of accomplished work and forward it to the user using 'ask_for_additional_info'.

Once the initial task given to the team is completed by implementing proposed solutions, you must write a short summary of
accomplished work and finish the message with the word "TERMINATE". That message will be forwarded to the client and make
sure it is understandable by non-experts. DO NOT allow the team to finish with actually implementing the proposed solution outlined
in the plan.
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

        name = GoogleAdsTeam._get_new_team_name()

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

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "google_ads_team"

    @property
    def _task(self) -> str:
        return f"""You are a Google Ads team in charge of running digital campaigns.
Your current task is:
\n{self.task}\n\n"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. Before solving the current task given to you, carefully write down all assumptions and ask any clarification
questions using the 'ask_for_additional_info' function.
2. Once you have all the information you need, you must create a detailed step-by-step plan on how to solve the task.
3. If you receive login url, forward it to the user by using the 'ask_for_additional_info' function.
4. Account_manager is responsible for coordinating all the team members and making sure the task is completed on time.
5. Please be concise and clear in your messages. As agents implemented by LLM, save context by making your answers as short as possible.
Don't repeat your self and others and do not use any filler words.
6. Before asking for additional information about the Ad campaigns try using 'execute_query' command for finding the neccessary informations.
7. Do not give advice on campaign improvement before you fetch all the important information about it by using 'execute_query' command.
8. Do NOT use 'ask_for_additional_info' command for asking the questions on how to Google Ads API.
Your team is in charge of using the Google Ads API and no one elce does NOT know how to use it.
9. Do NOT ask the user questions about the information which you can get by using Google Ads API (keywords, clikcks etc.)
10. Before making any changes (with budgets, keywords, etc.) ask the user if he approves.
Also, make sure that you explicitly tell the user which changes you want to make.
11. Always suggest one change at the time (do NOT work on multiple things at the same time)
"""

    @property
    def _commands(self) -> str:
        return """## Commands
Never use functions.function_name(...) because functions module does not exist.
Just suggest calling function 'function_name'.

All team members have access to the following command:
1. ask_for_additional_info: Ask the user for additional information, params: (question: string)
2. read_file: Read an existing file, params: (filename: string)

ONLY Google ads specialist can suggest following commands:
1. 'list_accessible_customers': List all the customers accessible to the user, no input params: ()
2. 'execute_query': Query Google ads API for the campaign information. Both input parameters are optional. params: (customer_ids: Optional[List[str]], query: Optional[str])
Example of customer_ids parameter: ["12", "44", "111"]
You can use optional parameter 'query' for writing SQL queries. e.g.:
"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name
FROM keyword_view WHERE segments.date DURING LAST_30_DAYS"

3. 'update_ad': Update the Google Ad, params: (customer_id: string, ad_group_id: string, ad_id: string,
name: Optional[str], cpc_bid_micros: Optional[int], status: Optional[Literal["ENABLED", "PAUSED"]])

Before executing the 'update_ad' command, you can easily get the needed parameters customer_id, ad_group_id and ad_id
with the 'execute_query' command and the following 'query':
"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_ad.ad.id FROM ad_group_ad"

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
        "ask_for_additional_info": ask_for_additional_info,
        # "analyze_query_response": lambda file_name: analyze_query_response(
        #     work_dir=work_dir, file_name=file_name
        # ),
        "read_file": read_file,
        "update_ad": lambda customer_id, ad_group_id, ad_id, name=None, cpc_bid_micros=None, status=None: update_campaign_or_group_or_ad(
            user_id=user_id,
            conv_id=conv_id,
            ad=AdGroupAd(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                ad_id=ad_id,
                name=name,
                cpc_bid_micros=cpc_bid_micros,
                status=status,
            ),
            endpoint="/update-ad",
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
