from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Any, Iterator, Tuple
from unittest.mock import patch

from autogen.cache import Cache

from ..teams import (
    BriefCreationTeam,
    CampaignCreationTeam,
    Team,
)
from ..tools._brief_creation_team_tools import (
    _change_the_team_and_start_new_chat,
)
from .brief_creation_team import _client_system_messages, _get_task
from .campaign_creation_team import (
    _patch_campaign_creation_team_vars,
    continue_conversation_until_finished,
    run_assertions_and_return_last_message,
)
from .helpers import get_client_response, get_config_list
from .models import Models


@contextmanager
def _patch_brief_creation_team_vars(
    team: BriefCreationTeam,
    client_system_message: str,
    cache: Cache,
) -> Iterator[Any]:
    with (
        patch.object(
            team.toolbox.functions,
            "reply_to_client",
            wraps=get_client_response(
                user_id=team.user_id,
                conv_id=team.conv_id,
                cache=cache,
                client_system_message=client_system_message,
            ),
        ),
        patch(
            "captn.captn_agents.backend.tools._brief_creation_team_tools._change_the_team_and_start_new_chat",
            wraps=_change_the_team_and_start_new_chat,
        ) as mock_change_the_team_and_start_new_chat,
    ):
        yield mock_change_the_team_and_start_new_chat


def benchmark_end2end(
    url: str,
    llm: str = Models.gpt4o,
) -> Tuple[str, int]:
    config_list = get_config_list(llm)

    user_id = 123
    conv_id = 234
    task = _get_task(url)
    brief_creation_team = BriefCreationTeam(
        task=task, user_id=user_id, conv_id=conv_id, config_list=config_list
    )

    team_name = "campaign_creation_team"
    client_system_message = _client_system_messages[team_name]

    try:
        with TemporaryDirectory() as cache_dir:
            with Cache.disk(cache_path_root=cache_dir) as cache:
                with _patch_brief_creation_team_vars(
                    team=brief_creation_team,
                    client_system_message=client_system_message,
                    cache=cache,
                ) as mock_change_the_team_and_start_new_chat:
                    with _patch_campaign_creation_team_vars() as (
                        mock_create_ad_group,
                        mock_create_ad_group_ad,
                        mock_create_ad_group_keyword,
                        mock_create_campaign,
                    ):
                        brief_creation_team.initiate_chat(cache=cache)
                        continue_conversation_until_finished(
                            user_id=user_id,
                            conv_id=conv_id,
                            mock_create_ad_group_ad=mock_create_ad_group_ad,
                            cache=cache,
                        )

                        mock_change_the_team_and_start_new_chat.assert_called()
                        team_class: Team = (
                            mock_change_the_team_and_start_new_chat.call_args.kwargs[
                                "team_class"
                            ]
                        )
                        assert team_class.get_registred_team_name() == team_name  # nosec: [B101]
                        campaign_creation_team = Team.get_team(
                            user_id=user_id, conv_id=conv_id
                        )
                        assert isinstance(campaign_creation_team, CampaignCreationTeam)  # nosec: [B101]

                        return (
                            run_assertions_and_return_last_message(
                                campaign_creation_team=campaign_creation_team,
                                mock_create_ad_group=mock_create_ad_group,
                                mock_create_ad_group_ad=mock_create_ad_group_ad,
                                mock_create_ad_group_keyword=mock_create_ad_group_keyword,
                                mock_create_campaign=mock_create_campaign,
                            ),
                            brief_creation_team.retry_from_scratch_counter
                            + campaign_creation_team.retry_from_scratch_counter,
                        )
    finally:
        poped_team = Team.pop_team(user_id=user_id, conv_id=conv_id)
        assert isinstance(poped_team, CampaignCreationTeam)  # nosec: [B101]
