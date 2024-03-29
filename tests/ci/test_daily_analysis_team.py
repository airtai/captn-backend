import json
import re
import unittest.mock
from pathlib import Path

import pytest
from tenacity import RetryError

from captn.captn_agents.backend.teams._daily_analysis_team import (
    REACT_APP_API_URL,
    AdGroup,
    AdGroupAd,
    Campaign,
    Keyword,
    KeywordMetrics,
    Metrics,
    _add_metrics_message,
    _update_chat_message_and_send_email,
    _update_message_and_campaigns_template,
    calculate_metrics_change,
    compare_reports,
    construct_daily_report_email_from_template,
    execute_daily_analysis,
    get_campaigns_report,
    get_daily_ad_group_ads_report,
    get_daily_keywords_report,
    get_web_status_code_report_for_campaign,
    google_ads_api_call,
)
from captn.google_ads.client import ALREADY_AUTHENTICATED


def test_metrics() -> None:
    metrics1 = Metrics(
        impressions=402,
        clicks=121,
        interactions=129,
        conversions=0,
        cost_micros=129000,
    )
    metrics2 = Metrics(
        impressions=433,
        clicks=100,
        interactions=135,
        conversions=0,
        cost_micros=153000,
    )
    metrics_new = calculate_metrics_change(metrics1, metrics2)
    excepted = Metrics(
        impressions=402,
        clicks=121,
        interactions=129,
        conversions=0,
        cost_micros=129000,
        impressions_increase=-7.16,
        clicks_increase=21.0,
        interactions_increase=-4.44,
        conversions_increase=0.0,
        cost_micros_increase=-15.69,
    )
    assert excepted == metrics_new


def test_keywords_metrics() -> None:
    metrics1 = KeywordMetrics(
        impressions=402,
        clicks=121,
        interactions=129,
        conversions=0,
        cost_micros=129000,
        historical_quality_score=3,
        historical_landing_page_quality_score="BELOW_AVERAGE",
        historical_creative_quality_score="ABOVE_AVERAGE",
    )
    metrics2 = KeywordMetrics(
        impressions=433,
        clicks=100,
        interactions=135,
        conversions=0,
        cost_micros=153000,
        historical_quality_score=4,
        historical_landing_page_quality_score="BELOW_AVERAGE",
        historical_creative_quality_score="ABOVE_AVERAGE",
    )
    metrics_new = calculate_metrics_change(metrics1, metrics2)
    excepted = KeywordMetrics(
        impressions=402,
        clicks=121,
        interactions=129,
        conversions=0,
        cost_micros=129000,
        historical_quality_score=3,
        historical_landing_page_quality_score="BELOW_AVERAGE",
        historical_creative_quality_score="ABOVE_AVERAGE",
        impressions_increase=-7.16,
        clicks_increase=21.0,
        interactions_increase=-4.44,
        conversions_increase=0.0,
        cost_micros_increase=-15.69,
        historical_quality_score_increase=-25.0,
    )
    assert excepted == metrics_new


