from unittest import mock

import autogen

from captn.captn_agents.backend.team import Team

roles = [
    {"Name": "Role1", "Description": "Description1"},
    {"Name": "Role2", "Description": "Description2"},
]


@mock.patch("captn.captn_agents.backend.team.Team._get_team_name_prefix")
def test_get_new_team_name(mock_get_team_name_prefix: mock.MagicMock) -> None:
    mock_get_team_name_prefix.return_value = "Team"
    assert Team._get_new_team_name() == "Team_0"
    assert Team._get_new_team_name() == "Team_1"
    assert Team._get_new_team_name() == "Team_2"


def test_create_member() -> None:
    team = Team(roles=roles, name="Team_1")
    member = team._create_member("QA gpt", "Description1")

    system_message = """You are qa_gpt, Description1

Your task is to chat with other team mambers and try to solve the given task.
Do NOT try to finish the task until other team members give their opinion.
"""
    assert member.system_message == system_message
    assert isinstance(member, autogen.AssistantAgent)


def test_create_members() -> None:
    team = Team(roles=roles, name="Team_2")
    team._create_members()

    assert len(team.members) == len(roles)
    assert isinstance(team.groupchat, autogen.GroupChat)
    for member in team.members:
        assert isinstance(member, autogen.AssistantAgent)


def test_is_termination_msg() -> None:
    assert Team._is_termination_msg({}) is False
    assert Team._is_termination_msg({"content": None}) is False
    assert Team._is_termination_msg({"content": "This should return false"}) is False
    assert Team._is_termination_msg({"content": "Woohoo TERMINATE..."}) is True

    # TERMINATE must be a part of the last element in:
    # content_xs = content.split()
    # "TERMINATE" in content_xs[-1]
    assert Team._is_termination_msg({"content": "Woohoo TERMINATE ..."}) is False
