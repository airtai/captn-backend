import time

import pytest
from pydantic_core._pydantic_core import ValidationError

from captn.captn_agents.backend.benchmarking.websurfer import benchmark_websurfer
from captn.captn_agents.backend.tools._functions import (
    WebUrl,
    get_get_info_from_the_web_page,
    get_webpage_status_code,
)


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
        assert status_code == None

        url = "https://airt.ai/lalala"
        status_code = get_webpage_status_code(url=url)
        assert status_code == 404

    @pytest.mark.parametrize(
        "url",
        [
            # "faststream.airt.ai",
            "airt.ai",
            # "https://www.ikea.com/gb/en/",
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
        # print isoformat timestamp
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        result = benchmark_websurfer(url=url, outer_retries=3, timestamp=timestamp)
        print(result)
