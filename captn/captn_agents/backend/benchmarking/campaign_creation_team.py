import random
import unittest
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Any, Iterator, Tuple
from unittest.mock import MagicMock

from autogen.cache import Cache

from captn.google_ads.client import ALREADY_AUTHENTICATED

from ..teams import Team
from ..teams._campaign_creation_team import (
    CampaignCreationTeam,
)
from ..tools._campaign_creation_team_tools import (
    _create_ad_group,
    _create_ad_group_ad,
    _create_ad_group_keyword,
)
from ..tools._google_ads_team_tools import _mock_create_campaign
from .fixtures.campaign_creation_team_fixtures import (
    CAMPAIGN_CREATION_DISNEY,
    CAMPAIGN_CREATION_FASTSTREAM,
    CAMPAIGN_CREATION_IKEA,
)
from .helpers import get_config_list
from .models import Models

# def _ask_client_for_permission_mock(*args: Any, **kwargs: Dict[str, Any]) -> str:
#     print("Inside _ask_client_for_permission_mock")
#     customer_to_update = (
#         "We propose changes for the following customer: 'IKEA' (ID: 1111)"
#     )
#     assert "resource_details" in kwargs, f"{kwargs.keys()=}"  # nosec: [B101]
#     assert "proposed_changes" in kwargs, f"{kwargs.keys()=}"  # nosec: [B101]
#     message = f"{customer_to_update}\n\n{kwargs['resource_details']}\n\n{kwargs['proposed_changes']}"

#     clients_answer = "yes"
#     # In real ask_client_for_permission, we would append (message, None)
#     # and we would update the clients_question_answer_list with the clients_answer in the continue_conversation function
#     context: Context = kwargs["context"]  # type: ignore[assignment]
#     context.clients_question_answer_list.append((message, clients_answer))
#     return clients_answer


URL_TASK_DICT = {
    "https://www.ikea.com/gb/en/": CAMPAIGN_CREATION_IKEA,
    "https://www.disneystore.eu": CAMPAIGN_CREATION_DISNEY,
    # "https://www.hamleys.com/": "",
    # "https://www.konzum.hr": "",
    "https://faststream.airt.ai": CAMPAIGN_CREATION_FASTSTREAM,
}


@contextmanager
def _patch_campaign_creation_team_vars() -> Iterator[Tuple[Any, Any, Any, Any]]:
    with (
        # unittest.mock.patch.object(
        #     campaign_creation_team.toolbox.functions,
        #     "list_accessible_customers",
        #     return_value=["1111"],
        # ),
        unittest.mock.patch(
            "captn.captn_agents.backend.tools._google_ads_team_tools.list_accessible_customers_client",
            return_value=["1111"],
        ),
        # unittest.mock.patch.object(
        #     campaign_creation_team.toolbox.functions,
        #     "ask_client_for_permission",
        #     wraps=_ask_client_for_permission_mock,
        # ) as mock_ask_client_for_permission,
        # unittest.mock.patch(
        #     "captn.captn_agents.backend.tools._google_ads_team_tools.ask_client_for_permission",
        #     wraps=_ask_client_for_permission_mock,
        # ) as mock_ask_client_for_permission,
        unittest.mock.patch(
            "captn.captn_agents.backend.tools._functions.BENCHMARKING",
            True,
        ),
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
        # unittest.mock.patch.object(
        #     campaign_creation_team.toolbox.functions,
        #     "execute_query",
        #     return_value=(
        #         "The currency code for the customer is 'EUR'.\nPlease do not use this command again.",
        #     ),
        # ),
        unittest.mock.patch(
            "captn.captn_agents.backend.tools._google_ads_team_tools.execute_query_client",
            return_value=(
                "The currency code for the customer is 'EUR'.\nPlease do not use this command again.",
            ),
        ),
        # unittest.mock.patch.object(
        #     campaign_creation_team.toolbox.functions,
        #     "create_campaign",
        #     wraps=create_campaign,
        # ) as mock_create_campaign,
        unittest.mock.patch(
            "captn.captn_agents.backend.tools._google_ads_team_tools._mock_create_campaign",
            wraps=_mock_create_campaign,
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
            f"Resource with id: {random.randint(100, 1000)} created!"  # nosec: [B311]
            for _ in range(200)
        ]
        yield (
            mock_create_ad_group,
            mock_create_ad_group_ad,
            mock_create_ad_group_keyword,
            mock_create_campaign,
        )


def run_assertions_and_return_last_message(
    campaign_creation_team: CampaignCreationTeam,
    mock_create_ad_group: Any,
    mock_create_ad_group_ad: Any,
    mock_create_ad_group_keyword: Any,
    mock_create_campaign: Any,
) -> str:
    mock_create_campaign.assert_called()
    mock_create_ad_group.assert_called()
    mock_create_ad_group_ad.assert_called()
    mock_create_ad_group_keyword.assert_called()
    assert len(campaign_creation_team.clients_question_answer_list) > 0  # nosec: [B101]

    last_message = campaign_creation_team.get_last_message()
    return last_message


def benchmark_campaign_creation(
    url: str,
    llm: str = Models.gpt4,
) -> str:
    try:
        task = URL_TASK_DICT[url]
        config_list = get_config_list(llm)
        campaign_creation_team = CampaignCreationTeam(
            user_id=123,
            conv_id=456,
            task=task,
            config_list=config_list,
        )
        with _patch_campaign_creation_team_vars() as (
            mock_create_ad_group,
            mock_create_ad_group_ad,
            mock_create_ad_group_keyword,
            mock_create_campaign,
        ):
            with TemporaryDirectory() as cache_dir:
                with Cache.disk(cache_path_root=cache_dir) as cache:
                    campaign_creation_team.initiate_chat(cache=cache)

            return run_assertions_and_return_last_message(
                campaign_creation_team=campaign_creation_team,
                mock_create_ad_group=mock_create_ad_group,
                mock_create_ad_group_ad=mock_create_ad_group_ad,
                mock_create_ad_group_keyword=mock_create_ad_group_keyword,
                mock_create_campaign=mock_create_campaign,
            )
    finally:
        user_id, conv_id = campaign_creation_team.name.split("_")[-2:]
        success = Team.pop_team(user_id=int(user_id), conv_id=int(conv_id))
        assert success is not None  # nosec: [B101]
