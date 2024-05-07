import time

import pytest
from pydantic_core._pydantic_core import ValidationError

from captn.captn_agents.backend.benchmarking.websurfer import benchmark_websurfer
from captn.captn_agents.backend.tools._functions import (
    Summary,
    WebPageSummary,
    WebUrl,
    get_get_info_from_the_web_page,
    get_webpage_status_code,
)


class TestWebPageSummary:
    def test_Summary_raises_error_if_there_are_no_relevant_pages(self):
        with pytest.raises(ValidationError) as e:
            Summary(
                summary="This is a summary",
                relevant_pages=[],
            )
        assert (
            "relevant_pages\n  List should have at least 1 item after validation, not 0"
            in str(e)
        ), str(e)

    def test_WebPageSummary_raises_error_if_less_than_3_headlines(self):
        with pytest.raises(ValidationError) as e:
            WebPageSummary(
                url="https://airt.ai",
                title="This is a title",
                page_summary="This is a page summary",
                headlines=[
                    "This is a headline",
                ],
                keywords=["This is a keyword"],
                summary="This is a summary",
                descriptions=["This is a description", "This is a description2"],
            )
        assert (
            "headlines\n  List should have at least 3 items after validation, not 1"
            in str(e)
        ), str(e)

    def test_WebPageSummary_raises_error_if_less_than_2_descriptions(self):
        with pytest.raises(ValidationError) as e:
            WebPageSummary(
                url="https://airt.ai",
                title="This is a title",
                page_summary="This is a page summary",
                headlines=[
                    "This is a headline",
                    "This is a headline2",
                    "This is a headline3",
                ],
                keywords=["This is a keyword"],
                summary="This is a summary",
                descriptions=["This is a description"],
            )
        assert (
            "descriptions\n  List should have at least 2 items after validation, not 1"
            in str(e)
        ), str(e)


class TestWebSurfer:
    def test_WebUrl(self):
        web_url = WebUrl(url="airt.ai")
        assert str(web_url.url) == "https://airt.ai/"

        web_url = WebUrl(url="https://google.com")
        assert str(web_url.url) == "https://google.com/"

        with pytest.raises(ValidationError):
            web_url = WebUrl(url="")

        with pytest.raises(ValidationError):
            web_url = WebUrl(url="[Insert URL here]")

        with pytest.raises(ValidationError):
            url = "myads.ads.google.com"
            web_url = WebUrl(url=url)

    def test_get_info_from_the_web_page_raises_error_if_url_is_invalid(self):
        with pytest.raises(ValidationError):
            get_get_info_from_the_web_page()(
                url="[Insert URL here]",
            )

    def test_get_info_from_the_web_page_returns_404_status_code_message(self):
        url = "https://airt.ai/lalala"
        result = get_get_info_from_the_web_page()(url=url)
        assert "404" in result

    def test_get_webpage_status_code_returns_200(self):
        url = "https://airt.ai"
        status_code = get_webpage_status_code(url=url)
        assert status_code == 200

    def test_get_webpage_status_code_returns_when_url_is_invalid(self):
        url = "www.non-valid-url.com"
        status_code = get_webpage_status_code(url=url)
        assert status_code is None

        url = "https://airt.ai/lalala"
        status_code = get_webpage_status_code(url=url)
        assert status_code == 404

    @pytest.mark.parametrize(
        "url",
        [
            # "faststream.airt.ai",
            # "airt.ai",
            "https://www.ikea.com/gb/en/",
            # "https://docs.pydantic.dev/",
            # "https://websitedemos.net/electronic-store-04",
            # "https://websitedemos.net/organic-shop-02/",
            # "https://www.disneystore.eu",
            # "https://www.hamleys.com/",
            # "www.bbc.com/news",
            # "https://www.konzum.hr/",
        ],
    )
    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.get_info_from_the_web_page
    def test_get_info_from_the_web_page(self, url: str):
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        result = benchmark_websurfer(url=url, outer_retries=3, timestamp=timestamp)
        print(result)