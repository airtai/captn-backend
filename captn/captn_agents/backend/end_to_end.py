__all__ = [
    "start_conversation",
    "continue_conversation",
]

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .banking_initial_team import BookingInitialTeam
from .captn_initial_team import CaptnInitialTeam
from .initial_team import InitialTeam
from .team import Team

initial_team_roles_never = [
    {
        "Name": "User_proxy",
        "Description": "Your job is to comunicate with the Account_manager, do NOT suggest any code or execute the code by yourself",
    },
    {
        "Name": "Account_manager",
        "Description": "You are an account manager in digital marketing agency.",
    },
]

captn_initial_team_roles_never = [
    {
        "Name": "User_proxy",
        "Description": """You are a user with a task for the Account_manager, do NOT suggest any code or execute the code by yourself.
If you receive a login link, just reply with: 'I am logged in now'""",
    },
    {
        "Name": "Account_manager",
        "Description": "You are an account manager in the digital agency. Your job is to communicate with the User_proxy.",
    },
]

captn_initial_team_roles_always = [
    {
        "Name": "User_proxy",
        "Description": """You are a proxy between the real user and the Account_manager. When you want to ask the client a question or return to him a summary of what has been done,
use the 'reply_to_client' command. The message which will be sent to the user must ALWAYS be written in CROATIAN language.""",
    },
    {
        "Name": "Account_manager",
        "Description": "You are an account manager in the digital agency. Your job is to communicate with the User_proxy.",
    },
]

banking_initial_team_roles_never = [
    {
        "Name": "User_proxy",
        "Description": """You are a proxy between the client and the Account_manager. do NOT suggest any code or execute the code by yourself.""",
    },
    {
        "Name": "Account_manager",
        "Description": "You are an account manager in the bank.",
    },
]

banking_initial_team_roles_always = [
    {
        "Name": "User_proxy",
        "Description": """You are a proxy between client and the Account_manager. When you want to ask the client a question or return to him a summary of what has been done,
    use the 'reply_to_client' command. The message which will be sent to the user must ALWAYS be written in CROATIAN language.""",
    },
    {
        "Name": "Account_manager",
        "Description": "You are an account manager in the bank.",
    },
]


roles_dictionary = {
    "initial_team": {
        "human_input_mode": {"NEVER": initial_team_roles_never, "ALWAYS": []},
        "class": InitialTeam,
    },
    "captn_initial_team": {
        "human_input_mode": {
            "NEVER": captn_initial_team_roles_always,  # captn_initial_team_roles_never,
            "ALWAYS": captn_initial_team_roles_always,
        },
        "class": CaptnInitialTeam,
    },
    "banking_initial_team": {
        "human_input_mode": {
            "NEVER": banking_initial_team_roles_always,  # banking_initial_team_roles_never,
            "ALWAYS": banking_initial_team_roles_always,
        },
        "class": BookingInitialTeam,
    },
}


def _get_initial_team(
    user_id: int,
    conv_id: int,
    root_dir: Path,
    *,
    task: str,
    roles: Optional[List[Dict[str, str]]],
    max_round: int,
    seed: int,
    temperature: float,
    human_input_mode: str,
    class_name: str,
    use_async: bool = False,
) -> Tuple[Optional[Team], str, bool]:
    working_dir: Path = root_dir / f"{user_id=}" / f"{conv_id=}"
    working_dir.mkdir(parents=True, exist_ok=True)

    initial_team_class = roles_dictionary[class_name]["class"]
    if roles is None:
        roles = roles_dictionary[class_name]["human_input_mode"][human_input_mode]  # type: ignore

    initial_team = None
    try:
        team_name = InitialTeam.get_user_conv_team_name(
            user_id=user_id, conv_id=conv_id
        )
        initial_team = Team.get_team(team_name)  # type: ignore
        create_new_conv = False
    except ValueError:
        create_new_conv = True

    if create_new_conv:
        initial_team = initial_team_class(  # type: ignore
            user_id=user_id,
            conv_id=conv_id,
            task=task,
            roles=roles,
            work_dir=str(working_dir),
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            human_input_mode=human_input_mode,
            use_async=use_async,
        )

    return initial_team, team_name, create_new_conv


def start_conversation(
    user_id: int,
    conv_id: int,
    root_dir: Path = Path(".") / "logs",
    *,
    task: str = "Hi!",
    roles: Optional[List[Dict[str, str]]] = None,
    max_round: int = 20,
    seed: int = 42,
    temperature: float = 0.2,
    human_input_mode: str = "ALWAYS",
    class_name: str = "initial_team",
) -> Tuple[str, str]:
    initial_team, team_name, create_new_conv = _get_initial_team(
        user_id=user_id,
        conv_id=conv_id,
        root_dir=root_dir,
        task=task,
        roles=roles,
        max_round=max_round,
        seed=seed,
        temperature=temperature,
        human_input_mode=human_input_mode,
        class_name=class_name,
    )
    if create_new_conv and initial_team:
        initial_team.initiate_chat()

        team_name = initial_team.name
        last_message = initial_team.get_last_message(add_prefix=False)

        return team_name, last_message

    else:
        return team_name, continue_conversation(team_name=team_name, message=task)


async def a_start_conversation(
    user_id: int,
    conv_id: int,
    root_dir: Path = Path(".") / "logs",
    *,
    task: str = "Hi!",
    roles: Optional[List[Dict[str, str]]] = None,
    max_round: int = 20,
    seed: int = 42,
    temperature: float = 0.2,
    human_input_mode: str = "ALWAYS",
    class_name: str = "initial_team",
) -> Tuple[str, str]:
    initial_team, team_name, create_new_conv = _get_initial_team(
        user_id=user_id,
        conv_id=conv_id,
        root_dir=root_dir,
        task=task,
        roles=roles,
        max_round=max_round,
        seed=seed,
        temperature=temperature,
        human_input_mode=human_input_mode,
        class_name=class_name,
        use_async=True,
    )
    if create_new_conv and initial_team:
        await initial_team.a_initiate_chat()

        team_name = initial_team.name
        last_message = initial_team.get_last_message(add_prefix=False)

        return team_name, last_message

    else:
        last_message = await a_continue_conversation(team_name=team_name, message=task)
        return team_name, last_message


def continue_conversation(team_name: str, message: str) -> str:
    initial_team = Team.get_team(team_name)

    initial_team.continue_chat(message=message)

    last_message: str = initial_team.get_last_message(add_prefix=False)

    return last_message


async def a_continue_conversation(team_name: str, message: str) -> str:
    initial_team = Team.get_team(team_name)

    await initial_team.a_continue_chat(message=message)

    last_message: str = initial_team.get_last_message(add_prefix=False)

    return last_message
