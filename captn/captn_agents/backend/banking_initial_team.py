from pathlib import Path
from typing import Any, Dict, List

from .banking_team import (
    answer_the_question,
    get_create_banking_credit_calculation_team,
)
from .function_configs import (
    answer_the_question_config,
    create_banking_credit_calculation_team_config,
    reply_to_client_config,
)
from .functions import reply_to_client
from .initial_team import InitialTeam


class BookingInitialTeam(InitialTeam):
    _functions: List[Dict[str, Any]] = [
        create_banking_credit_calculation_team_config,
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
        work_dir: str = "initial_banking",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        human_input_mode: str = "ALWAYS",
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
        )

    @property
    def _task(self) -> str:
        return f"""You are a team in charge of running a bank.
Your current task is:
\n{self.task}"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. If you receive easy questions from the user, you should just reply to them through the User_proxy
2. If you receive a task for calculating the credit, create a banking team by suggesting
'create_banking_credit_calculation_team' command.
3. If you receive banking non relevant question, reply with:
"I am not authorized to answer such questions"
"""

    @property
    def _commands(self) -> str:
        return """## Commands
You have access to the following commands:
1. create_banking_credit_calculation_team: Create banking team dedicated for the credit calculation, params: (task: string)
Always put all relevant information for solving the task inside the 'task' parameter (use relevant information from previous messages)

2. answer_the_question: Answer to the teams question, params: (answer: string, team_name: str)
Use this command only for answering the question which are asked by the banking teams

Only the User_proxy has access to the following commands:
1. reply_to_client: Respond to the client (answer to his task or question for additional information), params: (message: string)
"""

    @property
    def _final_section(self) -> str:
        return f"""## Task
Your TASK description:
\n{self.task}
"""

    def _get_function_map(self, user_id: int, working_dir: Path) -> Dict[str, Any]:
        create_banking_team = get_create_banking_credit_calculation_team(
            user_id=user_id,
            working_dir=working_dir,
        )

        function_map = {
            "create_banking_credit_calculation_team": lambda task: create_banking_team(
                task
            ),
            "answer_the_question": answer_the_question,
            "reply_to_client": reply_to_client,
        }

        return function_map
