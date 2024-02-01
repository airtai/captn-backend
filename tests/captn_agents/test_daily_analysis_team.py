import random
import unittest.mock
from datetime import datetime

from autogen.cache import Cache

from captn.captn_agents.backend.daily_analysis_team import (
    REACT_APP_API_URL,
    DailyAnalysisTeam,
    _get_conv_id_and_send_email,
    execute_daily_analysis,
    get_daily_ad_group_ads_report,
    get_daily_report,
    get_daily_report_for_customer,
)
from captn.captn_agents.backend.team import Team

execute_query_return_value = "{'1122': [{'campaign': {'resourceName': 'customers/2324127278/campaigns/20761810762', 'name': 'Website traffic-Search-3-updated-up', 'id': '20761810762'}, 'adGroup': {'resourceName': 'customers/2324127278/adGroups/156261983518', 'id': '156261983518', 'name': 'fastapi get super-dooper-cool'}, 'metrics': {'clicks': '0', 'conversions': 0.0, 'costMicros': '0', 'impressions': '0', 'interactions': '0'}, 'adGroupAd': {'resourceName': 'customers/2324127278/adGroupAds/156261983518~688768033895', 'ad': {'resourceName': 'customers/2324127278/ads/688768033895', 'id': '688768033895'}}}, {'campaign': {'resourceName': 'customers/2324127278/campaigns/20978334367', 'name': 'Book-Shop1', 'id': '20978334367'}, 'adGroup': {'resourceName': 'customers/2324127278/adGroups/161283342474', 'id': '161283342474', 'name': 'Books Bestsellers'}, 'metrics': {'clicks': '0', 'conversions': 0.0, 'costMicros': '0', 'impressions': '0', 'interactions': '0'}, 'adGroupAd': {'resourceName': 'customers/2324127278/adGroupAds/161283342474~689256163801', 'ad': {'resourceName': 'customers/2324127278/ads/689256163801', 'id': '689256163801'}}}]}"


def test_get_daily_ad_group_ads_report() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.return_value = execute_query_return_value
        daily_ad_group_ads_report = get_daily_ad_group_ads_report(
            user_id=1,
            conv_id=1,
            customer_id="1122",
            date="2021-01-01",
        )

        expected = [
            {
                "ad_id": "688768033895",
                "campaign": {
                    "id": "20761810762",
                    "name": "Website traffic-Search-3-updated-up",
                },
                "ad_group": {
                    "id": "156261983518",
                    "name": "fastapi get super-dooper-cool",
                },
                "metrics": {
                    "impressions": 0,
                    "clicks": 0,
                    "interactions": 0,
                    "conversions": 0,
                    "cost_micros": 0,
                },
            },
            {
                "ad_id": "689256163801",
                "campaign": {"id": "20978334367", "name": "Book-Shop1"},
                "ad_group": {"id": "161283342474", "name": "Books Bestsellers"},
                "metrics": {
                    "impressions": 0,
                    "clicks": 0,
                    "interactions": 0,
                    "conversions": 0,
                    "cost_micros": 0,
                },
            },
        ]
        assert len(expected) == len(daily_ad_group_ads_report)
        for i in range(len(expected)):
            assert expected[i] == daily_ad_group_ads_report[i].model_dump()


def test_get_daily_report_for_customer() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.return_value = execute_query_return_value

        daily_report_for_customer = get_daily_report_for_customer(
            user_id=1, conv_id=1, customer_id="1122", date="2021-01-01"
        )
        excepted = {
            "customer_id": "1122",
            "daily_ad_group_ads_report": [
                {
                    "ad_id": "688768033895",
                    "campaign": {
                        "id": "20761810762",
                        "name": "Website traffic-Search-3-updated-up",
                    },
                    "ad_group": {
                        "id": "156261983518",
                        "name": "fastapi get super-dooper-cool",
                    },
                    "metrics": {
                        "impressions": 0,
                        "clicks": 0,
                        "interactions": 0,
                        "conversions": 0,
                        "cost_micros": 0,
                    },
                },
                {
                    "ad_id": "689256163801",
                    "campaign": {"id": "20978334367", "name": "Book-Shop1"},
                    "ad_group": {"id": "161283342474", "name": "Books Bestsellers"},
                    "metrics": {
                        "impressions": 0,
                        "clicks": 0,
                        "interactions": 0,
                        "conversions": 0,
                        "cost_micros": 0,
                    },
                },
            ],
        }

        assert excepted == daily_report_for_customer.model_dump()


def test_get_daily_report() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.execute_query"
    ) as mock_execute_query:
        with unittest.mock.patch(
            "captn.captn_agents.backend.daily_analysis_team.list_accessible_customers"
        ) as mock_list_accessible_customers:
            mock_list_accessible_customers.return_value = ["1122"]
            mock_execute_query.return_value = execute_query_return_value
            daily_report = get_daily_report(user_id=1, conv_id=1)
            excepted = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "1122",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 0,\n            "clicks": 0,\n            "interactions": 0,\n            "conversions": 0,\n            "cost_micros": 0\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 0,\n            "clicks": 0,\n            "interactions": 0,\n            "conversions": 0,\n            "cost_micros": 0\n          }\n        }\n      ]\n    }\n  ]\n}'
            assert excepted == daily_report


