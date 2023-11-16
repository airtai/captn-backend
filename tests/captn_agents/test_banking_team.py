import unittest

# from unittest.mock import Mock
from captn_agents.banking_team import BankingTeam

from .utils import last_message_is_termination


def test_get_login_url() -> None:
    user_id = 13
    task = "I need a loan for 100,000 euros for a period of 10 years. Please provide me the credit calculation"

    with unittest.mock.patch(
        "captn_agents.banking_team.ask_for_additional_info",
        return_value="I don't know, I am fine with any proposal you suggest",  # type: ignore
    ):
        google_ads_team = BankingTeam(task=task, user_id=user_id)
        google_ads_team.initiate_chat()

        assert last_message_is_termination(google_ads_team)
