__all__ = [
    "create_planning_team",
    "answer_to_team_lead_question",
    "get_function_map_planning_team",
]

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from .execution_team import (
    answer_to_execution_team,
    get_create_execution_team,
    get_function_map_execution_team,
)
from .function_configs import (
    answer_to_execution_team_config,
    ask_for_additional_info_config,
    create_execution_team_config,
)
from .functions import ask_for_additional_info
from .team import Team


class PlanningTeam(Team):
    _functions: List[Dict[str, Any]] = [
        create_execution_team_config,
        ask_for_additional_info_config,
        answer_to_execution_team_config,
    ]

    def __init__(
        self,
        planning_team_input_dict: Dict[str, Any],
        function_map: Dict[str, Callable[[Any], Any]],
        work_dir: str = "planning",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        roles: List[Dict[str, str]] = planning_team_input_dict["Roles"]
        self.goals: List[str] = planning_team_input_dict["Goals"]
        name = PlanningTeam._get_new_team_name()
        super().__init__(
            roles=roles,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            name=name,
        )

        self.llm_config = PlanningTeam._get_llm_config(
            seed=seed, temperature=temperature
        )

        self._create_members()
        self._create_initial_message()

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "planning_team"

    @property
    def _task(self) -> str:
        goals = "\n".join([f"{i+1}. {goal}\n" for i, goal in enumerate(self.goals)])

        return f"""You are a team dedicated for creating an effective plan for each of the following goals:
\n{goals}"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. Go through the list of goals one by one. Discuss about the current goal with other team members, create a detailed plan
for accomplishing the goal and create an execution team which will use the created plan for solving the current goal.
The 'create_execution_team' command requires the `roles` input parameter to be a list
that contains a MINIMUM of two roles. This means that when creating an execution team,
you need to specify at LEAST two roles for the team members.
2. Always create a plan only for the current goal.
3. If the execution team asks a question, first anlyze the question with your team members.
(DO NOT answer the question before consulting with your team).
Once you know the answer to the question, send it to the execution team by suggesting the 'answer_to_execution_team' function.
4. Once the execution team has completed the goal, move to the next one.
5. If you have some doubts ask the user for clarification by suggesting 'ask_for_additional_info' function.
6. Once ALL the goals have been completed, write a short summary about what has been done and finish the message with the word "TERMINATE".
"""

    @property
    def _commands(self) -> str:
        return """## Commands
You have access to the following commands:
1. list_files: Lists Files in a Directory, params: (directory: string)
2. read_file: Read an existing file, params: (filename: string)
3. create_execution_team: Creates the execution team, params: (plan: string, roles: List[string])
4. ask_for_additional_info: Ask the user for additional information, params: (question: string)
5. answer_to_execution_team: Answer the question asked by the execution team, params: (answer: string, team_name: str)
"""

    @property
    def _final_section(self) -> str:
        return """You should chat with other team members until you have the complete understandig of the goal.
Once all the team members have understood the goal, determine exactly one command to use based on the given goal and the progress you have made so far,
and respond by suggesting one of the previously defined commands.
"""


def create_planning_team(
    json_as_a_string: str,
    function_map: Dict[str, Callable[..., Any]],
) -> str:
    roles_and_goals = json.loads(json_as_a_string)

    planning_team = PlanningTeam(roles_and_goals, function_map)

    planning_team.initiate_chat()

    last_message = planning_team.get_last_message()

    return last_message


def answer_to_team_lead_question(answer: str, team_name: str) -> str:
    planning_team: PlanningTeam = Team.get_team(team_name)  # type: ignore

    planning_team.continue_chat(message=answer)

    last_message = planning_team.get_last_message()

    return last_message


def get_function_map_planning_team(working_dir: Path) -> Dict[str, Callable[..., Any]]:
    create_execution_team = get_create_execution_team(working_dir=working_dir)
    function_map_execution_team = get_function_map_execution_team(
        working_dir=working_dir
    )

    function_map_planning_team: Dict[str, Callable[..., Any]] = {
        "create_execution_team": lambda plan, roles: create_execution_team(
            plan, roles, function_map_execution_team
        ),
        "ask_for_additional_info": ask_for_additional_info,
        "answer_to_execution_team": answer_to_execution_team,
    }

    return function_map_planning_team
