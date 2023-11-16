__all__ = ["GoogleAdsTeam"]

import ast
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

from ...google_ads.client import (
    get_login_url,
    list_accessible_customers,
)
from ...google_ads.client import (
    search as execute_query,
)
from .function_configs import (
    ask_for_additional_info_config,
    execute_query_config,
    get_login_url_config,
    list_accessible_customers_config,
)
from .functions import ask_for_additional_info

# from .google_ads_mock import execute_query, get_login_url, list_accessible_customers
from .team import Team


class GoogleAdsTeam(Team):
    _functions: List[Dict[str, Any]] = [
        get_login_url_config,
        list_accessible_customers_config,
        execute_query_config,
        ask_for_additional_info_config,
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
        work_dir: str = "google_ads",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        function_map: Dict[str, Callable[[Any], Any]] = _get_function_map(
            user_id=user_id
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
\n{self.task}"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. You are a Google Ads team in charge of running digital campaigns.
2. Before solving the current task given to you, carefully write down all assumptions and ask any clarification
questions using the 'ask_for_additional_info' function.
3. Once you have all the information you need, you must create a detailed step-by-step plan on how to solve the task.
4. To use Google ads api, you need to ask user to login using the URL retrieved by calling the 'get_login_url' function
 first and then passing the url to the user using 'ask_for_additional_info' function.
5. Account_manager is responsible for coordinating all the team members and making sure the task is completed on time.
6. Please be concise and clear in your messages. As agents implemented by LLM, save context by making your answers as short as possible.
Don't repeat your self and others and do not use any filler words.
7. Before asking for additional information about the Ad campaigns try using 'execute_query' command for finding the neccessary informations.
"""

    @property
    def _commands(self) -> str:
        return """## Commands
Never use functions.function_name(...) because functions module does not exist.
Just suggest calling function 'function_name'.

All team members have access to the following command:
1. ask_for_additional_info: Ask the user for additional information, params: (question: string)

ONLY Google ads specialist can suggest following commands:
1. 'get_login_url': Get the users login url, no input params: ()
2. 'list_accessible_customers': List all the customers accessible to the user, no input params: ()
3. 'execute_query': Query Google ads API for the campaign information. Both input parameters are optional. params: (customer_ids: Optional[List[str]], query: Optional[str])
Example of customer_ids parameter: ["12", "44", "111"]
You can use optional parameter 'query' for writing SQL queries. e.g.:
"SELECT campaign.id, campaign.name, ad_group.id, ad_group.name
FROM keyword_view WHERE segments.date DURING LAST_7_DAYS"
"""


def _get_function_map(user_id: int) -> Dict[str, Any]:
    def _string_to_list(customer_ids: Union[List[str], str]) -> List[str]:
        if isinstance(customer_ids, list):
            return customer_ids

        customer_ids_list = ast.literal_eval(customer_ids)
        if isinstance(customer_ids_list, list):
            return customer_ids_list

        raise TypeError(
            "Error: parameter customer_ids must be a list of strings. e.g. ['1', '5', '10']"
        )

    function_map = {
        "get_login_url": lambda: get_login_url(user_id=user_id),
        "list_accessible_customers": lambda: list_accessible_customers(user_id=user_id),
        "execute_query": lambda customer_ids=None, query=None: execute_query(  # type: ignore
            user_id, _string_to_list(customer_ids), query
        ),
        "ask_for_additional_info": ask_for_additional_info,
    }

    return function_map


def get_create_google_ads_team(user_id: int, working_dir: Path) -> Callable[[Any], Any]:
    def create_google_ads_team(
        task: str,
        user_id: int = user_id,
    ) -> str:
        google_ads_team = GoogleAdsTeam(
            task=task,
            user_id=user_id,
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
    user_id: int, working_dir: Path
) -> Callable[[Any], Any]:
    async def a_create_google_ads_team(
        task: str,
        user_id: int = user_id,
    ) -> str:
        google_ads_team = GoogleAdsTeam(
            task=task,
            user_id=user_id,
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
