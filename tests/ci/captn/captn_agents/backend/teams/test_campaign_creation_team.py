import random
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.teams import Team
from captn.captn_agents.backend.teams._campaign_creation_team import (
    CampaignCreationTeam,
)
from captn.captn_agents.backend.tools._campaign_creation_team_tools import (
    _create_ad_group,
    _create_ad_group_ad,
    _create_ad_group_keyword,
)
from captn.captn_agents.backend.tools._google_ads_team_tools import create_campaign
from captn.google_ads.client import ALREADY_AUTHENTICATED

from .fixtures.tasks import campaign_creation_team_task
from .helpers import helper_test_init


class TestCampaignCreationTeam:
    def test_init(self) -> None:
        campaign_creation_team = CampaignCreationTeam(
            user_id=123,
            conv_id=456,
            task="do your magic",
        )

        helper_test_init(
            team=campaign_creation_team,
            number_of_team_members=3,
            number_of_functions=7,
            team_class=CampaignCreationTeam,
        )

    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.campaign_creation_team
    def test_end2end(self) -> None:
        def ask_client_for_permission_mock(*args, **kwargs) -> str:
            customer_to_update = (
                "We propose changes for the following customer: 'IKEA' (ID: 1111)"
            )
            assert "resource_details" in kwargs, f"{kwargs.keys()=}"
            assert "proposed_changes" in kwargs, f"{kwargs.keys()=}"
            message = f"{customer_to_update}\n\n{kwargs['resource_details']}\n\n{kwargs['proposed_changes']}"

            clients_answer = "yes"
            # In real ask_client_for_permission, we would append (message, None)
            # and we would update the clients_question_answer_list with the clients_answer in the continue_conversation function
            context = kwargs["context"]
            context.clients_question_answer_list.append((message, clients_answer))
            return clients_answer

        try:
            campaign_creation_team = CampaignCreationTeam(
                user_id=123,
                conv_id=456,
                task=campaign_creation_team_task,
            )

            with (
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "list_accessible_customers",
                    return_value=["1111"],
                ),
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "ask_client_for_permission",
                    wraps=ask_client_for_permission_mock,
                ) as mock_ask_client_for_permission,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group",
                    wraps=_create_ad_group,
                ) as mock_create_ad_group,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group_ad",
                    wraps=_create_ad_group_ad,
                ) as mock_create_ad_group_ad,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._campaign_creation_team_tools._create_ad_group_keyword",
                    wraps=_create_ad_group_keyword,
                ) as mock_create_ad_group_keyword,
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "execute_query",
                    return_value=(
                        "The currency code for the customer is 'EUR'.\nPlease do not use this command again.",
                    ),
                ),
                unittest.mock.patch.object(
                    campaign_creation_team.toolbox.functions,
                    "create_campaign",
                    wraps=create_campaign,
                ) as mock_create_campaign,
                unittest.mock.patch(
                    "captn.captn_agents.backend.tools._google_ads_team_tools._get_customer_currency",
                    return_value="EUR",
                ),
                unittest.mock.patch(
                    "captn.google_ads.client.get_login_url",
                    return_value={"login_url": ALREADY_AUTHENTICATED},
                ),
                unittest.mock.patch(
                    "captn.google_ads.client.requests_get",
                    return_value=MagicMock(),
                ) as mock_requests_get,
            ):
                mock_requests_get.return_value.ok = True
                mock_requests_get.return_value.json.side_effect = [
                    f"Resource with id: {random.randint(100, 1000)} created!"
                    for _ in range(200)
                ]

                with TemporaryDirectory() as cache_dir:
                    with Cache.disk(cache_path_root=cache_dir) as cache:
                        campaign_creation_team.initiate_chat(cache=cache)

                mock_create_campaign.assert_called()
                mock_ask_client_for_permission.assert_called()
                mock_create_ad_group.assert_called()
                mock_create_ad_group_ad.assert_called()
                mock_create_ad_group_keyword.assert_called()
                assert len(campaign_creation_team.clients_question_answer_list) > 0
                assert (
                    len(campaign_creation_team.clients_question_answer_list)
                    == mock_ask_client_for_permission.call_count
                )
        finally:
            user_id, conv_id = campaign_creation_team.name.split("_")[-2:]
            success = Team.pop_team(user_id=int(user_id), conv_id=int(conv_id))
            assert success is not None
