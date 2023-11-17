import shutil
from pathlib import Path

from captn.captn_agents.backend.end_to_end import (
    continue_conversation,
    start_conversation,
)
from captn.captn_agents.backend.team import Team

from .utils import last_message_is_termination

# record the cassete (first time): pytest --record-mode=once test_end_to_end.py -s


# cassettes/{module_name}/test_end_to_end.yaml will be used
# @pytest.mark.vcr(
#     filter_headers=["api-key"]
# )
def test_end_to_end() -> None:
    root_dir = Path("./logs").resolve()
    if root_dir.exists():
        shutil.rmtree(root_dir)

    roles = [
        {
            "Name": "User_proxy",
            "Description": "Your job is to comunicate with the Product Owner, do NOT suggest any code or execute the code by yourself",
        },
        {
            "Name": "Product_owner",
            "Description": "You are a product owner in a software company.",
        },
    ]
    task = "Create a python script for checking whether a string is palindrome or not"
    team_name, last_message = start_conversation(
        user_id=1,
        conv_id=17,
        task=task,
        roles=roles,
        root_dir=root_dir,
        seed=45,
        human_input_mode="NEVER",
    )

    initial_team = Team.get_team(team_name)
    assert last_message_is_termination(initial_team)

    continue_conversation(
        team_name=team_name,
        message="Please also create README.md for the initial task",
    )
