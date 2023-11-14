__all__ = [
    "start_conversation",
    "continue_conversation",
]

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from captn_agents.captn_initial_team import CaptnInitialTeam
from captn_agents.initial_team import (
    InitialTeam,
)
from captn_agents.team import Team

initial_team_roles = [
    {
        "Name": "User_proxy",
        "Description": "Your job is to comunicate with the Account_manager, do NOT suggest any code or execute the code by yourself",
    },
    {
        "Name": "Account_manager",
        "Description": "You are an account manager in digital marketing agency.",
    },
]

captn_initial_team_roles = [
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
    use_captn_class: bool = False,
) -> Tuple[str, str]:
    working_dir: Path = root_dir / f"{user_id=}" / f"{conv_id=}"
    working_dir.mkdir(parents=True, exist_ok=True)

    initial_team_class = CaptnInitialTeam if use_captn_class else InitialTeam
    if roles is None:
        roles = captn_initial_team_roles if use_captn_class else initial_team_roles

    
    try:
        team_name = InitialTeam.get_user_conv_team_name(user_id=user_id, conv_id=conv_id)
        initial_team = Team.get_team(team_name)
        create_new_conv = False
    except:
        create_new_conv = True

    if create_new_conv:
        initial_team = initial_team_class(
            user_id=user_id,
            conv_id=conv_id,
            task=task,
            roles=roles,
            work_dir=str(working_dir),
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            human_input_mode=human_input_mode,
        )
        initial_team.initiate_chat()

        team_name = initial_team.name
        last_message = initial_team.get_last_message()

        return team_name, last_message
    
    else:
        continue_conversation(team_name=team_name, message=task)


def continue_conversation(team_name: str, message: str) -> str:
    initial_team = Team.get_team(team_name)

    initial_team.continue_chat(message=message)

    last_message = initial_team.get_last_message()

    return last_message
