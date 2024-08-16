from typing import Optional

import pytest
from pydantic import ValidationError

from google_ads.model import (
    AdGroupAd,
    CampaignCallouts,
    SiteLink,
    _remove_keyword_insertion_chars,
)


class TestAdGroupAd:
    @pytest.mark.parametrize(
        "headlines, descriptions, expected",
        [
            (
                ["Headline 1", "Headline 2", "Headline 3"],
                ["Description 1", "Description 2"],
                None,
            ),
            (
                ["Headline 1", "Headline 2"],
                ["Description 1", "Description 2"],
                ValidationError,
            ),
            (
                ["Headline 1", "Headline 2", "Headline 3"],
                ["Description 1"],
                ValidationError,
            ),
        ],
    )
    def test_minimum_number_of_headlines_and_descriptions(
        self, headlines, descriptions, expected
    ):
        if expected == ValidationError:
            with pytest.raises(ValidationError):
                AdGroupAd(
                    customer_id="2222", headlines=headlines, descriptions=descriptions
                )
        else:
            AdGroupAd(
                customer_id="2222", headlines=headlines, descriptions=descriptions
            )

    @pytest.mark.parametrize(
        "headline, expected",
        [
            ("{KeyWord: 1}", "1"),
            ("{keyWord: abc}", "abc"),
            ("keyword1", "keyword1"),
        ],
    )
    def test_remove_keyword_insertion_chars(self, headline, expected):
        assert _remove_keyword_insertion_chars(headline) == expected

    @pytest.mark.parametrize(
        "headlines, expected",
        [
            (["Headline 1", "h" * 31, "A" * 31], ValueError),
            (["Headline 1", "Headline 2", "{KeyWord: " + "A" * 30 + "}"], None),
            (["Headline 1", "Headline 2", "{KeyWord: " + "A" * 31 + "}"], ValueError),
        ],
    )
    def test_maximum_headline_string_length(self, headlines, expected):
        if expected is ValueError:
            with pytest.raises(ValueError):
                AdGroupAd(
                    customer_id="2222",
                    headlines=headlines,
                    descriptions=["Description 1", "Description 2"],
                )
        else:
            AdGroupAd(
                customer_id="2222",
                headlines=headlines,
                descriptions=["Description 1", "Description 2"],
            )


class TestSiteLink:
    def test_link_text_longer_than_25_characters(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            SiteLink(link_text="A" * 26, final_urls=["https://www.example.com"])

        assert "String should have at most 25 characters" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("description1", "description2", "expected"),
        [
            ("Description 1", "Description 2", None),
            ("Description 1", None, ValueError),
            (None, "Description 2", ValueError),
            (None, None, None),
        ],
    )
    def test_descritptions(
        self, description1: str, description2: str, expected: Optional[Exception]
    ) -> None:
        if expected is not None:
            with pytest.raises(ValueError) as exc_info:
                SiteLink(
                    link_text="Link Text",
                    final_urls=["https://www.example.com"],
                    description1=description1,
                    description2=description2,
                )
            assert (
                "Either both description1 and description2 should be provided, or neither"
                in str(exc_info.value)
            )
        else:
            SiteLink(
                link_text="Link Text",
                final_urls=["https://www.example.com"],
                description1=description1,
                description2=description2,
            )


class TestCampaignCallouts:
    @pytest.mark.parametrize(
        "callouts, expected",
        [
            (["Callout 1", "Callout 2", "Callout 3"], None),
            (["Callout 1", "Callout 2", "C" * 26], ValueError),
        ],
    )
    def test_maximum_callout_string_length(self, callouts, expected):
        if expected is not None:
            with pytest.raises(ValueError):
                CampaignCallouts(
                    customer_id="2222",
                    campaign_id="3333",
                    callouts=callouts,
                )
        else:
            CampaignCallouts(
                customer_id="2222",
                campaign_id="3333",
                callouts=callouts,
            )