def test_get_daily_ad_group_ads_report() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._daily_analysis_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.return_value = str(
            {
                "2324127278": [
                    {
                        "adGroup": {
                            "resourceName": "customers/2324127278/adGroups/153796669090",
                            "id": "153796669090",
                        },
                        "metrics": {
                            "clicks": "0",
                            "conversions": 0.0,
                            "costMicros": "0",
                            "impressions": "0",
                            "interactions": "0",
                        },
                        "adGroupAd": {
                            "resourceName": "customers/2324127278/adGroupAds/153796669090~690015466453",
                            "ad": {
                                "resourceName": "customers/2324127278/ads/690015466453",
                                "id": "690015466453",
                                "finalUrls": ["http://www.example.com"],
                            },
                        },
                    },
                    {
                        "adGroup": {
                            "resourceName": "customers/2324127278/adGroups/156261983518",
                            "id": "156261983518",
                        },
                        "metrics": {
                            "clicks": "0",
                            "conversions": 0.0,
                            "costMicros": "0",
                            "impressions": "0",
                            "interactions": "0",
                        },
                        "adGroupAd": {
                            "resourceName": "customers/2324127278/adGroupAds/156261983518~688768033895",
                            "ad": {
                                "resourceName": "customers/2324127278/ads/688768033895",
                                "id": "688768033895",
                                "finalUrls": ["https://faststream.airt.ai/"],
                            },
                        },
                    },
                    {
                        "adGroup": {
                            "resourceName": "customers/2324127278/adGroups/161283342474",
                            "id": "161283342474",
                        },
                        "metrics": {
                            "clicks": "0",
                            "conversions": 0.0,
                            "costMicros": "0",
                            "impressions": "0",
                            "interactions": "0",
                        },
                        "adGroupAd": {
                            "resourceName": "customers/2324127278/adGroupAds/161283342474~689256163801",
                            "ad": {
                                "resourceName": "customers/2324127278/ads/689256163801",
                                "id": "689256163801",
                                "finalUrls": [
                                    "https://www.shopbookshop.com/collections/books"
                                ],
                            },
                        },
                    },
                    {
                        "adGroup": {
                            "resourceName": "customers/2324127278/adGroups/161283342474",
                            "id": "161283342474",
                        },
                        "metrics": {
                            "clicks": "0",
                            "conversions": 0.0,
                            "costMicros": "0",
                            "impressions": "0",
                            "interactions": "0",
                        },
                        "adGroupAd": {
                            "resourceName": "customers/2324127278/adGroupAds/161283342474~689694296577",
                            "ad": {
                                "resourceName": "customers/2324127278/ads/689694296577",
                                "id": "689694296577",
                                "finalUrls": [
                                    "https://www.shopbookshop.com/collections/furnishings"
                                ],
                            },
                        },
                    },
                ]
            }
        )
        daily_ad_group_ads_report = get_daily_ad_group_ads_report(
            user_id=1,
            conv_id=1,
            customer_id="2324127278",
            date="2024-01-29",
        )

        expected = {
            "153796669090": {
                "690015466453": AdGroupAd(
                    id="690015466453",
                    final_urls=["http://www.example.com"],
                    metrics=Metrics(
                        impressions=0,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                )
            },
            "156261983518": {
                "688768033895": AdGroupAd(
                    id="688768033895",
                    final_urls=["https://faststream.airt.ai/"],
                    metrics=Metrics(
                        impressions=0,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                )
            },
            "161283342474": {
                "689256163801": AdGroupAd(
                    id="689256163801",
                    final_urls=["https://www.shopbookshop.com/collections/books"],
                    metrics=Metrics(
                        impressions=0,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                ),
                "689694296577": AdGroupAd(
                    id="689694296577",
                    final_urls=["https://www.shopbookshop.com/collections/furnishings"],
                    metrics=Metrics(
                        impressions=0,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                ),
            },
        }
        assert expected == daily_ad_group_ads_report


def test_get_daily_keywords_report() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._daily_analysis_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.return_value = str(
            {
                "7119828439": [
                    {
                        "adGroup": {
                            "resourceName": "customers/7119828439/adGroups/155431182157",
                            "id": "155431182157",
                        },
                        "metrics": {
                            "historicalCreativeQualityScore": "ABOVE_AVERAGE",
                            "historicalLandingPageQualityScore": "BELOW_AVERAGE",
                            "clicks": "1",
                            "conversions": 0.0,
                            "costMicros": "890000",
                            "historicalQualityScore": "3",
                            "impressions": "8",
                            "interactions": "1",
                        },
                        "adGroupCriterion": {
                            "resourceName": "customers/7119828439/adGroupCriteria/155431182157~51919090",
                            "keyword": {"matchType": "BROAD", "text": "NATS"},
                            "criterionId": "51919090",
                        },
                        "keywordView": {
                            "resourceName": "customers/7119828439/keywordViews/155431182157~51919090"
                        },
                    },
                    {
                        "adGroup": {
                            "resourceName": "customers/7119828439/adGroups/155431182157",
                            "id": "155431182157",
                        },
                        "metrics": {
                            "historicalCreativeQualityScore": "ABOVE_AVERAGE",
                            "historicalLandingPageQualityScore": "BELOW_AVERAGE",
                            "clicks": "0",
                            "conversions": 0.0,
                            "costMicros": "0",
                            "historicalQualityScore": "3",
                            "impressions": "34",
                            "interactions": "0",
                        },
                        "adGroupCriterion": {
                            "resourceName": "customers/7119828439/adGroupCriteria/155431182157~302418213753",
                            "keyword": {"matchType": "BROAD", "text": "RabbitMQ"},
                            "criterionId": "302418213753",
                        },
                        "keywordView": {
                            "resourceName": "customers/7119828439/keywordViews/155431182157~302418213753"
                        },
                    },
                    {
                        "adGroup": {
                            "resourceName": "customers/7119828439/adGroups/155431182157",
                            "id": "155431182157",
                        },
                        "metrics": {
                            "historicalCreativeQualityScore": "ABOVE_AVERAGE",
                            "historicalLandingPageQualityScore": "BELOW_AVERAGE",
                            "clicks": "9",
                            "conversions": 0.0,
                            "costMicros": "1940000",
                            "historicalQualityScore": "3",
                            "impressions": "106",
                            "interactions": "9",
                        },
                        "adGroupCriterion": {
                            "resourceName": "customers/7119828439/adGroupCriteria/155431182157~340537812163",
                            "keyword": {"matchType": "BROAD", "text": "Apache Kafka"},
                            "criterionId": "340537812163",
                        },
                        "keywordView": {
                            "resourceName": "customers/7119828439/keywordViews/155431182157~340537812163"
                        },
                    },
                ]
            }
        )
        daily_keywords_report = get_daily_keywords_report(
            user_id=1, conv_id=1, customer_id="7119828439", date="2024-01-29"
        )

        expected = {
            "155431182157": {
                "51919090": Keyword(
                    id="51919090",
                    metrics=KeywordMetrics(
                        impressions=8,
                        clicks=1,
                        interactions=1,
                        conversions=0,
                        cost_micros=890000,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                        historical_quality_score=3,
                        historical_landing_page_quality_score="BELOW_AVERAGE",
                        historical_creative_quality_score="ABOVE_AVERAGE",
                    ),
                    text="NATS",
                    match_type="BROAD",
                ),
                "302418213753": Keyword(
                    id="302418213753",
                    metrics=KeywordMetrics(
                        impressions=34,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                        historical_quality_score=3,
                        historical_landing_page_quality_score="BELOW_AVERAGE",
                        historical_creative_quality_score="ABOVE_AVERAGE",
                    ),
                    text="RabbitMQ",
                    match_type="BROAD",
                ),
                "340537812163": Keyword(
                    id="340537812163",
                    metrics=KeywordMetrics(
                        impressions=106,
                        clicks=9,
                        interactions=9,
                        conversions=0,
                        cost_micros=1940000,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                        historical_quality_score=3,
                        historical_landing_page_quality_score="BELOW_AVERAGE",
                        historical_creative_quality_score="ABOVE_AVERAGE",
                    ),
                    text="Apache Kafka",
                    match_type="BROAD",
                ),
            }
        }
        assert expected == daily_keywords_report


def test_compare_reports() -> None:
    first_report = {
        "20750580900": Campaign(
            id="20750580900",
            name="faststream-web-search",
            ad_groups={
                "155431182157": AdGroup(
                    id="155431182157",
                    name="Ad group 1",
                    metrics=Metrics(
                        impressions=148,
                        clicks=10,
                        interactions=10,
                        conversions=0,
                        cost_micros=2830000,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                    keywords={
                        "51919090": Keyword(
                            id="51919090",
                            text="NATS",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=8,
                                clicks=1,
                                interactions=1,
                                conversions=0,
                                cost_micros=890000,
                                impressions_increase=None,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=None,
                                cost_micros_increase=None,
                            ),
                        ),
                        "302418213753": Keyword(
                            id="302418213753",
                            text="RabbitMQ",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=34,
                                clicks=0,
                                interactions=0,
                                conversions=0,
                                cost_micros=0,
                                impressions_increase=None,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=None,
                                cost_micros_increase=None,
                            ),
                        ),
                        "340537812163": Keyword(
                            id="340537812163",
                            text="Apache Kafka",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=106,
                                clicks=9,
                                interactions=9,
                                conversions=0,
                                cost_micros=1940000,
                                impressions_increase=None,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=None,
                                cost_micros_increase=None,
                            ),
                        ),
                    },
                    ad_group_ads={
                        "680002685922": AdGroupAd(
                            id="680002685922",
                            final_urls=["https://github.com/airtai/faststream"],
                            metrics=Metrics(
                                impressions=148,
                                clicks=10,
                                interactions=10,
                                conversions=0,
                                cost_micros=2830000,
                                impressions_increase=None,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=None,
                                cost_micros_increase=None,
                            ),
                        )
                    },
                )
            },
            metrics=Metrics(
                impressions=148,
                clicks=10,
                interactions=10,
                conversions=0,
                cost_micros=2830000,
                impressions_increase=None,
                clicks_increase=None,
                interactions_increase=None,
                conversions_increase=None,
                cost_micros_increase=None,
            ),
        )
    }
    second_report = {
        "20750580900": Campaign(
            id="20750580900",
            name="faststream-web-search",
            ad_groups={
                "155431182157": AdGroup(
                    id="155431182157",
                    name="Ad group 1",
                    metrics=Metrics(
                        impressions=114,
                        clicks=7,
                        interactions=7,
                        conversions=0,
                        cost_micros=4220000,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                    keywords={
                        "51919090": Keyword(
                            id="51919090",
                            text="NATS",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=3,
                                clicks=0,
                                interactions=0,
                                conversions=0,
                                cost_micros=0,
                                impressions_increase=None,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=None,
                                cost_micros_increase=None,
                            ),
                        ),
                        "302418213753": Keyword(
                            id="302418213753",
                            text="RabbitMQ",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=13,
                                clicks=2,
                                interactions=2,
                                conversions=0,
                                cost_micros=70000,
                                impressions_increase=None,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=None,
                                cost_micros_increase=None,
                            ),
                        ),
                        "340537812163": Keyword(
                            id="340537812163",
                            text="Apache Kafka",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=98,
                                clicks=5,
                                interactions=5,
                                conversions=0,
                                cost_micros=4150000,
                                impressions_increase=None,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=None,
                                cost_micros_increase=None,
                            ),
                        ),
                    },
                    ad_group_ads={
                        "680002685922": AdGroupAd(
                            id="680002685922",
                            final_urls=["https://github.com/airtai/faststream"],
                            metrics=Metrics(
                                impressions=114,
                                clicks=7,
                                interactions=7,
                                conversions=0,
                                cost_micros=4220000,
                                impressions_increase=None,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=None,
                                cost_micros_increase=None,
                            ),
                        )
                    },
                )
            },
            metrics=Metrics(
                impressions=114,
                clicks=7,
                interactions=7,
                conversions=0,
                cost_micros=4220000,
                impressions_increase=None,
                clicks_increase=None,
                interactions_increase=None,
                conversions_increase=None,
                cost_micros_increase=None,
            ),
        )
    }

    compared_campaigns_report = compare_reports(first_report, second_report)
    expected = {
        "20750580900": Campaign(
            id="20750580900",
            name="faststream-web-search",
            ad_groups={
                "155431182157": AdGroup(
                    id="155431182157",
                    name="Ad group 1",
                    metrics=Metrics(
                        impressions=148,
                        clicks=10,
                        interactions=10,
                        conversions=0,
                        cost_micros=2830000,
                        impressions_increase=29.82,
                        clicks_increase=42.86,
                        interactions_increase=42.86,
                        conversions_increase=0.0,
                        cost_micros_increase=-32.94,
                    ),
                    keywords={
                        "51919090": Keyword(
                            id="51919090",
                            text="NATS",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=8,
                                clicks=1,
                                interactions=1,
                                conversions=0,
                                cost_micros=890000,
                                impressions_increase=166.67,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=0.0,
                                cost_micros_increase=None,
                            ),
                        ),
                        "302418213753": Keyword(
                            id="302418213753",
                            text="RabbitMQ",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=34,
                                clicks=0,
                                interactions=0,
                                conversions=0,
                                cost_micros=0,
                                impressions_increase=161.54,
                                clicks_increase=None,
                                interactions_increase=None,
                                conversions_increase=0.0,
                                cost_micros_increase=None,
                            ),
                        ),
                        "340537812163": Keyword(
                            id="340537812163",
                            text="Apache Kafka",
                            match_type="BROAD",
                            metrics=KeywordMetrics(
                                impressions=106,
                                clicks=9,
                                interactions=9,
                                conversions=0,
                                cost_micros=1940000,
                                impressions_increase=8.16,
                                clicks_increase=80.0,
                                interactions_increase=80.0,
                                conversions_increase=0.0,
                                cost_micros_increase=-53.25,
                            ),
                        ),
                    },
                    ad_group_ads={
                        "680002685922": AdGroupAd(
                            id="680002685922",
                            final_urls=["https://github.com/airtai/faststream"],
                            metrics=Metrics(
                                impressions=148,
                                clicks=10,
                                interactions=10,
                                conversions=0,
                                cost_micros=2830000,
                                impressions_increase=29.82,
                                clicks_increase=42.86,
                                interactions_increase=42.86,
                                conversions_increase=0.0,
                                cost_micros_increase=-32.94,
                            ),
                        )
                    },
                )
            },
            metrics=Metrics(
                impressions=148,
                clicks=10,
                interactions=10,
                conversions=0,
                cost_micros=2830000,
                impressions_increase=29.82,
                clicks_increase=42.86,
                interactions_increase=42.86,
                conversions_increase=0.0,
                cost_micros_increase=-32.94,
            ),
        )
    }
    assert expected == compared_campaigns_report


