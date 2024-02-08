import unittest.mock
from typing import Optional

from autogen.cache import Cache

from captn.captn_agents.backend.daily_analysis_team import (
    REACT_APP_API_URL,
    AdGroup,
    AdGroupAd,
    Campaign,
    Keyword,
    Metrics,
    _get_conv_id_and_send_email,
    calculate_metrics_change,
    compare_reports,
    construct_daily_report_message,
    execute_daily_analysis,
    get_campaigns_report,
    get_daily_ad_group_ads_report,
    get_web_status_code_report_for_campaign,
)


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


def test_get_daily_ad_group_ads_report() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.daily_analysis_team.execute_query"
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
                            metrics=Metrics(
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
                            metrics=Metrics(
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
                            metrics=Metrics(
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
                            metrics=Metrics(
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
                            metrics=Metrics(
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
                            metrics=Metrics(
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
                            metrics=Metrics(
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
                            metrics=Metrics(
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
                            metrics=Metrics(
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
        "captn.captn_agents.backend.daily_analysis_team.execute_query"
    ) as mock_execute_query:
        # mock get_ad_groups_report
        with unittest.mock.patch(
            "captn.captn_agents.backend.daily_analysis_team.get_ad_groups_report"
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
    warning_message = get_web_status_code_report_for_campaign(campaign, customer_id)
    expected = """<li><strong>WARNING:</strong> Some final URLs for your Ads are not reachable:
<ul>
<li>Final url <a href='https://not-reachable.airt.ai/' target='_blank'>https://not-reachable.airt.ai/</a> used in Ad <a href='https://ads.google.com/aw/ads/edit/search?adId=688768033895&adGroupIdForAd=156261983518&&__e=2324127278' target='_blank'>688768033895</a> is <strong>not reachable</strong></li>
<li>Final url <a href='https://airt.ai/bad' target='_blank'>https://airt.ai/bad</a> used in Ad <a href='https://ads.google.com/aw/ads/edit/search?adId=688768033895&adGroupIdForAd=158468020535&&__e=2324127278' target='_blank'>688768033895</a> is <strong>not reachable</strong></li>
</ul>
</li>\n"""
    assert expected == warning_message


def test_construct_campaign_report_message() -> None:
    message = construct_daily_report_message(daily_report, date="2024-02-05")
    expected = """<h2>Daily Analysis:</h2><p>Below is your daily analysis of your Google Ads campaigns for the date 2024-02-05</p><p>Customer <strong>2324127278</strong></p><ul><li>Campaign <strong><a href='https://ads.google.com/aw/campaigns?campaignId=20761810762&__e=2324127278' target='_blank'>Website traffic-Search-3-updated-up</a></strong></li><ul><li>Clicks: 5 (-42.86% compared to the day before)</li><li>Conversions: 0.0 (+0.0% compared to the day before)</li><li>Cost per click: 0.022222 (-32.94% compared to the day before)</li><li><strong>WARNING:</strong> Some final URLs for your Ads are not reachable:
<ul>
<li>Final url <a href='https://not-reachable.airt.ai/' target='_blank'>https://not-reachable.airt.ai/</a> used in Ad <a href='https://ads.google.com/aw/ads/edit/search?adId=688768033895&adGroupIdForAd=156261983518&&__e=2324127278' target='_blank'>688768033895</a> is <strong>not reachable</strong></li>
<li>Final url <a href='https://also-not-reachable.airt.ai/' target='_blank'>https://also-not-reachable.airt.ai/</a> used in Ad <a href='https://ads.google.com/aw/ads/edit/search?adId=688768033895&adGroupIdForAd=158468020535&&__e=2324127278' target='_blank'>688768033895</a> is <strong>not reachable</strong></li>
</ul>
</li>
</ul><li>Campaign <strong><a href='https://ads.google.com/aw/campaigns?campaignId=20979579987&__e=2324127278' target='_blank'>Empty</a></strong></li><ul><li>Clicks: 0 (+0% compared to the day before)</li><li>Conversions: 0.0 (+0% compared to the day before)</li><li>Cost per click: 0.0 (+0% compared to the day before)</li></ul></ul><p>Customer <strong>7119828439</strong></p><ul><li>Campaign <strong><a href='https://ads.google.com/aw/campaigns?campaignId=20750580900&__e=7119828439' target='_blank'>faststream-web-search</a></strong></li><ul><li>Clicks: 10</li><li>Conversions: 0.0 (+0.0% compared to the day before)</li><li>Cost per click: 2.83 (-32.94% compared to the day before)</li></ul></ul>"""
    assert expected == message


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
                    mock_post.return_value.json = lambda: {"chatID": 239}
                    mock_send_email_infobip.return_value = None

                    execute_daily_analysis(
                        send_only_to_emails=["robert@airt.ai"], date=date
                    )
                    mock_send_email_infobip.assert_called_once()


def test_execute_daily_analysis() -> None:
    current_date = "2024-01-30"
    _test_execute_daily_analysis(date=current_date)


def test_send_email() -> None:
    with unittest.mock.patch("requests.post") as mock_post:
        with unittest.mock.patch(
            "captn.captn_agents.backend.daily_analysis_team.send_email_infobip"
        ) as mock_send_email_infobip:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {"chatID": 239}
            mock_send_email_infobip.return_value = None

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

            mock_send_email_infobip.assert_called_once()


# def test_daily_analysis_real() -> None:
#     execute_daily_analysis(send_only_to_emails=["robert@airt.ai"])
