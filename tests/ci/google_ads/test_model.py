import pytest
from pydantic import ValidationError

from google_ads.model import AdGroupAd, _remove_keyword_insertion_chars


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
        if expected == ValueError:
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
