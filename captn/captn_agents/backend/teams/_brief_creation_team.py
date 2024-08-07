from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from ..config import Config
from ..toolboxes import Toolbox
from ..tools._brief_creation_team_tools import create_brief_creation_team_toolbox
from ._shared_prompts import GET_INFO_FROM_THE_WEB_COMMAND, REPLY_TO_CLIENT_COMMAND
from ._team import Team


@Team.register_team("brief_creation_team")
class BriefCreationTeam(Team):
    # The roles of the team members, like "admin", "manager", "analyst", etc.
    _default_roles = [
        {
            "Name": "Digitial_marketing_strategist",
            "Description": """You are a Strategist in a digital agency.
Never introduce yourself when writing messages. E.g. do not write 'As a ...'""",
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
    _use_only_team_names: Set[str] = {"default_team", "campaign_creation_team"}

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
        config_list: Optional[List[Dict[str, str]]] = None,
        create_toolbox_func: Callable[
            [int, int, str], Toolbox
        ] = create_brief_creation_team_toolbox,
    ):
        recommended_modifications_and_answer_list: List[
            Tuple[Dict[str, Any], Optional[str]]
        ] = []
        function_map: Dict[str, Callable[[Any], Any]] = {}

        roles: List[Dict[str, str]] = self._default_roles

        super().__init__(
            user_id=user_id,
            conv_id=conv_id,
            roles=roles,
            task=task,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
            use_user_proxy=True,
        )

        if config_list is None:
            config = Config()
            config_list = config.config_list_gpt_4o

        self.llm_config = self._get_llm_config(
            seed=seed, temperature=temperature, config_list=config_list
        )
        self.create_toolbox_func = create_toolbox_func

        self._create_members()

        self._add_tools()

        self._create_initial_message()

    def _add_tools(self) -> None:
        self.toolbox = self.create_toolbox_func(
            self.user_id,
            self.conv_id,
            self.task,
        )
        for agent in self.members:
            if agent != self.user_proxy:
                self.toolbox.add_to_agent(agent, self.user_proxy)

    @classmethod
    def get_avaliable_team_names_and_their_descriptions(
        cls, use_only_team_names: Set[str] = _use_only_team_names
    ) -> Dict[str, str]:
        return {
            name: team_class.get_capabilities()
            for name, team_class in Team._team_registry.items()
            if name in use_only_team_names
        }

    @classmethod
    def construct_team_names_and_descriptions_message(
        cls, use_only_team_names: Set[str] = _use_only_team_names
    ) -> str:
        avaliable_team_names_and_their_descriptions = (
            cls.get_avaliable_team_names_and_their_descriptions(
                use_only_team_names=use_only_team_names
            )
        )
        # Create a string from dict
        avaliable_team_names_and_their_descriptions_str = "\n".join(
            [
                f"{name} - {description}\n\n"
                for name, description in avaliable_team_names_and_their_descriptions.items()
            ]
        )

        return avaliable_team_names_and_their_descriptions_str

    @property
    def _task(self) -> str:
        return f"""You are a team in charge of choosing the appropriate team for the task and creating a brief for the chosen team.
The brief should be clear and concise and should contain all the necessary information for the chosen team to complete the task.
Brief creation is your ONLY task. You are NOT responsible for the following steps after the brief is created.

Here is the current customers brief/information we have gathered for you as a starting point:
{self.task}
"""

    @property
    def _guidelines(self) -> str:
        return f"""### Guidelines
1. Do NOT repeat the content of the previous messages nor repeat your role.
Write SHORT and CLEAR messages. Nobody likes to read long messages. Be concise and to the point, or you will be penalized!


2. The MOST important part of your task is to choose the appropriate team for the task.
ALWAYS ask the client for more information. Here is the FIRST (and probably the only) question you should ask the client:
message:"Do you want to create a new campaign or optimize an existing one?"
"smart_suggestions": {{
    'suggestions': ['Create new campaign', 'Optimize existing campaign'],
    'type': 'oneOf'
}}

and depending on the clients answer, choose the appropriate team.
If you fail to choose the appropriate team, you will be penalized!

3. Here is a list of teams you can choose from after you determine which one is the most appropriate for the task:
{self.construct_team_names_and_descriptions_message()}

4. AFTER the client has told you if he wants to create a new campaign or optimize an existing one and you have chosen the appropriate team for the task,
use 'get_brief_template' command to get the template for the brief which you will need to fill out.
Once you have the template, you are responsible for filling in all the fields. Do NOT ask the client to fill in the information for you, otherwise you will be penalized!


5. Use 'get_info_from_the_web_page' command to get information from the web page. This information MUST be used before creating the brief.
It is MANADATORY to use this command to gather information if the client has provided a link to the web page.
If the client has provided a link to the web page and you do not try to gather information from the web page, you will be penalized!
If you are unable to retrieve ANY information, use the 'reply_to_client' command to ask the client for the information which you need.
Otherwise, focus on creating the brief based on the information which you were able to gather from the web page (ignore the links which you were unable to retrieve information from and don't mention them in the brief!).

6. Initially, use the 'get_info_from_the_web_page' command with the 'max_links_to_click' parameter set to 10.
This will allow you to gather the most information about the clients business.
Once you have gathered the information, if the client wants to focus on a specific subpage(s), use the 'get_info_from_the_web_page' command again with the 'max_links_to_click' parameter set to 4.
This will allow you to gather deeper information about the specific subpage(s) which the client is interested in - this step is VERY important!

7. When you have gathered all the information, create a detailed brief.
Do NOT repeat the content which you have received from the 'get_info_from_the_web_page' command (the content will be injected automatically later on)!
i.e. do NOT mention keywords, headlines and descriptions in the brief which you are constructing!
Do NOT mention to the client that you are creating a brief. This is your internal task and the client does not need to know that.
Do NOT ask the client which information he wants to include in the brief.
i.e. word 'brief' should NOT be mentioned to the client at all!

8. Finally, after you retrieve the information from the web page and create the brief, use the 'delagate_task' command to send the brief to the chosen team.

Guidelines SUMMARY:
- Write a detailed step-by-step plan
- Choose the appropriate team depending on the clients answer
- Get the brief template
- Get information from the web page (do NOT forget this step, it is the MOST IMPORTANT step!)
- Create a detailed brief
- Delegate the task to the chosen team. Use this command ONLY after you have chosen the team, retrieved the information from the web page and created the brief.


## Additional Guidelines
1. When using reply_to_client command, try to use the 'smart_suggestions' parameter to suggest the next steps to the client when ever it is possible.
Do NOT use smart suggestions for open ended questions or questions which require the clients input.

smart suggestions examples:

When you ask the client for some suggestions (e.g. at the beginning when you need to choose the right team), you should also generate smart suggestions like:
"smart_suggestions": {{
    "suggestions":["Create NEW Google Ads campaign", "Optimize EXISTING Google Ads campaign"],
    "type":"manyOf"
}}

The client can see only the messages and the smart suggestions which are sent to him by using the 'reply_to_client' command. He can NOT see the chat history between the team members!!
So make sure you include all the necessary information in the messages and smart suggestions which you are sending by using the 'reply_to_client' command.

2. Use reply_to_client only when you need additional information from the client or when you need an approval for the next step i.e. use it as little as possible.
Do NOT send messages like "We will keep you updated on the progress" because the client is only interested in the final result.
If you know what to do, just do it and do NOT use reply_to_client for informing the client about the progress.

3. There is only 'reply_to_client' command, account_manager_reply_to_client or copywriter_reply_to_client commands do NOT exist.

4. NEVER tell the client which command you are using, he/she does not need to know that. Just ask the question or provide the information.
Do NOT tell the client that your job is to create a brief. The client does not need to know that!

5. Ensure that your responses are formatted using markdown syntax (except for the HTML anchor tags),
as they will be featured on a webpage to ensure a user-friendly presentation.

6. Do not suggest next steps to the client, these steps will be suggested by another team to whom you will delegate the task.
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
Use this command ONLY after you have asked the client if he wants to create a new campaign or optimize an existing one and you have chosen the appropriate team for the task!

4. 'delagate_task': Delegate the task to the selected team. params: (team_name: string, task: string, customers_business_brief: string)

5. NEVER ask the client questions like "Please provide the following information for the customer brief:..."
If you need additional information, use the 'reply_to_client' command and ask the client for the information you need, but ask him one question at a time.
"""