def test_get_campaigns_report() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._daily_analysis_team.execute_query"
    ) as mock_execute_query:
        # mock get_ad_groups_report
        with unittest.mock.patch(
            "captn.captn_agents.backend.teams._daily_analysis_team.get_ad_groups_report"
        ) as mock_get_ad_groups_report:
            mock_execute_query.return_value = str(
                {
                    "2324127278": [
                        {
                            "campaign": {
                                "resourceName": "customers/2324127278/campaigns/20750935821",
                                "name": "Search-1",
                                "id": "20750935821",
                            },
                            "metrics": {
                                "clicks": "0",
                                "conversions": 0.0,
                                "costMicros": "0",
                                "impressions": "0",
                                "interactions": "0",
                            },
                        },
                        {
                            "campaign": {
                                "resourceName": "customers/2324127278/campaigns/20761810762",
                                "name": "Website traffic-Search-3-updated-up",
                                "id": "20761810762",
                            },
                            "metrics": {
                                "clicks": "0",
                                "conversions": 0.0,
                                "costMicros": "0",
                                "impressions": "0",
                                "interactions": "0",
                            },
                        },
                        {
                            "campaign": {
                                "resourceName": "customers/2324127278/campaigns/20978334367",
                                "name": "Book-Shop1",
                                "id": "20978334367",
                            },
                            "metrics": {
                                "clicks": "0",
                                "conversions": 0.0,
                                "costMicros": "0",
                                "impressions": "0",
                                "interactions": "0",
                            },
                        },
                        {
                            "campaign": {
                                "resourceName": "customers/2324127278/campaigns/20979579987",
                                "name": "Empty",
                                "id": "20979579987",
                            },
                            "metrics": {
                                "clicks": "0",
                                "conversions": 0.0,
                                "costMicros": "0",
                                "impressions": "0",
                                "interactions": "0",
                            },
                        },
                    ]
                }
            )
            mock_get_ad_groups_report.return_value = {
                "153796669090": {
                    "690015466453": AdGroupAd(
                        id="690015466453",
                        final_urls=["http://www.example.com"],
                        metrics=Metrics(
                            impressions=0,
                            clicks=0,
                            interactions=0,
                            conversions=0,
                            cost_micros=0,
                            impressions_increase=None,
                            clicks_increase=None,
                            interactions_increase=None,
                            conversions_increase=None,
                            cost_micros_increase=None,
                        ),
                    )
                },
                "156261983518": {
                    "688768033895": AdGroupAd(
                        id="688768033895",
                        final_urls=["https://faststream.airt.ai/"],
                        metrics=Metrics(
                            impressions=0,
                            clicks=0,
                            interactions=0,
                            conversions=0,
                            cost_micros=0,
                            impressions_increase=None,
                            clicks_increase=None,
                            interactions_increase=None,
                            conversions_increase=None,
                            cost_micros_increase=None,
                        ),
                    )
                },
                "161283342474": {
                    "689256163801": AdGroupAd(
                        id="689256163801",
                        final_urls=["https://www.shopbookshop.com/collections/books"],
                        metrics=Metrics(
                            impressions=0,
                            clicks=0,
                            interactions=0,
                            conversions=0,
                            cost_micros=0,
                            impressions_increase=None,
                            clicks_increase=None,
                            interactions_increase=None,
                            conversions_increase=None,
                            cost_micros_increase=None,
                        ),
                    ),
                    "689694296577": AdGroupAd(
                        id="689694296577",
                        final_urls=[
                            "https://www.shopbookshop.com/collections/furnishings"
                        ],
                        metrics=Metrics(
                            impressions=0,
                            clicks=0,
                            interactions=0,
                            conversions=0,
                            cost_micros=0,
                            impressions_increase=None,
                            clicks_increase=None,
                            interactions_increase=None,
                            conversions_increase=None,
                            cost_micros_increase=None,
                        ),
                    ),
                },
            }

            campaigns_report = get_campaigns_report(
                user_id=1, conv_id=1, customer_id="2324127278", date="2024-01-29"
            )

            expected = {
                "20750935821": Campaign(
                    id="20750935821",
                    name="Search-1",
                    ad_groups={},
                    metrics=Metrics(
                        impressions=0,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                ),
                "20761810762": Campaign(
                    id="20761810762",
                    name="Website traffic-Search-3-updated-up",
                    ad_groups={},
                    metrics=Metrics(
                        impressions=0,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                ),
                "20978334367": Campaign(
                    id="20978334367",
                    name="Book-Shop1",
                    ad_groups={},
                    metrics=Metrics(
                        impressions=0,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                ),
                "20979579987": Campaign(
                    id="20979579987",
                    name="Empty",
                    ad_groups={},
                    metrics=Metrics(
                        impressions=0,
                        clicks=0,
                        interactions=0,
                        conversions=0,
                        cost_micros=0,
                        impressions_increase=None,
                        clicks_increase=None,
                        interactions_increase=None,
                        conversions_increase=None,
                        cost_micros_increase=None,
                    ),
                ),
            }
            assert expected == campaigns_report


daily_report = {
    "daily_customer_reports": [
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


def test_get_web_status_code_report_for_campaign() -> None:
    campaign = {
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
                        "final_urls": ["https://airt.ai/bad"],
                    }
                },
            },
        },
    }
    customer_id = "2324127278"
    warning_message, _ = get_web_status_code_report_for_campaign(campaign, customer_id)
    expected = """<li><strong>WARNING:</strong>Some final URLs for your Ads are not reachable:
<ul>
<li>Final url <a href='https://not-reachable.airt.ai/' target='_blank'>https://not-reachable.airt.ai/</a> used in Ad <a href='https://ads.google.com/aw/ads/edit/search?adId=688768033895&adGroupIdForAd=156261983518&__e=2324127278' target='_blank'>688768033895</a> is <strong>not reachable</strong></li>
<li>Final url <a href='https://airt.ai/bad' target='_blank'>https://airt.ai/bad</a> used in Ad <a href='https://ads.google.com/aw/ads/edit/search?adId=688768033895&adGroupIdForAd=158468020535&__e=2324127278' target='_blank'>688768033895</a> is <strong>not reachable</strong></li>
</ul>
</li>\n"""
    assert expected == warning_message


def test_add_metrics_message_for_positive_increase() -> None:
    result = _add_metrics_message(
        metrics={"clicks": 5, "clicks_increase": 10.4},
        title="Campaign",
        field="clicks",
        currency="",
    )
    excepted = ("<li>Campaign: 5 (+10.4%)</li>", "5", "+10.4%")
    assert excepted == result


def test_add_metrics_message_for_negative_increase() -> None:
    result = _add_metrics_message(
        metrics={"conversions": 5, "conversions_increase": -10.4},
        title="Conversions",
        field="conversions",
        currency="",
    )
    excepted = ("<li>Conversions: 5 (-10.4%)</li>", "5", "-10.4%")
    assert excepted == result


def test_add_metrics_message_when_increase_is_none() -> None:
    result = _add_metrics_message(
        metrics={"conversions": 5, "conversions_increase": None},
        title="Conversions",
        field="conversions",
        currency="",
    )
    excepted = ("<li>Conversions: 5</li>", "5", "-")
    assert excepted == result


def test_update_message_and_campaigns_template() -> None:
    campaigns_template = "{conversions} - {conversions_change_rate}"

    message, updated_template = _update_message_and_campaigns_template(
        metrics={"conversions": 5, "conversions_increase": 10.5},
        title="Conversions",
        field="conversions",
        currency="",
        message="Initial",
        campaigns_template=campaigns_template,
    )
    assert "Initial<li>Conversions: 5 (+10.5%)</li>" == message
    assert "5 - +10.5%" == updated_template


def test_construct_daily_report_email_from_template() -> None:
    message, main_email_template = construct_daily_report_email_from_template(
        daily_report, date="2024-02-05"
    )
    excepted_message = """<h2>Daily Google Ads Performance Report - 2024-02-05</h2><p>We're here with your daily analysis of your Google Ads campaigns for 2024-02-05. Below, you'll find insights into your campaign performances, along with notable updates and recommendations for optimization.</p><p>Customer <strong>2324127278</strong></p><ul><li>Campaign <strong><a href='https://ads.google.com/aw/campaigns?campaignId=20761810762&__e=2324127278' target='_blank'>Website traffic-Search-3-updated-up</a></strong><ul><li>Clicks: 5 (-42.86%)</li><li>Conversions: 0.0 (+0.0%)</li><li>Cost: 0.02 USD (-32.94%)</li><li><strong>WARNING:</strong>Some final URLs for your Ads are not reachable:
<ul>
<li>Final url <a href='https://not-reachable.airt.ai/' target='_blank'>https://not-reachable.airt.ai/</a> used in Ad <a href='https://ads.google.com/aw/ads/edit/search?adId=688768033895&adGroupIdForAd=156261983518&__e=2324127278' target='_blank'>688768033895</a> is <strong>not reachable</strong></li>
<li>Final url <a href='https://also-not-reachable.airt.ai/' target='_blank'>https://also-not-reachable.airt.ai/</a> used in Ad <a href='https://ads.google.com/aw/ads/edit/search?adId=688768033895&adGroupIdForAd=158468020535&__e=2324127278' target='_blank'>688768033895</a> is <strong>not reachable</strong></li>
</ul>
</li>
</ul></li><li>Campaign <strong><a href='https://ads.google.com/aw/campaigns?campaignId=20979579987&__e=2324127278' target='_blank'>Empty</a></strong><ul><li>Clicks: 0 (+0%)</li><li>Conversions: 0.0 (+0%)</li><li>Cost: 0.0 USD (+0%)</li></ul></li></ul><p>Customer <strong>7119828439</strong></p><ul><li>Campaign <strong><a href='https://ads.google.com/aw/campaigns?campaignId=20750580900&__e=7119828439' target='_blank'>faststream-web-search</a></strong><ul><li>Clicks: 10</li><li>Conversions: 0.0 (+0.0%)</li><li>Cost: 2.83 EUR (-32.94%)</li></ul></li></ul>"""
    assert excepted_message == message

    fixtures_path = Path(__file__).resolve().parent / "fixtures"
    with open(fixtures_path / "expected_main_email_template.html") as file:
        expected_main_email_template = file.read()

    # compare strings but ignore white spaces
    main_email_template = re.sub(r"\s+", "", main_email_template)
    expected_main_email_template = re.sub(r"\s+", "", expected_main_email_template)

    assert expected_main_email_template == main_email_template


def test_send_email() -> None:
    with unittest.mock.patch("requests.post") as mock_post:
        with unittest.mock.patch(
            "captn.captn_agents.backend.teams._daily_analysis_team.send_email_infobip"
        ) as mock_send_email_infobip:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {"chatID": 239}
            mock_send_email_infobip.return_value = None

            _update_chat_message_and_send_email(
                user_id=1,
                conv_id=239,
                client_email="myemail@mail.com",
                messages="[{'content': 'test'}{content: 'test2'}]",
                initial_message_in_chat="test",
                proposed_user_action=["test1", "test2"],
                main_email_template="test",
            )

            post_data = {
                "userId": 1,
                "chatId": 239,
                "messages": "[{'content': 'test'}{content: 'test2'}]",
                "initial_message_in_chat": '<div class = "captn-daily-analysis">\ntest\n</div>\n',
                "email_content": "<html></html>",
                "proposed_user_action": ["test1", "test2"],
            }

            mock_post.assert_called_once_with(
                f"{REACT_APP_API_URL}/captn-daily-analysis-webhook",
                json=post_data,
                timeout=60,
            )

            mock_send_email_infobip.assert_called_once()


def test_execute_daily_analysis_with_incorrect_emails() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._daily_analysis_team.get_user_ids_and_emails"
    ) as mock_get_user_ids_and_emails:
        with unittest.mock.patch(
            "captn.captn_agents.backend.teams._daily_analysis_team._get_conv_id"
        ) as mock_get_conv_id:
            mock_get_user_ids_and_emails.return_value = json.dumps(
                {
                    1: "name@mail.com",
                    2: "name2@mail.com",
                }
            )

            execute_daily_analysis(
                send_only_to_emails=["bla1@mail.com", "bla2@mail.com"]
            )
            mock_get_conv_id.assert_not_called()


