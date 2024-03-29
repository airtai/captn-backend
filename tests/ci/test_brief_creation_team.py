import unittest

import pytest

from captn.captn_agents.backend.teams import BriefCreationTeam, Team

from .test_brief_creation_team_tools import BRIEF_CREATION_TEAM_RESPONSE


class TestBriefCreationTeam:
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
    def test_end2_end(self) -> None:
        user_id = 123
        conv_id = 234
        task = "User wants to create a n new campaign. His website is airt.ai."

        with unittest.mock.patch(
            "captn.captn_agents.backend.teams._google_ads_team.reply_to_client_2"
        ) as mock_reply_to_client, unittest.mock.patch(
            "captn.captn_agents.backend.teams._google_ads_team.get_info_from_the_web_page"
        ) as mock_get_info_from_the_web_page, unittest.mock.patch(
            "captn.captn_agents.backend.tools._brief_creation_team_tools.delagate_task"
        ) as mock_delagate_task:
            mock_reply_to_client.return_value = "Do whatever you think is best."
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

            team = BriefCreationTeam(task=task, user_id=user_id, conv_id=conv_id)
            team.initiate_chat()

            mock_get_info_from_the_web_page.assert_called()
            mock_delagate_task.assert_called_once()
