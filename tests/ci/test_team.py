from typing import Iterator

import autogen
import pytest

from captn.captn_agents.backend.teams._team import Team


class TestTeam:
    roles = [
        {"Name": "Role1", "Description": "Description1"},
        {"Name": "Role2", "Description": "Description2"},
    ]

    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        Team._teams.clear()
        yield

    def test_create_member(self) -> None:
        team = Team(roles=TestTeam.roles, user_id=123, conv_id=456)
        team.llm_config = {"api_key": "DUMMY", "model": "gpt-4"}
        member = team._create_member("QA gpt", "Description1")

        system_message = """You are qa_gpt, Description1

Your task is to chat with other team members and try to solve the given task.
Do NOT try to finish the task until other team members give their opinion.
"""
        assert member.system_message == system_message
        assert isinstance(member, autogen.AssistantAgent)

    def test_create_members(self) -> None:
        team = Team(roles=TestTeam.roles, user_id=234, conv_id=456)
        team.llm_config = {"api_key": "dummy", "model": "gpt-4"}
        team._create_members()

        assert len(team.members) == len(TestTeam.roles)
        assert isinstance(team.groupchat, autogen.GroupChat)
        for member in team.members:
            assert isinstance(member, autogen.AssistantAgent)

    def test_is_termination_msg(self) -> None:
        assert Team._is_termination_msg({}) is False
        assert Team._is_termination_msg({"content": None}) is False
        assert (
            Team._is_termination_msg({"content": "This should return false"}) is False
        )
        assert (
            Team._is_termination_msg({"content": "Woohoo terminate_groupchat..."})
            is True
        )

        assert Team._is_termination_msg({"content": "Woohoo TERMINATE ..."}) is False

    def test_update_clients_question_answer_list(self) -> None:
        team = Team(roles=TestTeam.roles, user_id=123, conv_id=456)
        team.clients_question_answer_list.append(("Question1", None))
        team.update_clients_question_answer_list("Answer1")
        assert team.clients_question_answer_list == [("Question1", "Answer1")]

        team.update_clients_question_answer_list("Answer2")
        assert team.clients_question_answer_list == [("Question1", "Answer1")]

        team.clients_question_answer_list.append(("Question2", None))
        team.update_clients_question_answer_list("Answer3")
        assert team.clients_question_answer_list == [
            ("Question1", "Answer1"),
            ("Question2", "Answer3"),
        ]


class TestTeamRegistry:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        if "my name" in Team._team_registry:
            del Team._team_registry["my name"]

        yield

        if "my name" in Team._team_registry:
            del Team._team_registry["my name"]

    def test_register_team(self) -> None:
        @Team.register_team(name="my name")
        class MyTeam(Team):
            pass

        assert "my name" in Team._team_registry
        assert Team._team_registry["my name"] == MyTeam

        factory = Team.get_class_by_registred_team_name("my name")

        assert factory == MyTeam
