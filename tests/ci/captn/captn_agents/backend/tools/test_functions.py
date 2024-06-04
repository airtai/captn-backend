import time
import unittest
from typing import Any

import pytest
from pydantic_core._pydantic_core import ValidationError

from captn.captn_agents.backend.benchmarking.websurfer import benchmark_websurfer
from captn.captn_agents.backend.teams._campaign_creation_team import (
    ad_group_with_ad_and_keywords,
)
from captn.captn_agents.backend.toolboxes.base import Toolbox
from captn.captn_agents.backend.tools._campaign_creation_team_tools import (
    AdGroupWithAdAndKeywords,
)
from captn.captn_agents.backend.tools._functions import (
    Actions,
    BaseContext,
    Context,
    Summary,
    WebPageSummary,
    WebUrl,
    _find_value_in_nested_dict,
    _get_campaign_ids,
    _validate_modification_parameters,
    get_get_info_from_the_web_page,
    get_webpage_status_code,
    reply_to_client,
    send_email,
    validate_customer_and_campaign_id,
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
            # "https://www.ikea.com/gb/en/",
            # "https://docs.pydantic.dev/",
            # "https://websitedemos.net/electronic-store-04",
            # "https://websitedemos.net/organic-shop-02/",
            # "https://www.disneystore.eu",
            "https://www.hamleys.com/",
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


class TestAskClientForPermission:
    def test_find_value_in_nested_dict(self) -> None:
        example = {"customer": "222", "nested": {"find_this": "value"}}
        assert _find_value_in_nested_dict(example, "find_this") == "value"
        assert _find_value_in_nested_dict(example, "not_here") is None

    @pytest.mark.parametrize(
        "use_correct_parameters",
        [
            True,
            False,
        ],
    )
    def test_validate_customer_and_campaign_id(self, use_correct_parameters) -> None:
        campaign_id = "847" if use_correct_parameters else "dosnt_exist_campaign_id"
        context = Context(
            user_id=234,
            conv_id=345,
            recommended_modifications_and_answer_list=[],
            toolbox=Toolbox(),
        )
        modification_function_parameters = {
            "ad_group_with_ad_and_keywords": {
                "campaign_id": "847",
                "customer_id": "2222",
            }
        }
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._functions._get_campaign_ids",
            return_value=[campaign_id],
        ):
            if use_correct_parameters:
                validate_customer_and_campaign_id(
                    modification_function_parameters=modification_function_parameters,
                    context=context,
                )
            else:
                with pytest.raises(ValueError):
                    validate_customer_and_campaign_id(
                        modification_function_parameters=modification_function_parameters,
                        context=context,
                    )

    @pytest.mark.parametrize(
        "modification_function_parameters, expected_output",
        [
            (
                {"ad_group_with_ad_and_keywords": "not_a_model_dump"},
                "argument after ** must be a mapping, not str",
            ),
            (
                {"ad_group_with_ad_and_keywords": {"ad_group": "not_a_model_dump"}},
                "5 validation errors",
            ),
            (
                {
                    "ad_group_with_ad_and_keywords": ad_group_with_ad_and_keywords.model_dump()
                },
                None,
            ),
            (
                {
                    "customer_id": "1111",
                    "campaign_id": "847",
                    "ad_group": {"status": "ENABLED", "name": "FastStream Features"},
                    "ad_group_ad": {
                        "status": "ENABLED",
                        "final_url": "https://faststream.airt.ai/latest/faststream/",
                        "headlines": [
                            "FastAPI Compatible",
                            "Modern Microservices",
                            "Async Services",
                            "Streamline Workflow",
                            "Community Driven",
                        ],
                        "descriptions": [
                            "Build async web services with ease.",
                            "Validate messages with Pydantic.",
                            "Generate docs automatically.",
                            "Manage dependencies efficiently.",
                        ],
                    },
                    "keywords": [
                        {
                            "status": "ENABLED",
                            "keyword_text": "FastStream",
                            "keyword_match_type": "EXACT",
                        },
                    ],
                },
                "parameter customer_id does not exist in create_ad_group_with_ad_and_keywords input parameters: ['ad_group_with_ad_and_keywords']",
            ),
        ],
    )
    def test_validate_modification_parameters(
        self, modification_function_parameters, expected_output
    ) -> None:
        def create_ad_group_with_ad_and_keywords(
            ad_group_with_ad_and_keywords: AdGroupWithAdAndKeywords,
            context: Any,
        ) -> None:
            pass

        context = Context(
            user_id=234,
            conv_id=345,
            recommended_modifications_and_answer_list=[],
            toolbox=Toolbox(),
        )
        if expected_output is None:
            with unittest.mock.patch(
                "captn.captn_agents.backend.tools._functions._get_campaign_ids",
                return_value=["1212"],
            ):
                _validate_modification_parameters(
                    func=create_ad_group_with_ad_and_keywords,
                    function_name="create_ad_group_with_ad_and_keywords",
                    modification_function_parameters=modification_function_parameters,
                    context=context,
                )
        else:
            with pytest.raises(ValueError) as e:
                _validate_modification_parameters(
                    func=create_ad_group_with_ad_and_keywords,
                    function_name="create_ad_group_with_ad_and_keywords",
                    modification_function_parameters=modification_function_parameters,
                    context=context,
                )
            assert expected_output in str(e._excinfo[1])

    @pytest.mark.parametrize(
        "execute_query_return_value, expected",
        [
            (
                "{'222222': [{'campaign': {'id': '333'}}, {'campaign': {'id': '444'}}]}",
                ["333", "444"],
            ),
            (
                "{'222222': [{'campaign': {'id': '333'}}]}",
                ["333"],
            ),
            (
                "{'222222': []}",
                [],
            ),
        ],
    )
    def test_get_campaign_ids(self, execute_query_return_value, expected) -> None:
        context = Context(
            user_id=234,
            conv_id=345,
            recommended_modifications_and_answer_list=[],
            toolbox=Toolbox(),
        )
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._functions.execute_query",
            return_value=execute_query_return_value,
        ):
            assert (
                _get_campaign_ids(
                    context=context,
                    customer_id="222222",
                )
                == expected
            )


@pytest.mark.parametrize(
    "proposed_user_actions",
    [[], ["1"], ["1", "2"], ["1", "2", "3"], ["1", "2", "3", "4"]],
)
def test_send_email_with_proposed_user_actions(proposed_user_actions):
    actions_count = len(proposed_user_actions)
    if actions_count < 1 or actions_count > 3:
        with pytest.raises(ValidationError):
            actions = Actions(proposed_user_actions=proposed_user_actions)
    else:
        actions = Actions(proposed_user_actions=proposed_user_actions)

        result = send_email(actions=actions)
        assert result["proposed_user_action"] == proposed_user_actions


class TestReplyToClient:
    def test_reply_to_client(self):
        context = BaseContext(
            user_id=234,
            conv_id=345,
        )
        reply_to_client(
            message="This is a message",
            completed=True,
            context=context,
        )
        assert context.waiting_for_client_response is True

        # Test that the function raises an error if waiting_for_client_response is True
        with pytest.raises(ValueError):
            reply_to_client(
                message="This is a message",
                completed=False,
                context=context,
            )
