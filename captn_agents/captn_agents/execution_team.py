__all__ = [
    "list_files",
    "get_write_to_file",
    "get_read_file",
    "get_execute_command",
    "get_create_execution_team",
    "answer_to_execution_team",
    "get_function_map_execution_team",
]

import ast
import os
import platform
import subprocess  # nosec: B404
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Union

from captn_agents.function_configs import (
    ask_for_additional_info_config,
    execute_command_config,
    list_files_config,
    read_file_config,
    write_to_file_config,
)
from captn_agents.functions import ask_for_additional_info
from captn_agents.team import Team


class ExecutionTeam(Team):
    _functions: List[Dict[str, Any]] = [
        list_files_config,
        write_to_file_config,
        read_file_config,
        ask_for_additional_info_config,
        execute_command_config,
    ]

    def __init__(
        self,
        plan: str,
        roles: List[str],
        function_map: Dict[str, Callable[[Any], Any]],
        work_dir: str,
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        roles_with_descriptions = [
            {"Name": role, "Description": ""} for role in roles
        ]  # TODO: Each role must have a description
        name = ExecutionTeam._get_new_team_name()

        super().__init__(
            roles=roles_with_descriptions,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            name=name,
        )

        self.plan = plan
        self.llm_config = ExecutionTeam.get_llm_config(
            seed=seed, temperature=temperature
        )

        self._create_members()
        self._create_initial_message()

    @classmethod
    def _get_team_name_prefix(cls) -> str:
        return "execution_team"

    @property
    def _task(self) -> str:
        return f"""You are a team dedicated for implementing the following task in Python:
\n{self.plan}"""

    @property
    def _guidelines(self) -> str:
        return """## Guidelines
1. If you have some doubts ask the user for clarification by suggesting ask_for_additional_info command
2. Each code block must be successfuly executed before it is written iside the file
3. Always write the code inside the file by using the write_to_file command
4. Once the code is written inside the file try to execute it
5. For each function and method you write, a test must be written.
A test should be inside another file and it should import at the beginning everything what needs to be tested.
You should execute the test by suggesting execute_command with the parameter "['python', '-m', 'pytest']"
After the test is successfuly executed, write it inside the file (use write_to_file command)
6. Once the whole team agrees that you are finished with the task and everything is tested, write the summary of what has been done
and the names of the files which you have created.
7. The code that you write can NOT expect input from the use (input_string = input('Please enter a string...'))
Finally, your sentence must end with "TERMINATE"
"""

    @property
    def _commands(self) -> str:
        return """## Commands
You have access to the following commands:
1. list_files: List Files in a Directory, params: (directory_path: string)
2. read_file: Read an existing file, params: (filename: string)
3. write_to_file: Write content into the file: (filename: string, content: string)
4. ask_for_additional_info: Ask the user for additional information, params: (question: string)
5. execute_command: A command which will be executed, params: (question: string), e.g. execute_command("['python', '-m', 'pytest']")
"""

    @property
    def _final_section(self) -> str:
        return f"""## Before start
Before you start solving the task, list all the avaliable files in the {self.work_dir} and read the content of the relevant ones


## Task
For your task, you must implement the following functionality in Python:
\n{self.plan}


You should chat with other team members until you have the complete understandig of the task.
Once all the team members have understood the task, start start with the implementation
and respond by suggesting one of the previously defined Commands:
"""


def get_create_execution_team(working_dir: Path) -> Callable[..., Any]:
    def create_execution_team(
        plan: str,
        roles: List[str],
        function_map_execution_team: Dict[str, Callable[..., Any]],
        working_dir: Path = working_dir,
    ) -> str:
        execution_team = ExecutionTeam(
            plan, roles, function_map_execution_team, str(working_dir)
        )

        execution_team.initiate_chat()

        last_message = execution_team.get_last_message()

        return last_message  # type: ignore

    return create_execution_team


def answer_to_execution_team(answer: str, team_name: str) -> str:
    execution_team = Team.get_team(team_name)

    execution_team.continue_chat(message=answer)

    last_message = execution_team.get_last_message()

    return last_message


def list_files(directory_path: str) -> str:
    everything_in_folder = list(Path(directory_path).glob("*"))

    if len(everything_in_folder) == 0:
        return f"{directory_path} is empty."

    return "\n".join([f"{str(file)}\n" for file in everything_in_folder])


def get_write_to_file(working_dir: Path) -> Callable[[str, str], str]:
    def write_to_file(
        filename: str, content: str, working_dir: Path = working_dir
    ) -> str:
        file = working_dir / filename  # type: ignore
        file.write_text(content)
        return f"The file was successfully written inside the {filename}"

    return write_to_file


def get_read_file(working_dir: Path) -> Callable[[str], str]:
    def read_file(filename: str, working_dir: Path = working_dir) -> str:
        file = working_dir / filename  # type: ignore
        return file.read_text()

    return read_file


@contextmanager
def set_cwd(cwd_path: Union[Path, str]) -> Generator[None, None, None]:
    """Set the current working directory for the duration of the context manager.

    Args:
        cwd_path: The path to the new working directory.

    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """
    cwd_path = Path(cwd_path)
    original_cwd = os.getcwd()
    os.chdir(cwd_path)

    try:
        yield
    finally:
        os.chdir(original_cwd)


def get_execute_command(working_dir: Path) -> Callable[[List[str]], str]:
    def execute_command(command: List[str], working_dir: Path = working_dir) -> str:
        if isinstance(command, str):
            command = ast.literal_eval(command)

        with set_cwd(working_dir):
            # nosemgrep: python.lang.security.audit.subprocess-shell-true.subprocess-shell-true
            p = subprocess.run(  # nosec: B602, B603, B607 subprocess call - check for execution of untrusted input.
                command,
                capture_output=True,
                shell=True if platform.system() == "Windows" else False,
            )

            return f"{str(p.stderr.decode('utf-8'))}\n{str(p.stdout.decode('utf-8'))}"

    return execute_command


def get_function_map_execution_team(
    working_dir: Path,
) -> Dict[str, Callable[..., Any]]:
    write_to_file = get_write_to_file(working_dir=working_dir)
    read_file = get_read_file(working_dir=working_dir)
    execute_command = get_execute_command(working_dir=working_dir)

    function_map_execution_team: Dict[str, Callable[..., Any]] = {
        "list_files": list_files,
        "write_to_file": write_to_file,
        "read_file": read_file,
        "ask_for_additional_info": ask_for_additional_info,
        "execute_command": execute_command,
    }

    return function_map_execution_team