def test_google_ads_api_call_reties_three_times() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._daily_analysis_team.list_accessible_customers"
    ) as mock_list_accessible_customers:
        mock_list_accessible_customers.side_effect = [
            ValueError("Error1"),
            ValueError("Error2"),
            ValueError("Error2"),
        ]
        with pytest.raises(RetryError):
            google_ads_api_call(
                function=mock_list_accessible_customers,
                user_id=-1,
                conv_id=-1,
                get_only_non_manager_accounts=True,
            )
        assert mock_list_accessible_customers.call_count == 3


def test_google_ads_api_call_reties_returns_result_in_second_attempt() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._daily_analysis_team.list_accessible_customers"
    ) as mock_list_accessible_customers:
        mock_list_accessible_customers.side_effect = [ValueError("Error1"), ["1", "2"]]
        result = google_ads_api_call(
            function=mock_list_accessible_customers,
            user_id=-1,
            conv_id=-1,
            get_only_non_manager_accounts=True,
        )
        assert result == ["1", "2"]
        assert mock_list_accessible_customers.call_count == 2


def test_execute_daily_analysis_workflow() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._daily_analysis_team.get_user_ids_and_emails"
    ) as mock_get_user_ids_and_emails:
        with unittest.mock.patch(
            "captn.captn_agents.backend.teams._daily_analysis_team._get_conv_id"
        ) as mock_get_conv_id:
            with unittest.mock.patch(
                "captn.captn_agents.backend.teams._daily_analysis_team.get_login_url"
            ) as mock_get_login_url:
                with unittest.mock.patch(
                    "captn.captn_agents.backend.teams._daily_analysis_team.get_daily_report"
                ) as mock_get_daily_report:
                    with unittest.mock.patch(
                        "captn.captn_agents.backend.teams._daily_analysis_team.DailyAnalysisTeam.initiate_chat"
                    ) as mock_initiate_chat:
                        with unittest.mock.patch(
                            "captn.captn_agents.backend.teams._daily_analysis_team.DailyAnalysisTeam.get_messages",
                        ) as mock_messages:
                            with unittest.mock.patch(
                                "captn.captn_agents.backend.teams._daily_analysis_team._update_chat_message_and_send_email"
                            ) as mock_update_chat_message_and_send_email:
                                mock_get_user_ids_and_emails.return_value = (
                                    """{"1": "robert@airt.ai"}"""
                                )
                                mock_get_conv_id.return_value = -1
                                mock_get_login_url.return_value = {
                                    "login_url": ALREADY_AUTHENTICATED
                                }
                                fixtures_path = (
                                    Path(__file__).resolve().parent / "fixtures"
                                )
                                with open(fixtures_path / "daily_reports.txt") as file:
                                    daily_reports = json.load(file)
                                mock_get_daily_report.return_value = json.dumps(
                                    daily_reports
                                )
                                mock_initiate_chat.return_value = None
                                mock_messages.return_value = [
                                    {},
                                    {},
                                    {},
                                    {},
                                    {},
                                    {
                                        "content": "",
                                        "tool_calls": [
                                            {
                                                "id": "call_rGUkPeQguUphvXngXplK7iwy",
                                                "function": {
                                                    "arguments": "{\"proposed_user_actions\":[\"Pause the ad with ID 680002685922 in the 'Ad group 1' of the 'faststream-web-search' campaign due to high cost and no conversions.\",\"Update the match type for the keyword 'microservices' to 'PHRASE' or 'EXACT' to improve targeting in the 'Ad group 1' of the 'faststream-web-search' campaign.\",\"Add the keywords 'asynchronous web services', 'event streams', 'message queues', 'Pydantic validation', 'dependency injection', 'in-memory tests', and 'code generation' to the 'Ad group 1' of the 'faststream-web-search' campaign to align with the services offered as per the website summary.\",\"Create new ad copy for the 'Ad group 1' of the 'faststream-web-search' campaign with headlines such as 'FastStream Framework', 'Async Services Made Easy', 'Unified Messaging API', and descriptions like 'Build efficient microservices with FastStream', 'Streamline your message brokers', 'Automate with FastStream's features'.\",\"Remove the negative keyword 'synchronous' from the 'faststream-web-search' campaign as it might be too restrictive considering the client's focus on asynchronous services.\",\"Consider adding more specific negative keywords such as 'SQL databases', 'blocking IO', or 'monolithic architecture' to the 'faststream-web-search' campaign to filter out unrelated queries.\"]}",
                                                    "name": "send_email",
                                                },
                                                "type": "function",
                                                "index": 0,
                                            }
                                        ],
                                        "role": "assistant",
                                        "name": "account_manager",
                                    },
                                    {
                                        "content": "{'subject': 'Capt’n.ai Daily Analysis', 'email_content': '<html></html>', 'proposed_user_action': [\"Pause the ad with ID 680002685922 in the 'Ad group 1' of the 'faststream-web-search' campaign due to high cost and no conversions.\", \"Update the match type for the keyword 'microservices' to 'PHRASE' or 'EXACT' to improve targeting in the 'Ad group 1' of the 'faststream-web-search' campaign.\", \"Add the keywords 'asynchronous web services', 'event streams', 'message queues', 'Pydantic validation', 'dependency injection', 'in-memory tests', and 'code generation' to the 'Ad group 1' of the 'faststream-web-search' campaign to align with the services offered as per the website summary.\", \"Create new ad copy for the 'Ad group 1' of the 'faststream-web-search' campaign with headlines such as 'FastStream Framework', 'Async Services Made Easy', 'Unified Messaging API', and descriptions like 'Build efficient microservices with FastStream', 'Streamline your message brokers', 'Automate with FastStream's features'.\", \"Remove the negative keyword 'synchronous' from the 'faststream-web-search' campaign as it might be too restrictive considering the client's focus on asynchronous services.\", \"Consider adding more specific negative keywords such as 'SQL databases', 'blocking IO', or 'monolithic architecture' to the 'faststream-web-search' campaign to filter out unrelated queries.\"], 'terminate_groupchat': True}",
                                        "tool_responses": [
                                            {
                                                "tool_call_id": "call_rGUkPeQguUphvXngXplK7iwy",
                                                "role": "tool",
                                                "content": "{'subject': 'Capt’n.ai Daily Analysis', 'email_content': '<html></html>', 'proposed_user_action': [\"Pause the ad with ID 680002685922 in the 'Ad group 1' of the 'faststream-web-search' campaign due to high cost and no conversions.\", \"Update the match type for the keyword 'microservices' to 'PHRASE' or 'EXACT' to improve targeting in the 'Ad group 1' of the 'faststream-web-search' campaign.\", \"Add the keywords 'asynchronous web services', 'event streams', 'message queues', 'Pydantic validation', 'dependency injection', 'in-memory tests', and 'code generation' to the 'Ad group 1' of the 'faststream-web-search' campaign to align with the services offered as per the website summary.\", \"Create new ad copy for the 'Ad group 1' of the 'faststream-web-search' campaign with headlines such as 'FastStream Framework', 'Async Services Made Easy', 'Unified Messaging API', and descriptions like 'Build efficient microservices with FastStream', 'Streamline your message brokers', 'Automate with FastStream's features'.\", \"Remove the negative keyword 'synchronous' from the 'faststream-web-search' campaign as it might be too restrictive considering the client's focus on asynchronous services.\", \"Consider adding more specific negative keywords such as 'SQL databases', 'blocking IO', or 'monolithic architecture' to the 'faststream-web-search' campaign to filter out unrelated queries.\"], 'terminate_groupchat': True}",
                                            }
                                        ],
                                        "role": "tool",
                                        "name": "account_manager",
                                    },
                                ]

                                mock_update_chat_message_and_send_email.return_value = (
                                    None
                                )

                                execute_daily_analysis(
                                    send_only_to_emails=["robert@airt.ai"]
                                )

                                mock_update_chat_message_and_send_email.assert_called_once()


