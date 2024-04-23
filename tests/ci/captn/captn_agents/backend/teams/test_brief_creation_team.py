import unittest
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Iterator

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.teams import (
    BriefCreationTeam,
    Team,
)

from ..tools.test_brief_creation_team_tools import (
    BRIEF_CREATION_TEAM_RESPONSE,
)
from .helpers import get_client_response, helper_test_init


class TestBriefCreationTeam:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        Team._teams.clear()
        yield

    def test_init(self) -> None:
        brief_creation_team = BriefCreationTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        helper_test_init(
            team=brief_creation_team,
            number_of_team_members=3,
            number_of_functions=4,
            team_class=BriefCreationTeam,
        )

    def test_get_avaliable_teams_and_their_descriptions(self) -> None:
        avaliable_teams_and_their_descriptions = (
            BriefCreationTeam._get_avaliable_team_names_and_their_descriptions()
        )

        # All teams except the BriefCreationTeam should be in the dictionary
        assert (
            len(avaliable_teams_and_their_descriptions) == len(Team._team_registry) - 1
        )

    @contextmanager
    def patch_vars(
        self,
        team: BriefCreationTeam,
        client_system_message: str,
        cache: Cache,
    ) -> Iterator[None]:
        with (
            unittest.mock.patch.object(
                team.toolbox.functions,
                "reply_to_client",
                wraps=get_client_response(
                    team=team, cache=cache, client_system_message=client_system_message
                ),
            ) as mock_reply_to_client,
            unittest.mock.patch.object(
                team.toolbox.functions, "get_info_from_the_web_page"
            ) as mock_get_info_from_the_web_page,
            unittest.mock.patch.object(
                team.toolbox.functions,
                "delagate_task",
            ) as mock_delagate_task,
            unittest.mock.patch.object(
                team.toolbox.functions,
                "get_brief_template",
                wraps=team.toolbox.functions.get_brief_template,  # type: ignore[attr-defined]
            ) as mock_get_brief_template,
        ):
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
            yield (
                mock_reply_to_client,
                mock_get_info_from_the_web_page,
                mock_delagate_task,
                mock_get_brief_template,
            )

    def _test_end2_end_default_team_choosed(
        self, task: str, team_name: str, client_system_message: str
    ) -> None:
        user_id = 123
        conv_id = 234

        team = BriefCreationTeam(task=task, user_id=user_id, conv_id=conv_id)

        try:
            with TemporaryDirectory() as cache_dir:
                with Cache.disk(cache_path_root=cache_dir) as cache:
                    with self.patch_vars(
                        team=team,
                        client_system_message=client_system_message,
                        cache=cache,
                    ) as (
                        _,
                        mock_get_info_from_the_web_page,
                        mock_delagate_task,
                        mock_get_brief_template,
                    ):
                        team.initiate_chat(cache=cache)

                        mock_get_info_from_the_web_page.assert_called()
                        mock_get_brief_template.assert_called()
                        mock_delagate_task.assert_called_once()
                        assert (
                            mock_delagate_task.call_args.kwargs[
                                "task_and_context_to_delegate"
                            ].team_name
                            == team_name
                        )
        finally:
            poped_team = Team.pop_team(user_id=user_id, conv_id=conv_id)
            assert isinstance(poped_team, Team)

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.brief_creation_team
    def test_end2_end_campaign_creation_team_choosed(self) -> None:
        task = """Business: {Boost sales / Increase brand awareness}
Goal: {Increase brand awareness and boost sales}
Current Situation: {Website: airt.ai, Digital Marketing: Yes, Using Google Ads}
Website: {airt.ai}
Digital Marketing Objectives: {Increase brand awareness, Boost sales}
Next Steps: {First step is to get the summary of the Website.}
Any Other Information Related to Customer Brief: {}"""

        client_system_message = """You are a client who wants to create a ne google ads campaign.
You are in a conversation with a team of experts who will help you create a new google ads campaign.
Use their smart suggestions to guide you through the process.

Your answers should be short and to the point.
e.g.
I want to create new campaign.
I accept the suggestion.
Yes
"""

        self._test_end2_end_default_team_choosed(
            task=task,
            team_name="campaign_creation_team",
            client_system_message=client_system_message,
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.brief_creation_team
    def test_end2_end_default_team_choosed(self) -> None:
        task = """Business: Boost sales
Goal: Increase brand awareness
Website: airt.ai
Digital Marketing Objectives: Use Google Ads to maximize reach and conversions
Next Steps: First step is to get the summary of the Website.
Any Other Information Related to Customer Brief: None"""

        client_system_message = """You are a client who wants to optimize existing google ads campaign.
You are in a conversation with a team of experts who will help you optimize your google ads.
Use their smart suggestions to guide you through the process.

Your answers should be short and to the point.
e.g.
I want to optimize existing campaign.
I accept the suggestion.
Yes
"""
        self._test_end2_end_default_team_choosed(
            task=task,
            team_name="default_team",
            client_system_message=client_system_message,
        )
