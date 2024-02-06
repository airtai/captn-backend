import random
import unittest.mock
from datetime import datetime
from typing import Optional

from autogen.cache import Cache

from captn.captn_agents.backend.daily_analysis_team import (
    REACT_APP_API_URL,
    DailyAnalysisTeam,
    Metrics,
    _get_conv_id_and_send_email,
    calculate_metrics_change,
    execute_daily_analysis,
    get_ad_groups_report,
    get_campaigns_report,
    get_daily_ad_group_ads_report,
    get_daily_keywords_report,
    get_daily_report,
    get_daily_report_for_customer,
)
from captn.captn_agents.backend.team import Team

execute_query_return_value = "{'1122': [{'campaign': {'resourceName': 'customers/2324127278/campaigns/20761810762', 'name': 'Website traffic-Search-3-updated-up', 'id': '20761810762'}, 'adGroup': {'resourceName': 'customers/2324127278/adGroups/156261983518', 'id': '156261983518', 'name': 'fastapi get super-dooper-cool'}, 'metrics': {'clicks': '0', 'conversions': 0.0, 'costMicros': '0', 'impressions': '0', 'interactions': '0'}, 'adGroupAd': {'resourceName': 'customers/2324127278/adGroupAds/156261983518~688768033895', 'ad': {'resourceName': 'customers/2324127278/ads/688768033895', 'id': '688768033895'}}}, {'campaign': {'resourceName': 'customers/2324127278/campaigns/20978334367', 'name': 'Book-Shop1', 'id': '20978334367'}, 'adGroup': {'resourceName': 'customers/2324127278/adGroups/161283342474', 'id': '161283342474', 'name': 'Books Bestsellers'}, 'metrics': {'clicks': '0', 'conversions': 0.0, 'costMicros': '0', 'impressions': '0', 'interactions': '0'}, 'adGroupAd': {'resourceName': 'customers/2324127278/adGroupAds/161283342474~689256163801', 'ad': {'resourceName': 'customers/2324127278/ads/689256163801', 'id': '689256163801'}}}]}"


def test_metrics() -> None:
    metrics1 = Metrics(
        impressions=402,
        clicks=121,
        interactions=129,
        conversions=15,
        cost_micros=129000,
    )
    metrics2 = Metrics(
        impressions=433,
        clicks=100,
        interactions=135,
        conversions=21,
        cost_micros=153000,
    )
    metrics_new = calculate_metrics_change(metrics1, metrics2)
    excepted = Metrics(
        impressions=402,
        clicks=121,
        interactions=129,
        conversions=15,
        cost_micros=129000,
        impressions_increase=7.71,
        clicks_increase=-17.36,
        interactions_increase=4.65,
        conversions_increase=40.0,
        cost_micros_increase=18.6,
    )
    assert excepted == metrics_new


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

        expected = {
            "688768033895": {
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
                    "impressions_increase": None,
                    "clicks_increase": None,
                    "interactions_increase": None,
                    "conversions_increase": None,
                    "cost_micros_increase": None,
                },
            },
            "689256163801": {
                "ad_id": "689256163801",
                "campaign": {"id": "20978334367", "name": "Book-Shop1"},
                "ad_group": {"id": "161283342474", "name": "Books Bestsellers"},
                "metrics": {
                    "impressions": 0,
                    "clicks": 0,
                    "interactions": 0,
                    "conversions": 0,
                    "cost_micros": 0,
                    "impressions_increase": None,
                    "clicks_increase": None,
                    "interactions_increase": None,
                    "conversions_increase": None,
                    "cost_micros_increase": None,
                },
            },
        }
        assert len(expected) == len(daily_ad_group_ads_report)
        for key in expected.keys():
            assert expected[key] == daily_ad_group_ads_report[key].model_dump()


execute_query_return_value2 = "{'1122': [{'campaign': {'resourceName': 'customers/2324127278/campaigns/20761810762', 'name': 'Website traffic-Search-3-updated-up', 'id': '20761810762'}, 'adGroup': {'resourceName': 'customers/2324127278/adGroups/156261983518', 'id': '156261983518', 'name': 'fastapi get super-dooper-cool'}, 'metrics': {'clicks': '1', 'conversions': 3, 'costMicros': '0', 'impressions': '0', 'interactions': '5'}, 'adGroupAd': {'resourceName': 'customers/2324127278/adGroupAds/156261983518~688768033895', 'ad': {'resourceName': 'customers/2324127278/ads/688768033895', 'id': '688768033895'}}}, {'campaign': {'resourceName': 'customers/2324127278/campaigns/20978334367', 'name': 'Book-Shop1', 'id': '20978334367'}, 'adGroup': {'resourceName': 'customers/2324127278/adGroups/161283342474', 'id': '161283342474', 'name': 'Books Bestsellers'}, 'metrics': {'clicks': '0', 'conversions': 0.0, 'costMicros': '0', 'impressions': '0', 'interactions': '0'}, 'adGroupAd': {'resourceName': 'customers/2324127278/adGroupAds/161283342474~689256163801', 'ad': {'resourceName': 'customers/2324127278/ads/689256163801', 'id': '689256163801'}}}]}"
execute_query_return_value3 = "{'1122': [{'campaign': {'resourceName': 'customers/2324127278/campaigns/20761810762', 'name': 'Website traffic-Search-3-updated-up', 'id': '20761810762'}, 'adGroup': {'resourceName': 'customers/2324127278/adGroups/156261983518', 'id': '156261983518', 'name': 'fastapi get super-dooper-cool'}, 'metrics': {'clicks': '2', 'conversions': 2, 'costMicros': '0', 'impressions': '0', 'interactions': '5'}, 'adGroupAd': {'resourceName': 'customers/2324127278/adGroupAds/156261983518~688768033895', 'ad': {'resourceName': 'customers/2324127278/ads/688768033895', 'id': '688768033895'}}}]}"


