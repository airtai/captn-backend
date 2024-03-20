import unittest

from captn.captn_agents.backend.campaign_creation_team import (
    AdGroup,
    AdGroupAd,
    AdGroupCriterion,
    AdGroupWithAdAndKeywords,
    create_ad_group_with_ad_and_keywords,
)


def test_create_ad_group_with_ad_and_keywords() -> None:
    ad_group_ad = AdGroupAd(
        final_url="https://www.example.com",
        headlines=["headline1", "headline2", "headline3"],
        descriptions=["description1", "description2"],
        status="ENABLED",
    )

    keyword1 = AdGroupCriterion(
        keyword_text="keyword1",
        keyword_match_type="EXACT",
        status="ENABLED",
    )
    keyword2 = AdGroupCriterion(
        keyword_text="keyword2",
        keyword_match_type="EXACT",
        status="ENABLED",
    )

    ad_group = AdGroup(
        name="ad_group",
        status="ENABLED",
        ad_group_ad=ad_group_ad,
        keywords=[keyword1, keyword2],
    )

    ad_group_with_ad_and_keywords = AdGroupWithAdAndKeywords(
        customer_id="1111",
        campaign_id="1212",
        ad_group=ad_group,
        ad_group_ad=ad_group_ad,
        keywords=[keyword1, keyword2],
    )

    with unittest.mock.patch(
        "captn.captn_agents.backend.campaign_creation_team.google_ads_create_update"
    ) as mock_google_ads_create_update:
        side_effect = [
            "Created customers/1212/adGroups/3434.",
            "Created customers/1212/adGroupAds/3434~5656.",
            "Created customers/1212/adGroupCriteria/3434~7878.",
            "Created customers/1212/adGroupCriteria/3434~8989.",
        ]
        mock_google_ads_create_update.side_effect = side_effect

        response = create_ad_group_with_ad_and_keywords(
            user_id=1,
            conv_id=1,
            clients_question_answere_list=[("question", "yes")],
            clients_approval_message="yes",
            modification_question="question",
            ad_group_with_ad_and_keywords=ad_group_with_ad_and_keywords.model_dump(),
        )

        expected_response = f"""Ad group: {side_effect[0]}
Ad group ad: {side_effect[1]}
Keyword: {side_effect[2]}
Keyword: {side_effect[3]}\n"""

        assert mock_google_ads_create_update.call_count == 4
        assert response == expected_response
