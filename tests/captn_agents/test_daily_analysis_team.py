import unittest.mock
from typing import Optional

from autogen.cache import Cache

from captn.captn_agents.backend.daily_analysis_team import (
    execute_daily_analysis,
)


def _test_execute_daily_analysis(date: Optional[str] = None) -> None:
    # with unittest.mock.patch(
    #     "captn.captn_agents.backend.daily_analysis_team.get_daily_report"
    # ) as mock_daily_report:
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.list_accessible_customers"
    ) as mock_list_accessible_customers:
        with unittest.mock.patch("requests.post") as mock_post:
            with unittest.mock.patch(
                "captn.captn_agents.backend.daily_analysis_team.send_email_infobip"
            ) as mock_send_email_infobip:
                with Cache.disk(cache_seed=42):
                    mock_list_accessible_customers.return_value = [
                        "2324127278",
                        "7119828439",
                    ]
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json = lambda: {"chatId": 239}
                    mock_send_email_infobip.return_value = None

                    execute_daily_analysis(
                        send_only_to_emails=["robert@airt.ai"], date=date
                    )
                    mock_send_email_infobip.assert_called_once()


def test_execute_daily_analysis() -> None:
    current_date = "2024-01-30"
    _test_execute_daily_analysis(date=current_date)


def test_delete_chat_webhook_if_daily_analysis_fails() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.get_login_url"
    ) as mock_get_login_url:
        with unittest.mock.patch(
            "captn.captn_agents.backend.daily_analysis_team._get_conv_id"
        ) as mock_get_conv_id:
            with unittest.mock.patch(
                "captn.captn_agents.backend.daily_analysis_team._delete_chat_webhook"
            ) as mock_delete_chat_webhook:
                mock_get_login_url.return_value = ValueError("Error")
                mock_get_conv_id.return_value = 239
                mock_delete_chat_webhook.return_value = None

                execute_daily_analysis(
                    send_only_to_emails=["robert@airt.ai"], date="2024-01-30"
                )

                mock_get_login_url.assert_called_once()
                mock_get_conv_id.assert_called_once()
                mock_delete_chat_webhook.assert_called_once()
