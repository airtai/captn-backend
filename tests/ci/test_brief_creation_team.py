import unittest
from tempfile import TemporaryDirectory
from typing import Iterator

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.teams import (
    BriefCreationTeam,
    Team,
)

from .test_brief_creation_team_tools import BRIEF_CREATION_TEAM_RESPONSE


class TestBriefCreationTeam:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        Team._teams.clear()
        yield

    def test_get_avaliable_teams_and_their_descriptions(self) -> None:
        avaliable_teams_and_their_descriptions = (
            BriefCreationTeam._get_avaliable_team_names_and_their_descriptions()
        )

        # All teams except the BriefCreationTeam should be in the dictionary
        assert (
            len(avaliable_teams_and_their_descriptions) == len(Team._team_registry) - 1
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.brief_creation_team
    def test_end2_end(self) -> None:
        user_id = 123
        conv_id = 234
        task = "I want to create a n new campaign. My website is: https://airt.ai"

        team = BriefCreationTeam(task=task, user_id=user_id, conv_id=conv_id)

        try:
            with unittest.mock.patch.object(
                team.toolbox.functions, "reply_to_client_2"
            ) as mock_reply_to_client, unittest.mock.patch.object(
                team.toolbox.functions, "get_info_from_the_web_page"
            ) as mock_get_info_from_the_web_page, unittest.mock.patch.object(
                team.toolbox.functions,
                "delagate_task",
            ) as mock_delagate_task, unittest.mock.patch.object(
                team.toolbox.functions,
                "get_brief_template",
                wraps=team.toolbox.functions.get_brief_template,  # type: ignore[attr-defined]
            ) as mock_get_brief_template:
                mock_reply_to_client.return_value = "I approve what ever you suggest. Please continue without asking me any more questions."
                mock_get_info_from_the_web_page.return_value = (
                    mock_get_info_from_the_web_page.return_value
                ) = """SUMMARY:

    Page content: The website is for a company called "airt" that offers an AI-powered framework for streaming app development. They provide a FastStream framework for creating, testing, and managing microservices for streaming data. They also have tools like Monotonic Neural Networks and Material for nbdev. The company focuses on driving impact with deep learning and incorporates a GPT-based model for predicting future events to be streamed. They have a community section and offer various products and tools. The website provides information about the company, news, and contact details.

    Relevant links:
    - FastStream framework: https://faststream.airt.ai
    - Monotonic Neural Networks: https://monotonic.airt.ai
    - Material for nbdev: https://nbdev-mkdocs.airt.ai
    - News: /news
    - About Us: /about-us
    - Company information: /company-information
    - Contact Us: /contact-us

    Keywords: airt, AI-powered framework, streaming app development, FastStream framework, microservices, Monotonic Neural Networks, Material for nbdev, deep learning, GPT-based model

    Headlines (MAX 30 char each): airt, AI-powered framework, FastStream, microservices, Monotonic Neural Networks, deep learning, GPT-based model, community, news, contact

    Descriptions (MAX 90 char each): AI-powered framework for streaming app development, Create, test, and manage microservices for streaming data, Driving impact with deep learning, GPT-based model for predicting future events, Explore news and contact information

    Use these information to SUGGEST the next steps to the client, but do NOT make any permanent changes without the client's approval!
    """
                mock_delagate_task.return_value = BRIEF_CREATION_TEAM_RESPONSE

                with TemporaryDirectory() as cache_dir:
                    with Cache.disk(cache_path_root=cache_dir) as cache:
                        team.initiate_chat(cache=cache)

                mock_get_info_from_the_web_page.assert_called()
                mock_get_brief_template.assert_called()
                mock_delagate_task.assert_called_once()
        finally:
            poped_team = Team.pop_team(user_id=user_id, conv_id=conv_id)
            assert isinstance(poped_team, Team)
            # assert isinstance(poped_team, CampaignCreationTeam)
