from pathlib import Path
from typing import Tuple, Type

from .teams import Team
from .tools._functions import BaseContext

__all__ = [
    "start_or_continue_conversation",
    "continue_conversation",
]


def _get_team(
    user_id: int,
    conv_id: int,
    root_dir: Path,
    *,
    task: str,
    max_round: int,
    seed: int,
    temperature: float,
    registred_team_name: str,
) -> Tuple[Team, bool]:
    working_dir: Path = root_dir / f"{user_id=}" / f"{conv_id=}"
    working_dir.mkdir(parents=True, exist_ok=True)

    team = None
    team = Team.get_team(user_id=user_id, conv_id=conv_id)
    if team is not None:
        return team, False
    else:
        team_class: Type[Team] = Team.get_class_by_registred_team_name(
            registred_team_name
        )
        team = team_class(  # type: ignore
            user_id=user_id,
            conv_id=conv_id,
            task=task,
            work_dir=str(working_dir),
            max_round=max_round,
            seed=seed,
            temperature=temperature,
        )
        return team, True


def start_or_continue_conversation(
    user_id: int,
    conv_id: int,
    root_dir: Path = Path(".") / "logs",
    *,
    task: str = "Hi!",
    max_round: int = 20,
    seed: int = 42,
    temperature: float = 0.2,
    registred_team_name: str = "initial_team",
) -> Tuple[str, str]:
    team, create_new_conv = _get_team(
        user_id=user_id,
        conv_id=conv_id,
        root_dir=root_dir,
        task=task,
        max_round=max_round,
        seed=seed,
        temperature=temperature,
        registred_team_name=registred_team_name,
    )

    team_name = team.name

    if create_new_conv and team:
        team.initiate_chat()

        last_message = team.get_last_message(add_prefix=False)

        return team_name, last_message

    else:
        return team_name, continue_conversation(team, message=task)


def continue_conversation(team: Team, message: str) -> str:
    if team.toolbox is not None:
        context: BaseContext = team.toolbox._context  # type: ignore[assignment]
        context.waiting_for_client_response = False
    team.update_recommended_modifications_and_answer_list(message.strip())

    team.continue_chat(message=message)

    last_message: str = team.get_last_message(add_prefix=False)

    return last_message
