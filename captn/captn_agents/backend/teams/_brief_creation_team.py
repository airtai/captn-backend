from typing import Any, Callable, Dict, List, Optional, Tuple

from captn.captn_agents.backend.config import Config

from ..tools._brief_creation_team_tools import create_brief_creation_team_toolbox
from ..tools._functions import get_info_from_the_web_page, reply_to_client_2
from ._google_ads_team import GoogleAdsTeam
from ._shared_prompts import GET_INFO_FROM_THE_WEB_COMMAND, REPLY_TO_CLIENT_COMMAND
from ._team import Team


@Team.register_team("brief_creation_team")
class BriefCreationTeam(Team):
    # The roles of the team members, like "admin", "manager", "analyst", etc.
    _default_roles = [
        {
            "Name": "Copywriter",
            "Description": """You are a Copywriter in the digital agency.
Never introduce yourself when writing messages. E.g. do not write 'As a copywriter'""",
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
Never introduce yourself when writing messages. E.g. do not write 'As an account manager'
""",
        },
    ]

    _functions: Optional[List[Dict[str, Any]]] = []

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
        function_map: Dict[str, Callable[[Any], Any]] = {}

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

        config = Config()
        self.llm_config = BriefCreationTeam._get_llm_config(
            seed=seed, temperature=temperature, config_list=config.config_list_gpt_3_5
        )

        self._create_members()

        self._add_tools()

        self._create_initial_message()

    def _add_tools(self) -> None:
        self.toolbox = create_brief_creation_team_toolbox(
            user_id=self.user_id,
            conv_id=self.conv_id,
        )
        for agent in self.members:
            self.toolbox.add_to_agent(agent, agent)

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
Create a detailed brief based on the task provided by the client. The brief should be clear and concise and should contain all the necessary information for the chosen team to complete the task.
Brief creation is your ONLY task. You are NOT responsible for the following steps after the brief is created.

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
1. Do NOT repeat the content of the previous messages nor repeat your role.
Write short and clear messages. Nobody likes to read long messages. Be concise and to the point.

2. Here is a list of teams you can choose from after you determine which one is the most appropriate for the task:
{avaliable_team_names_and_their_descriptions_str}

3. After you have chosen the team, use 'get_brief_template' command to get the template for the brief which you will send to the chosen team.

4. Use 'get_info_from_the_web_page' command to get information from the web page. This information MUST be used before creating the brief.
It is MANADATORY to use this command to gather information if the client has provided a link to the web page.
If the client has provided a link to the web page and you do not try to gather information from the web page, you will be penalized!
If you are unable to retrieve the information, use the 'reply_to_client' command to ask the client for the information which you need.

5. When you have gathered all the information, create a detailed brief.
Team members should discuss and agree on the content of the brief before sending it to the chosen team.

6. Finally, after you retrieve the information from the web page and create the brief, use the 'delagate_task' command to send the brief to the chosen team.

Guidelines SUMMARY:
- Write a detailed step-by-step plan
- Choose the appropriate team
- Get the brief template
- Get information from the web page (do NOT forget this step, it is the MOST IMPORTANT step!)
- Create a detailed brief
- Delagate the task to the chosen team. Use this command ONLY after you have retrieved the information from the web page and created the brief.


## Additional Guidelines
1. When using reply_to_client command, try to use the 'smart_suggestions' parameter to suggest the next steps to the client when ever it is possible.
Do NOT use smart suggestions for open ended questions or questions which require the clients input.

smart suggestions examples:

When you ask the client for some suggestions (e.g. which headline should be added), you should also generate smart suggestions like:
"smart_suggestions": {{
    "suggestions":["Create Google Ads campaign", "increase trafic"],
    "type":"manyOf"
}}

The client can see only the messages and the smart suggestions which are sent to him by using the 'reply_to_client' command. He can NOT see the chat history between the team members!!
So make sure you include all the necessary information in the messages and smart suggestions which you are sending by using the 'reply_to_client' command.

2. Use reply_to_client only when you need additional information from the client or when you need an approval for the next step i.e. use it as little as possible.
Do NOT send messages like "We will keep you updated on the progress" because the client is only interested in the final result.
If you know what to do, just do it and do NOT use reply_to_client for informing the client about the progress.

3. There is only 'reply_to_client' command, account_manager_reply_to_client or copywriter_reply_to_client commands do NOT exist.

3. NEVER tell the client which command you are using, he/she does not need to know that. Just ask the question or provide the information.
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

3. 'get_brief_template': Get the TEMPLATE for the customer brief you will need to create. params: (team_name: string)
Use this command ONLY one time after you have chosen the team.

4. 'delagate_task': Delagate the task to the selected team. params: (team_name: string, task: string, customers_brief: string, summary_from_web_page: string)
summary_from_web_page contains the summary retrieved from the clients web page by using the 'get_info_from_the_web_page' command.
"""


def _get_function_map() -> Dict[str, Any]:
    function_map = {
        "reply_to_client": reply_to_client_2,
        "get_info_from_the_web_page": lambda url,
        task,
        task_guidelines: get_info_from_the_web_page(
            url=url, task=task, task_guidelines=task_guidelines
        ),
    }

    return function_map
