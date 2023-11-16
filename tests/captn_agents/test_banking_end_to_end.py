import shutil
from pathlib import Path

from captn_agents.end_to_end import continue_conversation, start_conversation
from captn_agents.team import Team

from .utils import last_message_is_termination


def test_end_to_end() -> None:
    root_dir = Path("./logs/captn").resolve()
    if root_dir.exists():
        shutil.rmtree(root_dir)

    task = "I need a loan for 100,000 euros for a period of 10 years. Please provide me the credit calculation"
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        root_dir=root_dir,
        seed=45,
        max_round=15,
        human_input_mode="NEVER",
        class_name="banking_initial_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)

    last_message = continue_conversation(
        team_name=team_name,
        message="I don't have any previous loans or credit history.",
    )
    print("*" * 100)
    print(last_message)
    assert last_message_is_termination(initial_team)


def test_non_relevan_questions() -> None:
    root_dir = Path("./logs/captn").resolve()
    if root_dir.exists():
        shutil.rmtree(root_dir)

    task = "Where are you from?"
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        root_dir=root_dir,
        seed=45,
        max_round=15,
        human_input_mode="NEVER",
        class_name="banking_initial_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)


def test_hello() -> None:
    root_dir = Path("./logs/captn").resolve()
    if root_dir.exists():
        shutil.rmtree(root_dir)

    task = "Hello"
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        root_dir=root_dir,
        seed=45,
        max_round=15,
        human_input_mode="NEVER",
        class_name="banking_initial_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)


def test_final() -> None:
    root_dir = Path("./logs/captn").resolve()
    if root_dir.exists():
        shutil.rmtree(root_dir)

    task = "Trebam kredit za stan."
    user_id = 1
    conv_id = 17

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task=task,
        root_dir=root_dir,
        seed=45,
        max_round=15,
        human_input_mode="NEVER",
        class_name="banking_initial_team",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task="Treba mi 100 000eura.",
    )
    print("*" * 100)
    print(last_message)
    assert last_message_is_termination(initial_team)

    team_name, last_message = start_conversation(
        user_id=user_id,
        conv_id=conv_id,
        task="Na 10 godina.",
    )
    print("*" * 100)
    print(last_message)
    assert last_message_is_termination(initial_team)
