from typing import Any, Callable, Dict, List, Optional, Tuple

from ..tools._brief_creation_team_tools import add_delagate_task, add_get_brief_template
from ..tools._function_configs import (
    get_info_from_the_web_page_config,
    reply_to_client_2_config,
)
from ..tools._functions import get_info_from_the_web_page, reply_to_client_2
from ._google_ads_team import GoogleAdsTeam
from ._shared_prompts import GET_INFO_FROM_THE_WEB_COMMAND, REPLY_TO_CLIENT_COMMAND
from ._team import Team


@Team.register_team("brief_creation_team")
class BriefCreationTeam(Team):
    _functions: List[Dict[str, Any]] = [
        get_info_from_the_web_page_config,
        reply_to_client_2_config,
    ]

    # The roles of the team members, like "admin", "manager", "analyst", etc.
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
including steps and expected outcomes.
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
        work_dir: str = "brief_creation_team",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        self.user_id = user_id
        self.conv_id = conv_id
        self.task = task

        clients_question_answer_list: List[Tuple[str, Optional[str]]] = []
        function_map: Dict[str, Callable[[Any], Any]] = _get_function_map()

        roles: List[Dict[str, str]] = BriefCreationTeam._default_roles

        name = Team.get_user_conv_team_name(
            name_prefix=BriefCreationTeam._get_team_name_prefix(),
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
            clients_question_answer_list=clients_question_answer_list,
        )

        self.llm_config = BriefCreationTeam._get_llm_config(
            seed=seed, temperature=temperature
        )

        self._create_members()

        self._add_tools()

        self._create_initial_message()

    def _add_tools(self) -> None:
        for agent in self.members:
            add_get_brief_template(agent=agent)
            add_delagate_task(agent=agent, user_id=self.user_id, conv_id=self.conv_id)

    @staticmethod
    def _is_termination_msg(x: Dict[str, Optional[str]]) -> bool:
        return GoogleAdsTeam._is_termination_msg(x)

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "brief_creation_team"

    @classmethod
    def _get_avaliable_team_names_and_their_descriptions(cls) -> Dict[str, str]:
        return {
            name: team_class.get_capabilities()
            for name, team_class in Team._team_registry.items()
            if cls != team_class
        }

    @property
    def _task(self) -> str:
        return f"""You are a team in charge of creating customer brief which will be used by one of the teams which you will choose depending on the task.
Here is the current brief/information we have gathered:
{self.task}
"""

    @property
    def _guidelines(self) -> str:
        avaliable_team_names_and_their_descriptions = (
            BriefCreationTeam._get_avaliable_team_names_and_their_descriptions()
        )
        # Create a string from dict
        avaliable_team_names_and_their_descriptions_str = "\n".join(
            [
                f"{name}\n: {description}\n\n"
                for name, description in avaliable_team_names_and_their_descriptions.items()
            ]
        )

        return f"""### Guidelines
1. BEFORE you do ANYTHING, write a detailed step-by-step plan of what you are going to do. For EACH STEP, an APPROPRIATE
TEAM MEMBER should propose a SOLUTION for that step. The TEAM MEMBER PROPOSING the solution should explain the
reasoning behind it, and every OTHER TEAM MEMBER on the team should give a CONSTRUCTIVE OPINION. The TEAM MEMBER
proposing the ORIGINAL SOLUTION should take those considerations into account and adjust the SOLUTION accordingly.
Once the solution is modified, the team should REPEAT the process until the team reaches a CONSENSUS. The team should
then move on to the next step. If the team is unable to reach a consensus, the account manager should make the final
call. If you need additional information, use the 'reply_to_client' command to ask the client for it.


2. Here is a list of teams you can choose from after you determine which one is the most appropriate for the task:
{avaliable_team_names_and_their_descriptions_str}

3. After you have chosen the team, use 'get_brief_template' command to get the template for the brief which you will send to the chosen team.

4. Use 'get_info_from_the_web_page' command to get information from the web page. This information can be used to create the brief.
If you are unable to retrieve the information, use the 'reply_to_client' command to ask the client for the information which you need.

5. When you have gathered all the information, create a detailed brief

6. Finally, use the 'delagate_task' command to send the brief to the chosen team.


Additional information:
When using reply_to_client command, try to use the 'smart_suggestions' parameter to suggest the next steps to the client when ever it is possible.
Do NOT use smart suggestions for open ended questions or questions which require the clients input.

smart suggestions examples:

When you ask the client for some suggestions (e.g. which headline should be added), you should also generate smart suggestions like:
"smart_suggestions": {{
    "suggestions":["Create Google Ads campaign", "increase trafic"],
    "type":"manyOf"
}}
"""

    @property
    def _commands(self) -> str:
        return f"""## Commands
All team members have access to the following command:
1. {REPLY_TO_CLIENT_COMMAND}
"smart_suggestions": {{
    'suggestions': ['Create new campaign', 'Optimize existing campaign'],
    'type': 'oneOf'
}}

2. {GET_INFO_FROM_THE_WEB_COMMAND}
"""


def _get_function_map() -> Dict[str, Any]:
    function_map = {
        "reply_to_client": reply_to_client_2,
        "get_info_from_the_web_page": lambda url, task, task_guidelines: get_info_from_the_web_page(
            url=url, task=task, task_guidelines=task_guidelines
        ),
    }

    return function_map
