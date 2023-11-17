from pathlib import Path
from typing import Any, Dict, List

from .function_configs import (
    answer_the_question_config,
    create_google_ads_team_config,
    reply_to_client_config,
)
from .functions import reply_to_client
from .google_ads_team import (
    a_answer_the_question,
    answer_the_question,
    get_a_create_google_ads_team,
    get_create_google_ads_team,
)
from .initial_team import InitialTeam


class CaptnInitialTeam(InitialTeam):
    _functions: List[Dict[str, Any]] = [
        create_google_ads_team_config,
        answer_the_question_config,
        reply_to_client_config,
    ]

    def __init__(
        self,
        *,
        user_id: int,
        conv_id: int,
        task: str,
        roles: List[Dict[str, str]],
        work_dir: str = "initial",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        human_input_mode: str = "ALWAYS",
        use_async: bool = False,
    ):
        super().__init__(
            user_id=user_id,
            conv_id=conv_id,
            task=task,
            roles=roles,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            human_input_mode=human_input_mode,
            use_async=use_async,
        )

    @property
    def _task(self) -> str:
        return f"""You are a team in charge of running digital campaigns.
Your current task is:
\n{self.task}"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
### Basic Guidelines
Here are few mandatory guidelines which you mus ALWAYS follow:
1. If you receive a simple question/message from the client, try to answer it quickly (do NOT create google ads team for these messages)     
2. Do NOT try answer to questions non related with Digital marketing, just reply: "I am a digital marketing assistant, I cannot answer questions on other topics" 

### Google Ads Guidelines
3. If Google Ads team sends you a login link, the link must be forwarded to the user (always use Markdown when returning url links)
4. Once the user is logged in, you need to suggest the 'answer_the_question' command and answer with:
'User has logged in, please continue'. This will enable the Google Ads team to continue with the task.
"""

    @property
    def _commands(self) -> str:
        return """## Commands
You have access to the following commands:
1. create_google_ads_team: Create Google Ads team for solving the task, params: (task: string)
2. answer_the_question: Answer to the teams question, params: (answer: string, team_name: str)

Only the User_proxy has access to the following commands:
1. reply_to_client: Respond to the client (answer to his task or question for additional information), params: (message: string)
"""

    @property
    def _final_section(self) -> str:
        return f"""## Task
Your TASK description:
\n{self.task}
"""

    def _get_function_map(
        self, user_id: int, conv_id: int, working_dir: Path
    ) -> Dict[str, Any]:
        create_google_ads_team = get_create_google_ads_team(
            user_id=user_id,
            conv_id=conv_id,
            working_dir=working_dir,
        )

        function_map = {
            "create_google_ads_team": lambda task: create_google_ads_team(task),
            "answer_the_question": answer_the_question,
            "reply_to_client": reply_to_client,
        }

        return function_map

    def _get_function_map_async(
        self, user_id: int, conv_id: int, working_dir: Path
    ) -> Dict[str, Any]:
        a_create_google_ads_team = get_a_create_google_ads_team(
            user_id=user_id,
            conv_id=conv_id,
            working_dir=working_dir,
        )

        function_map = {
            "create_google_ads_team": a_create_google_ads_team,
            "answer_the_question": a_answer_the_question,
        }

        return function_map
