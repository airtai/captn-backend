from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type

from .teams import Team

__all__ = [
    "start_or_continue_conversation",
    "continue_conversation",
]


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

    initial_team_class: Type[Team] = Team.get_class_by_name(class_name)
    initial_team = None
    try:
        team_name = Team.get_user_conv_team_name(
            name_prefix=initial_team_class._get_team_name_prefix(),
            user_id=user_id,
            conv_id=conv_id,
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
            work_dir=str(working_dir),
            max_round=max_round,
            seed=seed,
            temperature=temperature,
        )

    return initial_team, team_name, create_new_conv


def start_or_continue_conversation(
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


def continue_conversation(team_name: str, message: str) -> str:
    message = message.strip()
    initial_team = Team.get_team(team_name)
    initial_team.update_clients_question_answer_list(message)

    initial_team.continue_chat(message=message)

    last_message: str = initial_team.get_last_message(add_prefix=False)

    return last_message
