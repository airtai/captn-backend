import shutil
from pathlib import Path
from unittest.mock import Mock

from captn.captn_agents.backend.execution_team import (
    ExecutionTeam,
    get_create_execution_team,
    get_execute_command,
    get_read_file,
    get_write_to_file,
    list_files,
)
from captn.captn_agents.backend.team import Team

from .utils import last_message_is_termination

ask_for_additional_info = Mock()
ask_for_additional_info.side_effect = [
    "I'm not sure",
    "Do what ever you think is the best solution",
] * 5

working_dir = Path("./logs/execution_team").resolve()
write_to_file = get_write_to_file(working_dir=working_dir)
read_file = get_read_file(working_dir=working_dir)
execute_command = get_execute_command(working_dir=working_dir)

function_map = {
    "list_files": list_files,
    "write_to_file": write_to_file,
    "read_file": read_file,
    "ask_for_additional_info": ask_for_additional_info,
    "execute_command": execute_command,
}

plan = "1. Define a function named is_palindrome that takes a string as an argument. \n2. Inside the function, convert the string to lowercase using the lower() method.\n3. Remove all spaces and punctuation from the string. We can use the replace() method to remove spaces and the translate() method along with maketrans() to remove punctuation.\n4. Compare the processed string with its reverse. If they are the same, the string is a palindrome. We can get the reverse of a string in Python using slicing with a step of -1.\n5. Return True if the string is a palindrome and False otherwise.\n6. Include a brief description of what the function does at the beginning of the function.\n7. Document the input parameter, specifying its type and what it represents.\n8. Document the return value, specifying its type and what it represents.\n9. Include comments in the code where necessary to explain complex parts of the code."
roles = ["python_dev_gpt", "doc_writer_gpt", "code_executor"]


def test_inital_message() -> None:
    execution_team = ExecutionTeam(plan=plan, roles=roles, function_map=function_map, work_dir="execution")  # type: ignore

    for key in ["## Guidelines", "## Constraints"]:
        assert key in execution_team.initial_message, key

    expected_commands = """## Commands
You have access to the following commands:
1. list_files: List Files in a Directory, params: (directory_path: string)
2. read_file: Read an existing file, params: (filename: string)
3. write_to_file: Write content into the file: (filename: string, content: string)
4. ask_for_additional_info: Ask the user for additional information, params: (question: string)
5. execute_command: A command which will be executed, params: (question: string), e.g. execute_command("['python', '-m', 'pytest']")
"""
    assert expected_commands in execution_team.initial_message


# @pytest.mark.vcr(
#     filter_headers=["api-key"]
# )
def test_execution_team() -> None:
    filenames = ["__init__.py", "very_important_notes.txt"]
    contents = [
        "",
        "Please make sure that the palindrome code is saved in the my_palindrome.py",
    ]

    if working_dir.exists():
        shutil.rmtree(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in zip(filenames, contents):
        file = (working_dir / filename).absolute()
        write_to_file(str(file), content)

    create_execution_team = get_create_execution_team(working_dir=working_dir)
    create_execution_team(plan, roles, function_map)  # type: ignore
    execution_team = list(Team._teams.values())[-1]

    assert execution_team is not None
    assert last_message_is_termination(execution_team)