def test_calculate_metrics_change() -> None:
    metrics1 = KeywordMetrics(
        impressions=8,
        clicks=0,
        interactions=0,
        conversions=0,
        cost_micros=0,
        impressions_increase=None,
        clicks_increase=None,
        interactions_increase=None,
        conversions_increase=None,
        cost_micros_increase=None,
        historical_quality_score=2,
        historical_landing_page_quality_score="BELOW_AVERAGE",
        historical_creative_quality_score="AVERAGE",
        historical_quality_score_increase=None,
    )
    metrics2 = KeywordMetrics(
        impressions=9,
        clicks=1,
        interactions=1,
        conversions=0,
        cost_micros=170000,
        impressions_increase=None,
        clicks_increase=None,
        interactions_increase=None,
        conversions_increase=None,
        cost_micros_increase=None,
        historical_quality_score=None,
        historical_landing_page_quality_score=None,
        historical_creative_quality_score=None,
        historical_quality_score_increase=None,
    )
    result = calculate_metrics_change(metrics1, metrics2)
    excepted_result = KeywordMetrics(
        impressions=8,
        clicks=0,
        interactions=0,
        conversions=0,
        cost_micros=0,
        impressions_increase=-11.11,
        clicks_increase=None,
        interactions_increase=None,
        conversions_increase=0.0,
        cost_micros_increase=None,
        historical_quality_score=2,
        historical_landing_page_quality_score="BELOW_AVERAGE",
        historical_creative_quality_score="AVERAGE",
        historical_quality_score_increase=None,
    )
    assert excepted_result == result
