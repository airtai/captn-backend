import random
import unittest
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Any, Iterator, List, Tuple
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
from ..tools._functions import Context
from ..tools._google_ads_team_tools import _mock_create_campaign
from .fixtures.campaign_creation_team_fixtures import (
    CAMPAIGN_CREATION_DISNEY,
    CAMPAIGN_CREATION_FASTSTREAM,
    CAMPAIGN_CREATION_IKEA,
)
from .helpers import get_client_response_for_the_team_conv, get_config_list
from .models import Models

URL_TASK_DICT = {
    "https://www.ikea.com/gb/en/": CAMPAIGN_CREATION_IKEA,
    "https://www.disneystore.eu": CAMPAIGN_CREATION_DISNEY,
    # "https://www.hamleys.com/": "",
    # "https://www.konzum.hr": "",
    "https://faststream.airt.ai": CAMPAIGN_CREATION_FASTSTREAM,
}


def mock_get_campaign_ids(context: Context, customer_id: str) -> List[str]:
    print("Inside mock_get_campaign_ids")
    if len(context.created_campaigns) == 0:
        return []
    if customer_id not in context.created_campaigns:
        raise ValueError(f"Invalid customer ID: '{customer_id}'")
    return context.created_campaigns[customer_id]


@contextmanager
def _patch_campaign_creation_team_vars() -> Iterator[Tuple[Any, Any, Any, Any]]:
    accessible_customers = ["1111"]
    with (
        # unittest.mock.patch.object(
        #     campaign_creation_team.toolbox.functions,
        #     "list_accessible_customers",
        #     return_value=["1111"],
        # ),
        unittest.mock.patch(
            "captn.captn_agents.backend.tools._google_ads_team_tools.list_accessible_customers_client",
            return_value=accessible_customers,
        ),
        unittest.mock.patch(
            "captn.captn_agents.backend.tools._functions.list_accessible_customers",
            return_value=accessible_customers,
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
        unittest.mock.patch(
            "captn.captn_agents.backend.tools._functions._get_campaign_ids",
            wraps=mock_get_campaign_ids,
        ),
    ):
        mock_requests_get.return_value.ok = True
        mock_requests_get.return_value.json.side_effect = [
            f"Created resource/new/{random.randint(100, 1000)}"  # nosec: [B311]
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
    assert len(campaign_creation_team.recommended_modifications_and_answer_list) > 0  # nosec: [B101]

    last_message = campaign_creation_team.get_last_message()
    return last_message


_client_system_messages = """You are a client who wants to create a ne google ads campaign (with ads and keywords).
You are in a conversation with a team of experts who will help you create a new google ads campaign.
Use their smart suggestions to guide you through the process.

Your answers should be short and to the point.
e.g.
I want to create new campaign.
I accept the suggestion.
Yes
"""


def continue_conversation_until_finished(
    user_id: int,
    conv_id: int,
    mock_create_ad_group_ad: Any,
    cache: Cache,
) -> None:
    while True:
        current_team = Team.get_team(user_id=user_id, conv_id=conv_id)
        current_team.toolbox._context.waiting_for_client_response = False  # type: ignore[union-attr]
        if not isinstance(current_team, Team):
            raise ValueError(
                f"Team with user_id {user_id} and conv_id {conv_id} not found."
            )
        num_messages = len(current_team.get_messages())
        if (
            num_messages < current_team.max_round
            and mock_create_ad_group_ad.call_count == 0
        ):
            customers_response = get_client_response_for_the_team_conv(
                user_id=user_id,
                conv_id=conv_id,
                message=current_team.get_last_message(),
                cache=cache,
                client_system_message=_client_system_messages,
            )
            current_team.continue_chat(message=customers_response)
        else:
            break


def benchmark_campaign_creation(
    url: str,
    llm: str = Models.gpt4o,
) -> Tuple[str, int]:
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

                    continue_conversation_until_finished(
                        user_id=123,
                        conv_id=456,
                        mock_create_ad_group_ad=mock_create_ad_group_ad,
                        cache=cache,
                    )

            return run_assertions_and_return_last_message(
                campaign_creation_team=campaign_creation_team,
                mock_create_ad_group=mock_create_ad_group,
                mock_create_ad_group_ad=mock_create_ad_group_ad,
                mock_create_ad_group_keyword=mock_create_ad_group_keyword,
                mock_create_campaign=mock_create_campaign,
            ), campaign_creation_team.retry_from_scratch_counter
    finally:
        user_id, conv_id = campaign_creation_team.name.split("_")[-2:]
        success = Team.pop_team(user_id=int(user_id), conv_id=int(conv_id))
        assert success is not None  # nosec: [B101]
