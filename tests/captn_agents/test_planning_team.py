import json
from unittest.mock import Mock

from captn_agents.planning_team import (
    PlanningTeam,
    create_planning_team,
)
from captn_agents.team import Team

from .utils import last_message_is_termination

ask_for_additional_info = Mock()
ask_for_additional_info.side_effect = [
    "I'm not sure",
    "Do what ever you think is the best solution",
] * 5

create_execution_team = Mock()
create_execution_team.side_effect = [
    "Should I log the errors?",
    "Completed, proceed with the next goal",
] * 5

answer_to_execution_team = Mock()
answer_to_execution_team.side_effect = [
    "Do I need a kafka broker?",
    "What is the email of our client?",
    "whuch libraries should I use?",
    "Completed, proceed with the next goal",
] * 5

function_map = {
    "create_execution_team": create_execution_team,
    "ask_for_additional_info": ask_for_additional_info,
    "answer_to_execution_team": answer_to_execution_team,
}

planning_team_input = '{"Roles": [{"Name": "PYTHON_DEV_GPT", "Description": "a professional Python developer AI that assists in writing Python scripts and functions"}, {"Name": "QA_GPT", "Description": "a professional Quality Assurance AI that assists in testing Python scripts and functions for bugs and errors"}, {"Name": "DOC_WRITER_GPT", "Description": "a professional Documentation Writer AI that assists in writing clear and concise documentation for Python scripts and functions"}], "Goals": ["Write a Python function that checks if a string is a palindrome, ignoring spaces, punctuation, and capitalization.", "Test the function thoroughly to ensure it works as expected.", "Write clear and concise documentation for the function."]}'


def test_inital_message() -> None:
    planning_team = PlanningTeam(json.loads(planning_team_input), function_map)  # type: ignore

    for key in ["## Guidelines", "## Constraints"]:
        assert key in planning_team.initial_message, key

    expected_commands = """## Commands
You have access to the following commands:
1. list_files: Lists Files in a Directory, params: (directory: string)
2. read_file: Read an existing file, params: (filename: string)
3. create_execution_team: Creates the execution team, params: (plan: string, roles: List[string])
4. ask_for_additional_info: Ask the user for additional information, params: (question: string)
5. answer_to_execution_team: Answer the question asked by the execution team, params: (answer: string, team_name: str)
"""
    assert expected_commands in planning_team.initial_message


# @pytest.mark.vcr('../fixtures/vcr_cassettes/test_planning_team.yaml', filter_query_parameters=["api-key"])
# @pytest.mark.vcr(
#     filter_headers=["api-key"]
# )
def test_planning_team() -> None:
    create_planning_team(planning_team_input, function_map)  # type: ignore

    planning_team = list(Team._teams.values())[-1]

    assert planning_team is not None
    assert last_message_is_termination(planning_team)
