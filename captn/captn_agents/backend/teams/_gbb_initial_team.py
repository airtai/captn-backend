from typing import Callable, Dict, List, Optional

from ..toolboxes import Toolbox
from ..tools._gbb_initial_team_tools import create_gbb_initial_team_toolbox
from ._brief_creation_team import BriefCreationTeam
from ._shared_prompts import REPLY_TO_CLIENT_COMMAND
from ._team import Team

__all__ = ("GBBInitialTeam",)


@Team.register_team("gbb_initial_team")
class GBBInitialTeam(BriefCreationTeam):
    def __init__(
        self,
        *,
        task: str,
        user_id: int,
        conv_id: int,
        work_dir: str = "gbb_initial_team",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        config_list: Optional[List[Dict[str, str]]] = None,
        create_toolbox_func: Callable[
            [int, int, str], Toolbox
        ] = create_gbb_initial_team_toolbox,
    ):
        super().__init__(
            task=task,
            user_id=user_id,
            conv_id=conv_id,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            config_list=config_list,
            create_toolbox_func=create_toolbox_func,
        )

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
Depending on the clients needs, choose the appropriate team.
If you fail to choose the appropriate team, you will be penalized!

3. Here is a list of teams you can choose from after you determine which one is the most appropriate for the task:
{self.construct_team_names_and_descriptions_message(use_only_team_names={"gbb_google_sheets_team", "gbb_page_feed_team"})}

Guidelines SUMMARY:
- Write a detailed step-by-step plan
- Choose the appropriate team depending on the clients answer
- Get the brief template
- Create a detailed brief
- Delegate the task to the chosen team. Use this command ONLY after you have chosen the team and created the brief.


## Additional Guidelines
1. When using reply_to_client command, try to use the 'smart_suggestions' parameter to suggest the next steps to the client when ever it is possible.
Do NOT use smart suggestions for open ended questions or questions which require the clients input.

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
    'suggestions': ['Create new campaign'],
    'type': 'oneOf'
}}

2. 'get_brief_template': Get the TEMPLATE for the customer brief you will need to create. params: (team_name: string)
Use this command ONLY after you have chosen the appropriate team for the task!

3. 'delagate_task': Delegate the task to the selected team. params: (team_name: string, task: string, customers_business_brief: string)

4. NEVER ask the client questions like "Please provide the following information for the customer brief:..."
If you need additional information, use the 'reply_to_client' command and ask the client for the information you need, but ask him one question at a time.
"""
