import json
import unittest
from tempfile import TemporaryDirectory
from typing import Tuple

from autogen.cache import Cache

from ..teams import Team
from ..teams._weekly_analysis_team import (
    WeeklyAnalysisTeam,
    _create_task_message,
    _validate_conversation_and_send_email,
    construct_weekly_report_email_from_template,
)
from .helpers import get_config_list
from .models import Models

weekly_report = {
    "weekly_customer_reports": [
        {
            "customer_id": "2324127278",
            "currency": "USD",
            "campaigns": {
                "20761810762": {
                    "id": "20761810762",
                    "metrics": {
                        "clicks": 5,
                        "conversions": 0.0,
                        "cost_micros": 22222,
                        "impressions": 148,
                        "interactions": 10,
                        "clicks_increase": -42.86,
                        "conversions_increase": 0.0,
                        "cost_micros_increase": -32.94,
                        "impressions_increase": None,
                        "interactions_increase": 42.86,
                    },
                    "name": "Website traffic-Search-3-updated-up",
                    "ad_groups": {
                        "156261983518": {
                            "id": "156261983518",
                            "metrics": {},
                            "name": "fastapi get super-dooper-cool",
                            "keywords": {},
                            "ad_group_ads": {
                                "688768033895": {
                                    "id": "688768033895",
                                    "metrics": {},
                                    "final_urls": ["https://not-reachable.airt.ai/"],
                                }
                            },
                        },
                        "158468020535": {
                            "id": "158468020535",
                            "metrics": {},
                            "name": "TVs",
                            "keywords": {},
                            "ad_group_ads": {
                                "688768033895": {
                                    "id": "688768033895",
                                    "metrics": {},
                                    "final_urls": [
                                        "https://also-not-reachable.airt.ai/"
                                    ],
                                }
                            },
                        },
                    },
                },
                "20979579987": {
                    "id": "20979579987",
                    "metrics": {
                        "clicks": 0,
                        "conversions": 0.0,
                        "cost_micros": 0,
                        "impressions": 0,
                        "interactions": 0,
                        "clicks_increase": 0,
                        "conversions_increase": 0,
                        "cost_micros_increase": 0,
                        "impressions_increase": 0,
                        "interactions_increase": 0,
                    },
                    "name": "Empty",
                    "ad_groups": {},
                },
            },
        },
        {
            "customer_id": "7119828439",
            "currency": "EUR",
            "campaigns": {
                "20750580900": {
                    "id": "20750580900",
                    "metrics": {
                        "clicks": 10,
                        "conversions": 0.0,
                        "cost_micros": 2830000,
                        "impressions": 148,
                        "interactions": 10,
                        "clicks_increase": None,
                        "conversions_increase": 0.0,
                        "cost_micros_increase": -32.94,
                        "impressions_increase": None,
                        "interactions_increase": 42.86,
                    },
                    "name": "faststream-web-search",
                    "ad_groups": {
                        "155431182157": {
                            "id": "155431182157",
                            "metrics": {},
                            "name": "Ad group 1",
                            "keywords": {},
                            "ad_group_ads": {
                                "680002685922": {
                                    "id": "680002685922",
                                    "metrics": {},
                                    "final_urls": [
                                        "https://github.com/airtai/faststream"
                                    ],
                                }
                            },
                        }
                    },
                }
            },
        },
    ]
}


def benchmark_weekly_analysis(
    url: str = "currently_not_used",
    llm: str = Models.gpt4,
) -> Tuple[str, int]:
    date = "2024-04-14"
    (
        weekly_report_message,
        _,
    ) = construct_weekly_report_email_from_template(
        weekly_reports=weekly_report, date=date
    )

    task = _create_task_message(date, json.dumps(weekly_report), weekly_report_message)
    user_id = 123
    conv_id = 234

    config_list = get_config_list(llm)
    weekly_analysis_team = WeeklyAnalysisTeam(
        task=task, user_id=user_id, conv_id=conv_id, config_list=config_list
    )

    try:
        with (
            unittest.mock.patch.object(
                weekly_analysis_team.toolbox.functions,
                "list_accessible_customers",
                return_value=["1111"],
            ),
            unittest.mock.patch.object(
                weekly_analysis_team.toolbox.functions,
                "execute_query",
                return_value=(
                    "You have all the necessary details. Do not use the execute_query anymore."
                ),
            ),
            unittest.mock.patch.object(
                weekly_analysis_team.toolbox.functions,
                "send_email",
                wraps=weekly_analysis_team.toolbox.functions.send_email,  # type: ignore[attr-defined]
            ) as mock_send_email,
            unittest.mock.patch(
                "captn.captn_agents.backend.teams._weekly_analysis_team._update_chat_message_and_send_email",
                return_value=None,
            ) as mock_update_chat_message_and_send_email,
        ):
            with TemporaryDirectory() as cache_dir:
                with Cache.disk(cache_path_root=cache_dir) as cache:
                    weekly_analysis_team.initiate_chat(cache=cache)

            mock_send_email.assert_called_once()

            _validate_conversation_and_send_email(
                weekly_analysis_team=weekly_analysis_team,
                conv_uuid="fake_uuid",
                email="fake@email.com",
                weekly_report_message="fake_message",
                main_email_template="fake_template",
            )
            mock_update_chat_message_and_send_email.assert_called_once()

            last_message = weekly_analysis_team.get_last_message()
            return last_message, weekly_analysis_team.retry_from_scratch_counter

    finally:
        poped_team = Team.pop_team(user_id=user_id, conv_id=conv_id)
        assert isinstance(poped_team, Team)  # nosec: [B101]