def test_daily_analysis_team() -> None:
    # current_date = datetime.today().strftime("%Y-%m-%d")
    current_date = "2024-01-30"

    task = f"""
Current date is: {current_date}.
You need compare the ads performance between yesterday and the same day of the previous week (-7 days).
- Clicks
- Conversions
- Cost per click (display in customer local currency)

Check which ads have the highest cost and which have the highest number of conversions.
If for some reason thera are no recorded impressions/clicks/interactions/conversions for any of the ads across all campaigns try to identify the reason (bad positive/negative keywords etc).
At the end of the analysis, you need to suggest the next steps to the client. Usually, the next steps are:
- pause the ads with the highest cost and the lowest number of conversions.
- keywords analysis (add negative keywords, add positive keywords, change match type etc).
- ad copy analysis (change the ad copy, add more ads etc).
    """

    task = f"""
Current date is: {current_date}.
Execute daily analysis and immediately send the report to the client. (you can exchange maximum 5 messages between the team!!)
"""

    user_id = 1
    conv_id = random.randint(1, 100)
    daily_analysis_team = DailyAnalysisTeam(
        task=task,
        user_id=user_id,
        conv_id=conv_id,
    )

    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.get_daily_report"
    ) as mock_daily_report:
        with unittest.mock.patch(
            "captn.captn_agents.backend.daily_analysis_team.list_accessible_customers"
        ) as mock_list_accessible_customers:
            with unittest.mock.patch(
                "captn.captn_agents.backend.daily_analysis_team.datetime"
            ) as mock_datetime:
                with Cache.disk(cache_seed=42):
                    mock_list_accessible_customers.return_value = ["2324127278"]
                    return_value1 = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "2324127278",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 402,\n            "clicks": 121,\n            "interactions": 129,\n            "conversions": 15,\n            "cost_micros": 129000\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 53,\n            "clicks": 9,\n            "interactions": 9,\n            "conversions": 2,\n            "cost_micros": 1000\n          }\n        }\n      ]\n    }\n  ]\n}'
                    return_value2 = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "2324127278",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 433,\n            "clicks": 129,\n            "interactions": 135,\n            "conversions": 21,\n            "cost_micros": 153000\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 22,\n            "clicks": 3,\n            "interactions": 4,\n            "conversions": 1,\n            "cost_micros": 800\n          }\n        }\n      ]\n    }\n  ]\n}'

                    mock_daily_report.side_effect = [return_value1, return_value2]
                    mock_datetime.today.return_value = datetime(2021, 1, 1)

                    daily_analysis_team.initiate_chat()

    mock_daily_report.assert_called()

    team_name = daily_analysis_team.name
    # last_message = daily_analysis_team.get_last_message(add_prefix=False)
    Team.pop_team(team_name=team_name)


def test_execute_daily_analysis() -> None:
    current_date = "2024-01-30"

    task = f"""
Current date is: {current_date}.
Execute daily analysis (get_daily_report )and without any further analysis send the report to the client. (you can exchange maximum 5 messages between the team!!)
You need to propose at least 3 next steps to the client. (What ever pops up in your mind)
"""
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.get_daily_report"
    ) as mock_daily_report:
        with unittest.mock.patch(
            "captn.captn_agents.backend.daily_analysis_team.list_accessible_customers"
        ) as mock_list_accessible_customers:
            with unittest.mock.patch(
                "captn.captn_agents.backend.daily_analysis_team.datetime"
            ) as mock_datetime:
                with Cache.disk(cache_seed=42):
                    mock_list_accessible_customers.return_value = ["2324127278"]
                    return_value1 = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "2324127278",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 402,\n            "clicks": 121,\n            "interactions": 129,\n            "conversions": 15,\n            "cost_micros": 129000\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 53,\n            "clicks": 9,\n            "interactions": 9,\n            "conversions": 2,\n            "cost_micros": 1000\n          }\n        }\n      ]\n    }\n  ]\n}'
                    return_value2 = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "2324127278",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 433,\n            "clicks": 129,\n            "interactions": 135,\n            "conversions": 21,\n            "cost_micros": 153000\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 22,\n            "clicks": 3,\n            "interactions": 4,\n            "conversions": 1,\n            "cost_micros": 800\n          }\n        }\n      ]\n    }\n  ]\n}'

                    mock_daily_report.side_effect = [return_value1, return_value2]
                    mock_datetime.today.return_value = datetime(2021, 1, 1)

                    execute_daily_analysis(task=task)


def test_send_email() -> None:
    with unittest.mock.patch("requests.post") as mock_post:
        with unittest.mock.patch(
            "captn.captn_agents.backend.daily_analysis_team.send_email_infobip"
        ) as mock_send_email_infobip:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {"chatID": 239}

            _get_conv_id_and_send_email(
                user_id=1,
                client_email="myemail@mail.com",
                messages="[{'content': 'test'}{content: 'test2'}]",
                initial_message_in_chat="test",
                proposed_user_action=["test1", "test2"],
            )

            post_data = {
                "userId": 1,
                "messages": "[{'content': 'test'}{content: 'test2'}]",
                "initial_message_in_chat": "test",
                "email_content": "<html></html>",
                "proposed_user_action": ["test1", "test2"],
            }

            mock_post.assert_called_once_with(
                f"{REACT_APP_API_URL}/captn-daily-analysis-webhook",
                json=post_data,
                timeout=60,
            )
            body_text = "Daily Analysis:\ntest\n\nProposed User Actions:\n1. test1 (http://localhost:3000/chat/239?selected_user_action=1)\n2. test2 (http://localhost:3000/chat/239?selected_user_action=2)\n"
            mock_send_email_infobip.assert_called_once_with(
                to_email="myemail@mail.com",
                from_email="info@airt.ai",
                subject="Captn.ai Daily Analysis",
                body_text=body_text,
            )
