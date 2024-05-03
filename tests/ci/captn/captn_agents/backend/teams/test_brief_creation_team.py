import unittest
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Iterator

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.benchmarking.fixtures.brief_creation_team_fixtures import (
    BRIEF_CREATION_TEAM_RESPONSE,
    WEB_PAGE_SUMMARY_IKEA,
)
from captn.captn_agents.backend.benchmarking.helpers import get_client_response
from captn.captn_agents.backend.teams import (
    BriefCreationTeam,
    Team,
)

from .helpers import helper_test_init


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
            unittest.mock.patch(
                "captn.captn_agents.backend.tools._brief_creation_team_tools._get_info_from_the_web_page_original",
                return_value=WEB_PAGE_SUMMARY_IKEA,
            ) as mock_get_info_from_the_web_page,
            unittest.mock.patch(
                "captn.captn_agents.backend.tools._brief_creation_team_tools._change_the_team_and_start_new_chat",
                return_value=BRIEF_CREATION_TEAM_RESPONSE,
            ) as mock_change_the_team_and_start_new_chat,
            unittest.mock.patch.object(
                team.toolbox.functions,
                "get_brief_template",
                wraps=team.toolbox.functions.get_brief_template,  # type: ignore[attr-defined]
            ) as mock_get_brief_template,
        ):
            yield (
                mock_reply_to_client,
                mock_get_info_from_the_web_page,
                mock_change_the_team_and_start_new_chat,
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
                        mock_change_the_team_and_start_new_chat,
                        mock_get_brief_template,
                    ):
                        team.initiate_chat(cache=cache)

                        mock_get_info_from_the_web_page.assert_called()
                        mock_get_brief_template.assert_called()
                        mock_change_the_team_and_start_new_chat.assert_called()
                        team_class: Team = (
                            mock_change_the_team_and_start_new_chat.call_args.kwargs[
                                "team_class"
                            ]
                        )
                        assert team_class.get_registred_team_name() == team_name

        finally:
            poped_team = Team.pop_team(user_id=user_id, conv_id=conv_id)
            assert isinstance(poped_team, Team)

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.brief_creation_team
    def test_end2_end_campaign_creation_team_choosed(self) -> None:
        task = """Business: {Boost sales / Increase brand awareness}
Goal: {Increase brand awareness and boost sales}
Current Situation: {Website: https://www.ikea.com/gb/en, Digital Marketing: Yes, Using Google Ads}
Website: {https://www.ikea.com/gb/en}
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
Website: https://www.ikea.com/gb/en
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
