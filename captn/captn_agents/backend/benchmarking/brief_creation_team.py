from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Any, Iterator, Tuple
from unittest.mock import patch

from autogen.cache import Cache

from ..config import Config
from ..teams import (
    BriefCreationTeam,
    Team,
)
from .fixtures.brief_creation_team_fixtures import (
    BRIEF_CREATION_TEAM_RESPONSE,
    WEB_PAGE_SUMMARY_DISNEY,
    WEB_PAGE_SUMMARY_FASTSTREAM,
    WEB_PAGE_SUMMARY_HAMLEYS,
    WEB_PAGE_SUMMARY_IKEA,
    WEB_PAGE_SUMMARY_KONZUM,
)
from .helpers import get_client_response
from .models import Models

__all__ = (
    "benchmark_brief_creation",
    "URL_SUMMARY_DICT",
)


URL_SUMMARY_DICT = {
    "https://www.ikea.com/gb/en/": WEB_PAGE_SUMMARY_IKEA,
    "https://www.disneystore.eu": WEB_PAGE_SUMMARY_DISNEY,
    "https://www.hamleys.com/": WEB_PAGE_SUMMARY_HAMLEYS,
    "https://www.konzum.hr": WEB_PAGE_SUMMARY_KONZUM,
    "https://faststream.airt.ai": WEB_PAGE_SUMMARY_FASTSTREAM,
}


@contextmanager
def _patch_vars(
    url: str,
    team: BriefCreationTeam,
    client_system_message: str,
    cache: Cache,
) -> Iterator[Tuple[Any, Any, Any, Any]]:
    with (
        patch.object(
            team.toolbox.functions,
            "reply_to_client",
            wraps=get_client_response(
                team=team, cache=cache, client_system_message=client_system_message
            ),
        ) as mock_reply_to_client,
        patch(
            "captn.captn_agents.backend.tools._brief_creation_team_tools._get_info_from_the_web_page_original",
            return_value=URL_SUMMARY_DICT[url],
        ) as mock_get_info_from_the_web_page,
        patch(
            "captn.captn_agents.backend.tools._brief_creation_team_tools._change_the_team_and_start_new_chat",
            return_value=BRIEF_CREATION_TEAM_RESPONSE,
        ) as mock_change_the_team_and_start_new_chat,
        patch.object(
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


def benchmark_brief_creation(
    url: str,
    team_name: str,
    llm: str = Models.gpt3_5,
) -> str:
    config = Config()
    if llm == Models.gpt3_5:
        config_list = config.config_list_gpt_3_5
    elif llm == Models.gpt4:
        config_list = config.config_list_gpt_4
    else:
        raise ValueError(f"llm {llm} not supported")

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
                    # return "it's ok"
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

                    delegate_task_function_sugestion = team.get_messages()[-2]
                    assert "tool_calls" in delegate_task_function_sugestion  # nosec: [B101]

                    delegate_task_function_sugestion_function = (
                        delegate_task_function_sugestion["tool_calls"][0]["function"]
                    )
                    assert (
                        delegate_task_function_sugestion_function["name"]
                        == "delagate_task"
                    )  # nosec: [B101]

                    assert "arguments" in delegate_task_function_sugestion_function  # nosec: [B101]
                    assert (
                        "task" in delegate_task_function_sugestion_function["arguments"]
                    )  # nosec: [B101]

                    return delegate_task_function_sugestion_function["arguments"]  # type: ignore[no-any-return]
    finally:
        poped_team = Team.pop_team(user_id=user_id, conv_id=conv_id)
        assert isinstance(poped_team, Team)  # nosec: [B101]
