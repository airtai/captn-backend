__all__ = [
    "InitialTeam",
]


from pathlib import Path
from typing import Any, Dict, List

from .function_configs import answer_to_team_lead_question_config, create_team_config
from .planning_team import (
    answer_to_team_lead_question,
    create_planning_team,
    get_function_map_planning_team,
)
from .team import Team


class InitialTeam(Team):
    _functions: List[Dict[str, Any]] = [
        answer_to_team_lead_question_config,
        create_team_config,
    ]

    json_encoded_string = '{"Roles": [{"Name": "CMO_GPT", "Description": "a professional digital marketer AI that assists Solopreneurs in growing their businesses by providing world-class expertise in solving marketing problems for SaaS, content products, agencies, and more."}, {"Name": "DESIGNER_GPT", "Description": "a professional designer AI that assists Solopreneurs by creating visuals for their marketing communication"}, {"Name": "COPYRIGTHER_GPT", "Description": "a professional copyrighting AI that assists Solopreneurs in writing texts for their marketing communication"}], "Goals": ["Engage in effective problem-solving, prioritization, planning, and supporting execution to address your marketing needs as your virtual Chief Marketing Officer.", "Provide specific, actionable, and concise advice to help you make informed decisions without the use of platitudes or overly wordy explanations.", "Identify and prioritize quick wins and cost-effective campaigns that maximize results with minimal time and budget investment.", "Proactively take the lead in guiding you and offering suggestions when faced with unclear information or uncertainty to ensure your marketing strategy remains on track.", "Create texts and visuals for campaigns"]}'

    def __init__(
        self,
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
        name = InitialTeam.get_user_conv_team_name(user_id=user_id, conv_id=conv_id)
        if use_async:
            function_map = self._get_function_map_async(
                user_id=user_id, working_dir=Path(work_dir)
            )
        else:
            function_map = self._get_function_map(
                user_id=user_id, working_dir=Path(work_dir)
            )
        super().__init__(
            roles=roles,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            name=name,
            human_input_mode=human_input_mode,
        )

        self.task = task
        self.llm_config = self.__class__.get_llm_config(
            seed=seed, temperature=temperature
        )

        self._create_members()
        self._create_initial_message()

    @classmethod
    def get_user_conv_team_name(cls, user_id: int, conv_id: int) -> str:
        name_prefix = cls._get_team_name_prefix()
        name = f"{name_prefix}_{str(user_id)}_{str(conv_id)}"

        return name

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "initial_team"

    @property
    def _task(self) -> str:
        return """Your task is to devise up to 5 highly effective goals and up to 3 appropriate role-based names (_GPT) for autonomous agents,
ensuring that the goals are optimally aligned with the successful completion of their assigned task. Use this information to
create a JSON-encoded string with parameters to be passed to the 'create_team' function.
"""

    @property
    def _guidelines(self) -> str:
        return f"""## Guidelines
1. After receiving a task from the user, the you should write all assumptions and ask the user for any missing
information and clarification, but one question at the time until everything is clear.

2. Then you should write the task for the ad-hoc team together with their roles and descriptions as JSON.
Example input:
TASK: Help me with marketing my business

Example of a valid JSON-encoded string:

'{InitialTeam.json_encoded_string}'


3. Once you have a JSON-encoded with roles and descriptions, use the 'create_team' command
with the json_as_a_string argument (based on the JSON string from above).

4. The ad-hoc team might have some additional questions. The Product_owner should try to answer them as much as possible using reasonable
assumptions. If not possible, the product owner should write questions before answering.

5. Once you have the answer to the ad-hoc team question, suggest calling the 'answer_to_team_lead_question' command.

6. Once you agree with the user that the his task was successfuly completed, write "TERMINATE"
"""

    @property
    def _commands(self) -> str:
        return """## Commands
You have access to the following commands:
1. create_team: Create an ad-hoc team to solve the problem, params: (json_as_a_string: string)
2. answer_to_team_lead_question: Answer to the team leaders question, params: (answer: string, team_name: str)
"""

    @property
    def _final_section(self) -> str:
        return f"""## Task
Your TASK description:
\n{self.task}
"""

    def _create_members(self) -> None:
        self.members = []
        for role in self.roles:
            is_user_proxy = True if "user" in role["Name"].lower() else False

            self.members.append(
                self._create_member(role["Name"], role["Description"], is_user_proxy)
            )

        self._create_groupchat_and_manager()

    def _get_function_map(self, user_id: int, working_dir: Path) -> Dict[str, Any]:
        function_map_initial_team = {
            "create_team": lambda json_as_a_string: create_planning_team(
                json_as_a_string,
                function_map=get_function_map_planning_team(working_dir),
            ),
            "answer_to_team_lead_question": answer_to_team_lead_question,
        }

        return function_map_initial_team

    def _get_function_map_async(
        self, user_id: int, working_dir: Path
    ) -> Dict[str, Any]:
        raise NotImplementedError()
