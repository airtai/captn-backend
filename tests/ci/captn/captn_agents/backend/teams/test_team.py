import unittest
from typing import Iterator
from unittest.mock import MagicMock

import autogen
import httpx
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
        team.llm_config = {
            "api_key": "DUMMY",  # pragma: allowlist secret
            "model": "gpt-4",
        }
        member = team._create_member("QA gpt", "Description1")

        system_message = """You are qa_gpt, Description1

Your task is to chat with other team members and try to solve the given task.
Do NOT try to finish the task until other team members give their opinion.
"""
        assert member.system_message == system_message
        assert isinstance(member, autogen.AssistantAgent)

    def test_create_members(self) -> None:
        team = Team(roles=TestTeam.roles, user_id=234, conv_id=456)
        team.llm_config = {
            "api_key": "dummy",  # pragma: allowlist secret
            "model": "gpt-4",
        }
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

    def test_update_recommended_modifications_and_answer_list(self) -> None:
        team = Team(roles=TestTeam.roles, user_id=123, conv_id=456)
        team.recommended_modifications_and_answer_list.append(("Question1", None))
        team.update_recommended_modifications_and_answer_list("Answer1")
        assert team.recommended_modifications_and_answer_list == [
            ("Question1", "Answer1")
        ]

        team.update_recommended_modifications_and_answer_list("Answer2")
        assert team.recommended_modifications_and_answer_list == [
            ("Question1", "Answer1")
        ]

        team.recommended_modifications_and_answer_list.append(("Question2", None))
        team.update_recommended_modifications_and_answer_list("Answer3")
        assert team.recommended_modifications_and_answer_list == [
            ("Question1", "Answer1"),
            ("Question2", "Answer3"),
        ]

    @pytest.mark.parametrize("number_of_exceptions", [0, 2, 10])
    def test_retry_func(self, number_of_exceptions) -> None:
        team = Team(roles=TestTeam.roles, user_id=123, conv_id=456)
        team.manager = MagicMock()
        team.manager.send = MagicMock()

        if number_of_exceptions == 0:
            team.retry_func(delay=0)
            team.manager.send.assert_called_once()
        elif number_of_exceptions > len(Team._retry_messages):
            team.manager.send.side_effect = httpx.ReadTimeout("Timeout")
            with pytest.raises(httpx.ReadTimeout):
                team.retry_func(delay=0)
            assert team.manager.send.call_count == len(Team._retry_messages)
        else:
            team.manager.send.side_effect = [
                httpx.ReadTimeout("Timeout")
            ] * number_of_exceptions + [None]
            team.retry_func(delay=0)
            assert team.manager.send.call_count == number_of_exceptions + 1

    @pytest.mark.parametrize("raise_exception", [False, True])
    def test_handle_exceptions_decorator(self, raise_exception) -> None:
        @Team.handle_exceptions
        def f(self: Team, message: str, raise_exception: bool) -> None:
            if raise_exception:
                raise httpx.ReadTimeout("Timeout")

        team = Team(roles=TestTeam.roles, user_id=123, conv_id=456)
        team.groupchat = MagicMock()
        team.groupchat.messages = ["message1"]
        team.retry_func = MagicMock()

        f(team, "message", raise_exception=raise_exception)
        if raise_exception:
            team.retry_func.assert_called_once()
        else:
            team.retry_func.assert_not_called()

    @pytest.mark.parametrize("number_of_exceptions", [0, 2, 10, 30])
    def test_initiate_chat(self, number_of_exceptions) -> None:
        team = Team(roles=TestTeam.roles, user_id=123, conv_id=456)
        team.initial_message = "Initial message"
        team.manager = MagicMock()
        team.manager.initiate_chat = MagicMock()
        team.manager.send = MagicMock()
        team.groupchat = MagicMock()
        team.groupchat.messages = ["message1", "message2"]

        if number_of_exceptions == 0:
            team.initiate_chat(delay=0)
            team.manager.send.assert_not_called()
            team.manager.initiate_chat.assert_called_once()
        elif (
            number_of_exceptions
            > len(Team._retry_messages) * Team._MAX_RETRIES_FROM_SCRATCH
        ):
            team.manager.initiate_chat.side_effect = httpx.ReadTimeout("Timeout")
            team.manager.send.side_effect = httpx.ReadTimeout("Timeout")
            with pytest.raises(httpx.ReadTimeout):
                team.initiate_chat(delay=0)

            expected_call_count = (
                len(Team._retry_messages) * Team._MAX_RETRIES_FROM_SCRATCH
            )
            assert team.manager.send.call_count == expected_call_count
            assert (
                team.manager.initiate_chat.call_count == Team._MAX_RETRIES_FROM_SCRATCH
            )
        elif number_of_exceptions < len(Team._retry_messages):
            team.manager.initiate_chat.side_effect = httpx.ReadTimeout("Timeout")
            team.manager.send.side_effect = [
                httpx.ReadTimeout("Timeout")
            ] * number_of_exceptions + [None]
            team.initiate_chat(delay=0)
            assert team.manager.send.call_count == number_of_exceptions + 1
            team.manager.initiate_chat.assert_called_once()
        elif number_of_exceptions == 10:
            team.manager.initiate_chat.side_effect = httpx.ReadTimeout("Timeout")
            team.manager.send.side_effect = [
                httpx.ReadTimeout("Timeout")
            ] * number_of_exceptions + [None]
            team.initiate_chat(delay=0)
            assert team.manager.send.call_count == number_of_exceptions + 1
            assert team.manager.initiate_chat.call_count == 2

    @pytest.mark.parametrize("num_of_messages", [2, 5, 10])
    def test_max_number_of_messages(self, num_of_messages) -> None:
        max_round = 5
        team = Team(roles=TestTeam.roles, user_id=123, conv_id=456, max_round=max_round)
        team.initial_message = "Initial message"
        team.manager = MagicMock()
        team.manager.initiate_chat = MagicMock()
        team.manager.send = MagicMock()
        team.groupchat = MagicMock()
        team.groupchat.messages = ["message1"] * num_of_messages

        if num_of_messages < max_round:
            team.initiate_chat(delay=0)
            team.manager.send.assert_not_called()
            team.manager.initiate_chat.assert_called_once()
        else:
            with pytest.raises(Exception):  # noqa: B017
                team.initiate_chat(delay=0)
            team.manager.send.assert_not_called()
            assert (
                team.manager.initiate_chat.call_count == Team._MAX_RETRIES_FROM_SCRATCH
            )

    def test_get_last_message(self) -> None:
        team = Team(roles=TestTeam.roles, user_id=123, conv_id=456)

        team.groupchat = MagicMock()

        last_successful_message = """{"message":"To better align with your goals of boosting sales and increasing brand awareness, could you please clarify if you are looking to create a new campaign or optimize an existing one for your website?","smart_suggestions":{"suggestions":["Create new campaign","Optimize existing campaign"],"type":"oneOf"},"is_question":true,"status":"pause","terminate_groupchat":true}"""

        last_message_with_junk = f"""{last_successful_message}

Error: We have already another message to the client and we are waiting for his response! Please wait for the client to respond before sending another message!

Error: We have already another message to the client and we are waiting for his response! Please wait for the client to respond before sending another message!"""
        # mock team get team.get_messages
        with unittest.mock.patch.object(Team, "get_messages") as mock_get_messages:
            mock_get_messages.return_value = [{"content": last_message_with_junk}]
            last_message = team.get_last_message(add_prefix=False)
            assert last_message == last_successful_message


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
