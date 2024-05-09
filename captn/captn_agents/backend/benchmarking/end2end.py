from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Any, Iterator
from unittest.mock import patch

from autogen.cache import Cache

from ..teams import (
    BriefCreationTeam,
    Team,
)
from ..tools._brief_creation_team_tools import _change_the_team_and_start_new_chat
from .brief_creation_team import _client_system_messages, _get_task
from .helpers import get_client_response, get_config_list
from .models import Models

URLS = [
    "https://www.ikea.com/gb/en/",
    "https://www.disneystore.eu",
    "https://www.hamleys.com/",
    "https://www.konzum.hr",
    "https://faststream.airt.ai",
]


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
                team=team, cache=cache, client_system_message=client_system_message
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
    team_name: str,
    llm: str = Models.gpt4,
) -> str:
    config_list = get_config_list(llm)

    user_id = 123
    conv_id = 234
    task = _get_task(url)
    team = BriefCreationTeam(
        task=task, user_id=user_id, conv_id=conv_id, config_list=config_list
    )
    client_system_message = _client_system_messages[team_name]

    try:
        with TemporaryDirectory() as cache_dir:
            with Cache.disk(cache_path_root=cache_dir) as cache:
                with _patch_brief_creation_team_vars(
                    team=team, client_system_message=client_system_message, cache=cache
                ) as mock_change_the_team_and_start_new_chat:
                    team.initiate_chat(cache=cache)

                    mock_change_the_team_and_start_new_chat.assert_called()
                    team_class: Team = (
                        mock_change_the_team_and_start_new_chat.call_args.kwargs[
                            "team_class"
                        ]
                    )
                    assert team_class.get_registred_team_name() == team_name  # nosec: [B101]

                    return "Change later"
    finally:
        poped_team = Team.pop_team(user_id=user_id, conv_id=conv_id)
        assert isinstance(poped_team, Team)  # nosec: [B101]