def test_get_daily_report_for_customer() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.side_effect = [
            execute_query_return_value2,
            execute_query_return_value3,
        ]

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
                        "clicks": 1,
                        "interactions": 5,
                        "conversions": 3,
                        "cost_micros": 0,
                        "impressions_increase": None,
                        "clicks_increase": 100.0,
                        "interactions_increase": 0.0,
                        "conversions_increase": -33.33,
                        "cost_micros_increase": None,
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
                        "impressions_increase": None,
                        "clicks_increase": None,
                        "interactions_increase": None,
                        "conversions_increase": None,
                        "cost_micros_increase": None,
                    },
                },
            ],
        }

        # print(daily_report_for_customer.model_dump())
        assert excepted == daily_report_for_customer.model_dump()


def test_get_daily_report() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.execute_query"
    ) as mock_execute_query:
        with unittest.mock.patch(
            "captn.captn_agents.backend.daily_analysis_team.list_accessible_customers"
        ) as mock_list_accessible_customers:
            mock_list_accessible_customers.return_value = ["1122"]
            mock_execute_query.side_effect = [
                execute_query_return_value2,
                execute_query_return_value3,
            ]
            daily_report = get_daily_report(user_id=1, conv_id=1)
            excepted = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "1122",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 0,\n            "clicks": 1,\n            "interactions": 5,\n            "conversions": 3,\n            "cost_micros": 0,\n            "impressions_increase": null,\n            "clicks_increase": 100.0,\n            "interactions_increase": 0.0,\n            "conversions_increase": -33.33,\n            "cost_micros_increase": null\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 0,\n            "clicks": 0,\n            "interactions": 0,\n            "conversions": 0,\n            "cost_micros": 0,\n            "impressions_increase": null,\n            "clicks_increase": null,\n            "interactions_increase": null,\n            "conversions_increase": null,\n            "cost_micros_increase": null\n          }\n        }\n      ]\n    }\n  ]\n}'
            assert excepted == daily_report


def test_get_daily_keyword_report() -> None:
    get_daily_keywords_report(
        user_id=1, conv_id=1, customer_id="2324127278", date="2024-01-29"
    )


def test_get_campaigns_report() -> None:
    get_campaigns_report(
        user_id=1, conv_id=1, customer_id="2324127278", date="2024-01-29"
    )


def test_get_ad_groups_report() -> None:
    get_ad_groups_report(
        user_id=1, conv_id=1, customer_id="2324127278", date="2024-01-29"
    )


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

                    return_value1 = '{\n  "daily_customer_reports": [\n    {\n      "customer_id": "2324127278",\n      "daily_ad_group_ads_report": [\n        {\n          "ad_id": "688768033895",\n          "campaign": {\n            "id": "20761810762",\n            "name": "Website traffic-Search-3-updated-up"\n          },\n          "ad_group": {\n            "id": "156261983518",\n            "name": "fastapi get super-dooper-cool"\n          },\n          "metrics": {\n            "impressions": 402,\n            "clicks": 121,\n            "interactions": 129,\n            "conversions": 15,\n            "cost_micros": 129000,\n            "impressions_increase": 22.3,\n            "clicks_increase": 11.2,\n            "interactions_increase": 12.1,\n            "conversions_increase": 5.21,\n            "cost_micros_increase": null\n          }\n        },\n        {\n          "ad_id": "689256163801",\n          "campaign": {\n            "id": "20978334367",\n            "name": "Book-Shop1"\n          },\n          "ad_group": {\n            "id": "161283342474",\n            "name": "Books Bestsellers"\n          },\n          "metrics": {\n            "impressions": 159,\n            "clicks": 22,\n            "interactions": 25,\n            "conversions": 6,\n            "cost_micros": 22000,\n            "impressions_increase": -12.2,\n            "clicks_increase": -20.44,\n            "interactions_increase": -19.21,\n            "conversions_increase": -9.9,\n            "cost_micros_increase": -5.5\n          }\n        }\n      ]\n    }\n  ]\n}'

                    mock_daily_report.side_effect = [return_value1]  # , return_value2]
                    mock_datetime.today.return_value = datetime(2021, 1, 1)

                    daily_analysis_team.initiate_chat()

    mock_daily_report.assert_called()

    team_name = daily_analysis_team.name
    # last_message = daily_analysis_team.get_last_message(add_prefix=False)
    Team.pop_team(team_name=team_name)


def _test_execute_daily_analysis(task: Optional[str] = None) -> None:
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


def test_execute_daily_analysis() -> None:
    current_date = "2024-01-30"
    task = f"""
Current date is: {current_date}.
Execute daily analysis (get_daily_report )and without any further analysis send the report to the client. (you can exchange maximum 5 messages between the team!!)
You need to propose at least 3 next steps to the client. (What ever pops up in your mind)
"""
    _test_execute_daily_analysis(task=task)


def test_execute_daily_analysis_original() -> None:
    _test_execute_daily_analysis()


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
