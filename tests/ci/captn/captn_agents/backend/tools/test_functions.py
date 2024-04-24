import pytest
from pydantic_core._pydantic_core import ValidationError

from captn.captn_agents.backend.tools._functions import (
    WebUrl,
    get_info_from_the_web_page,
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
            get_info_from_the_web_page(
                url="[Insert URL here]",
                task="Website summary",
                task_guidelines="guidelines.",
            )

    @pytest.mark.parametrize(
        "url",
        [
            "faststream.airt.ai",
            "airt.ai",
            "https://www.ikea.com/",
            "https://docs.pydantic.dev/",
            "https://websitedemos.net/electronic-store-04",
            "https://websitedemos.net/organic-shop-02/",
            "https://www.disneystore.eu",
            "https://www.hamleys.com/",
            "www.bbc.com/news",
            "https://www.konzum.hr/",
        ],
    )
    @pytest.mark.flaky
    @pytest.mark.openai
    @pytest.mark.get_info_from_the_web_page
    def test_get_info_from_the_web_page(self, url: str):
        info = get_info_from_the_web_page(
            url=url,
            task="I need website summary which will help me create Google Ads ad groups, ads, and keywords for the website.",
            task_guidelines="Please provide a summary of the website, including the products/services offered, target audience, and any unique selling points.",
        )

        assert "SUMMARY" in info
