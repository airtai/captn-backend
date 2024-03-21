from typing import Any, Callable, Dict, List, Optional, Tuple

from captn.captn_agents.backend.google_ads_team import GoogleAdsTeam
from captn.captn_agents.backend.team import Team

# from ...google_ads.client import (
#     execute_query,
#     get_login_url,
#     google_ads_create_update,
#     list_accessible_customers,
# )
# from .function_configs import (
#     ask_client_for_permission_config,
#     change_google_account_config,
#     create_campaign_config,
#     execute_query_config,
#     get_info_from_the_web_page_config,
#     list_accessible_customers_config,
#     reply_to_client_2_config,
# )
# from .functions import (
#     ask_client_for_permission,
#     get_info_from_the_web_page,
#     reply_to_client_2,
# )


class CampaignCreationTeam(Team):
    _functions: List[Dict[str, Any]] = []

    _default_roles = [
        {
            "Name": "Copywriter",
            "Description": "You are a Copywriter in the digital agency",
        },
        {
            "Name": "Account_manager",
            "Description": """You are an account manager in the digital agency.
You are also SOLELY responsible for communicating with the client.

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
        roles: List[Dict[str, str]] = CampaignCreationTeam._default_roles

        # name = GoogleAdsTeam._get_new_team_name()
        name = Team.get_user_conv_team_name(
            name_prefix=CampaignCreationTeam._get_team_name_prefix(),
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
        return GoogleAdsTeam._is_termination_msg(x)

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "campaign_creation_team"

    @property
    def _task(self) -> str:
        return f"""You are a Google Ads team in charge of CREATING digital campaigns.
The client has sent you the task to create a digital campaign for them. And this is the customer's brief:
\n{self.task}\n\n"""

    @property
    def _guidelines(self) -> str:
        return ""

    @property
    def _commands(self) -> str:
        return ""


def _get_function_map(
    user_id: int,
    conv_id: int,
    work_dir: str,
    clients_question_answere_list: List[Tuple[str, Optional[str]]],
) -> Dict[str, Any]:
    return {}
