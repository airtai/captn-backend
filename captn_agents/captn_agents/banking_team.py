__all__ = ["BankingTeam"]

from pathlib import Path
from typing import Any, Callable, Dict, List

from captn_agents.function_configs import (
    ask_for_additional_info_config,
    calculate_credit_config,
)
from captn_agents.functions import ask_for_additional_info
from captn_agents.team import Team


class BankingTeam(Team):
    _functions: List[Dict[str, Any]] = [
        ask_for_additional_info_config,
        calculate_credit_config,
    ]

    _default_roles = [
        {
            "Name": "Personal_banking_manager",
            "Description": "You are a personal banking manager",
        },
        # {
        #     "Name": "Banking_associate",
        #     "Description": "You are a banking associate",
        # },
        {
            "Name": "Account_manager",
            "Description": """You are an account manager in the bank. Your job is to coordinate all the team members
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
        work_dir: str = "banking",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        function_map: Dict[str, Callable[[Any], Any]] = _get_function_map(
            user_id=user_id
        )
        roles: List[Dict[str, str]] = BankingTeam._default_roles

        name = BankingTeam._get_new_team_name()

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
        self.llm_config = BankingTeam.get_llm_config(seed=seed, temperature=temperature)

        self._create_members()
        self._create_initial_message()

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "banking_team"

    @property
    def _task(self) -> str:
        return f"""You are a Banking team in charge of calculating the credit.
Your current task is:
\n{self.task}"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. You are a Banking team in charge of calculating the credit.
2. Before solving the current task given to you, carefully write down all assumptions and ask any clarification
questions using the 'ask_for_additional_info' function.
3. Please be concise and clear in your messages. As agents implemented by LLM, save context by making your answers as short as possible.
Don't repeat your self and others and do not use any filler words.
"""

    @property
    def _commands(self) -> str:
        return """## Commands
Never use functions.function_name(...) because functions module does not exist.
Just suggest calling function 'function_name'.

All team members have access to the following command:
1. 'ask_for_additional_info': Ask the user for additional information, params: (question: string)
2. 'calculate_credit': Calculate the credit, params: (credit_duration: string, amount_euro: string)
"""


def _get_function_map(user_id: int) -> Dict[str, Any]:
    calculate_credit_mock = """
Monthly annuity
EUR 716.58
Type of interest rate
Fixed
Interest rate
3.69%
Effective interest rate
3.75%
Interest
EUR 50,687.74
Total repayment amount
EUR 172,187.74
TERMINATE
"""

    function_map = {
        "ask_for_additional_info": ask_for_additional_info,
        "calculate_credit": lambda credit_duration, amount_euro: calculate_credit_mock,
    }

    return function_map


def get_create_banking_credit_calculation_team(
    user_id: int, working_dir: Path
) -> Callable[[Any], Any]:
    def create_banking_credit_calculation_team(
        task: str,
        user_id: int = user_id,
    ) -> str:
        banking_team = BankingTeam(
            task=task,
            user_id=user_id,
            work_dir=str(working_dir),
        )

        banking_team.initiate_chat()

        last_message = banking_team.get_last_message()

        return last_message

    return create_banking_credit_calculation_team


def answer_the_question(answer: str, team_name: str) -> str:
    banking_team: BankingTeam = Team.get_team(team_name)  # type: ignore

    banking_team.continue_chat(message=answer)

    last_message = banking_team.get_last_message()

    return last_message
