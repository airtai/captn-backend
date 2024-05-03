import unittest
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Any, Iterator, Tuple

from autogen.cache import Cache

from captn.captn_agents.backend.benchmarking.helpers import get_client_response
from captn.captn_agents.backend.teams import (
    BriefCreationTeam,
    Team,
)

from .fixtures.brief_creation_team_fixtures import (
    BRIEF_CREATION_TEAM_RESPONSE,
    WEB_PAGE_SUMMARY_IKEA,
)

__all__ = ("run_end2end_correct_team_choosed",)


url_web_page_summary_dict = {
    "https://www.ikea.com/gb/en/": WEB_PAGE_SUMMARY_IKEA,
}


@contextmanager
def _patch_vars(
    url: str,
    team: BriefCreationTeam,
    client_system_message: str,
    cache: Cache,
) -> Iterator[Tuple[Any, Any, Any, Any]]:
    with (
        unittest.mock.patch.object(  # type: ignore[attr-defined]
            team.toolbox.functions,
            "reply_to_client",
            wraps=get_client_response(
                team=team, cache=cache, client_system_message=client_system_message
            ),
        ) as mock_reply_to_client,
        unittest.mock.patch(  # type: ignore[attr-defined]
            "captn.captn_agents.backend.tools._brief_creation_team_tools._get_info_from_the_web_page_original",
            return_value=url_web_page_summary_dict[url],
        ) as mock_get_info_from_the_web_page,
        unittest.mock.patch(  # type: ignore[attr-defined]
            "captn.captn_agents.backend.tools._brief_creation_team_tools._change_the_team_and_start_new_chat",
            return_value=BRIEF_CREATION_TEAM_RESPONSE,
        ) as mock_change_the_team_and_start_new_chat,
        unittest.mock.patch.object(  # type: ignore[attr-defined]
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


def _get_task(url: str) -> str:
    return f"""Business: Boost sales / Increase brand awareness
Goal: Increase brand awareness and boost sales
Current Situation: Website: {url}, Digital Marketing: Yes, Using Google Ads
Website: {url}
Digital Marketing Objectives: Increase brand awareness, Boost sales
Next Steps: First step is to get the summary of the Website.
Any Other Information Related to Customer Brief: None"""


_client_system_messages = {
    "campaign_creation_team": """You are a client who wants to create a ne google ads campaign.
You are in a conversation with a team of experts who will help you create a new google ads campaign.
Use their smart suggestions to guide you through the process.

Your answers should be short and to the point.
e.g.
I want to create new campaign.
I accept the suggestion.
Yes
""",
    "default_team": """You are a client who wants to optimize existing google ads campaign.
You are in a conversation with a team of experts who will help you optimize your google ads.
Use their smart suggestions to guide you through the process.

Your answers should be short and to the point.
e.g.
I want to optimize existing campaign.
I accept the suggestion.
Yes
""",
}


def run_end2end_correct_team_choosed(
    url: str,
    team_name: str = "campaign_creation_team",
) -> None:
    user_id = 123
    conv_id = 234
    task = _get_task(url)
    team = BriefCreationTeam(task=task, user_id=user_id, conv_id=conv_id)
    client_system_message = _client_system_messages[team_name]
    try:
        with TemporaryDirectory() as cache_dir:
            with Cache.disk(cache_path_root=cache_dir) as cache:
                with _patch_vars(
                    url=url,
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
                    assert team_class.get_registred_team_name() == team_name  # nosec: [B101]

    finally:
        poped_team = Team.pop_team(user_id=user_id, conv_id=conv_id)
        assert isinstance(poped_team, Team)  # nosec: [B101]
