import inspect
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock
from unittest.mock import MagicMock

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._google_ads_team_tools import (
    Context,
    _check_currency,
    _get_customer_currency,
    add_currency_check,
    create_google_ads_team_toolbox,
)
from google_ads.model import AdGroup, AdGroupAd, AdGroupCriterion, Campaign

from .helpers import check_llm_config_descriptions, check_llm_config_total_tools


class TestGoogleAdsTeamTools:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        user_id = 1234
        conv_id = 5678
        self.clients_question_answer_list: List[Tuple[str, Optional[str]]] = []

        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

        self.toolbox = create_google_ads_team_toolbox(
            user_id=user_id,
            conv_id=conv_id,
            clients_question_answer_list=self.clients_question_answer_list,
        )

        self.agent = AssistantAgent(name="agent", llm_config=self.llm_config)
        self.user_proxy = UserProxyAgent(name="user_proxy")

        self.toolbox.add_to_agent(self.agent, self.user_proxy)

    def test_llm_config(self) -> None:
        llm_config = self.agent.llm_config

        check_llm_config_total_tools(llm_config, 12)

        name_desc_dict = {
            "get_info_from_the_web_page": "Retrieve wanted information from the web page.",
            "reply_to_client_2": r"Respond to the client \(answer to his task or question for additional information\)",
            "ask_client_for_permission": "Ask the client for permission to make the changes.",
            "change_google_account": "This method should be used only when the client explicitly asks for the change of the Google account",
            "list_accessible_customers": "List all the customers accessible to the user",
            "execute_query": "Query the Google Ads API.",
            "create_campaign": "Creates Google Ads Campaign. VERY IMPORTANT:",
            "create_keyword_for_ad_group": r"Creates \(regular and negative\) keywords for Ad Group",
            "update_ad_group_ad": "Update Google Ad.",
            "update_ad_group": "Update Google Ads Ad Group.",
            "create_ad_group": "Create Google Ads Ad Group.",
            "update_ad_group_criterion": "Update Google Ads Group Criterion.",
        }
        check_llm_config_descriptions(llm_config, name_desc_dict)

    def test_create_campaign_signature(self) -> None:
        create_campaign = self.user_proxy.function_map["create_campaign"]

        sig = inspect.signature(create_campaign)

        params = list(sig.parameters.values())

        names = [param.name for param in params]
        expected = [
            "customer_id",
            "name",
            "budget_amount_micros",
            "clients_approval_message",
            "modification_question",
            "status",
            "network_settings_target_google_search",
            "network_settings_target_search_network",
            "network_settings_target_content_network",
            "local_currency",
        ]
        assert set(names) == set(expected)

    params_create_campaign = {
        "funtion_name": "create_campaign",
        "kwargs": {
            "customer_id": "123",
            "name": "cool campaign",
            "budget_amount_micros": 1000,
            "clients_approval_message": "yes",
            "modification_question": "may I?",
            "status": "ENABLED",
            "network_settings_target_google_search": True,
            "network_settings_target_search_network": False,
            "network_settings_target_content_network": True,
            "local_currency": "EUR",
        },
        "kwargs_set_to_none": {},
        "model_class": Campaign,
        "endpoint": "/create-campaign",
    }

    params_create_keyword_for_ad_group = {
        "funtion_name": "create_keyword_for_ad_group",
        "kwargs": {
            "ad_group_id": "234",
            "keyword_text": "keyword",
            "keyword_match_type": "EXACT",
            "negative": False,
            "bid_modifier": 1.0,
            "cpc_bid_micros": 1000,
        },
        "kwargs_set_to_none": {},
        "model_class": AdGroupCriterion,
        "endpoint": "/add-keywords-to-ad-group",
    }

    params_update_ad_group_ad = {
        "funtion_name": "update_ad_group_ad",
        "kwargs": {
            "ad_group_id": "234",
            "ad_id": "345",
            "cpc_bid_micros": 1000,
        },
        "kwargs_set_to_none": {
            "headlines": None,
            "descriptions": None,
        },
        "model_class": AdGroupAd,
        "endpoint": "/update-ad-group-ad",
    }

    params_update_ad_group = {
        "funtion_name": "update_ad_group",
        "kwargs": {
            "ad_group_id": "234",
            "cpc_bid_micros": 1000,
            "name": "cool ad group",
        },
        "kwargs_set_to_none": {},
        "model_class": AdGroup,
        "endpoint": "/update-ad-group",
    }

    params_create_ad_group = {
        "funtion_name": "create_ad_group",
        "kwargs": {
            "campaign_id": "234",
            "name": "cool ad group",
            "cpc_bid_micros": 1000,
        },
        "kwargs_set_to_none": {},
        "model_class": AdGroup,
        "endpoint": "/create-ad-group",
    }

    params_update_ad_group_criterion = {
        "funtion_name": "update_ad_group_criterion",
        "kwargs": {
            "ad_group_id": "234",
            "criterion_id": "345",
            "cpc_bid_micros": 1000,
            "keyword_text": "keyword",
            "keyword_match_type": "EXACT",
        },
        "kwargs_set_to_none": {},
        "model_class": AdGroupCriterion,
        "endpoint": "/update-ad-group-criterion",
    }

    @pytest.mark.parametrize(
        "params",
        [
            params_create_campaign,
            params_create_keyword_for_ad_group,
            params_update_ad_group_ad,
            params_update_ad_group,
            params_create_ad_group,
            params_update_ad_group_criterion,
        ],
    )
    def test_functions_which_use_add_currency_check_decorator(
        self, params: Dict[str, Any]
    ) -> None:
        func = self.user_proxy.function_map[params["funtion_name"]]

        with (
            mock.patch(
                "captn.captn_agents.backend.tools._google_ads_team_tools.google_ads_create_update",
                return_value="campaign created",
            ) as mock_google_ads_create_update,
            mock.patch(
                "captn.captn_agents.backend.tools._google_ads_team_tools._get_customer_currency",
                return_value="EUR",
            ) as mock_get_customer_currency,
        ):
            self.clients_question_answer_list.append(("whatsup?", "whatsup!"))

            default_kwargs = {
                "customer_id": "123",
                "clients_approval_message": "yes",
                "modification_question": "may I?",
                "status": "ENABLED",
                "local_currency": "EUR",
            }
            params["kwargs"] = {**default_kwargs, **params["kwargs"]}

            func(**params["kwargs"])

            kwargs_combined = {**params["kwargs"], **params["kwargs_set_to_none"]}

            mock_google_ads_create_update.assert_called_once_with(
                user_id=1234,
                conv_id=5678,
                clients_question_answer_list=[("whatsup?", "whatsup!")],
                clients_approval_message="yes",
                modification_question="may I?",
                ad=params["model_class"](**kwargs_combined),
                endpoint=params["endpoint"],
            )

            mock_get_customer_currency.assert_called_once_with(
                user_id=1234, conv_id=5678, customer_id="123"
            )
            mock_get_customer_currency.reset_mock()

            params["kwargs"]["local_currency"] = "USD"
            params["kwargs"]["customer_id"] = "987"
            with pytest.raises(
                ValueError,
                match=r"Error: Customer .+ account has set currency .EUR. which is different from the provided currency .+USD",
            ):
                func(**params["kwargs"])
            mock_get_customer_currency.assert_called_once_with(
                user_id=1234, conv_id=5678, customer_id="987"
            )

    def test_create_campaign_config(self) -> None:
        names = [
            function_wrapper["function"]["name"]
            for function_wrapper in self.agent.llm_config["tools"]
        ]
        i = names.index("create_campaign")
        create_campaign_config = self.agent.llm_config["tools"][i]["function"]
        assert create_campaign_config["name"] == "create_campaign"

        param_names = list(create_campaign_config["parameters"]["properties"].keys())

        assert "context" not in param_names

        expected = [
            "customer_id",
            "name",
            "budget_amount_micros",
            "clients_approval_message",
            "modification_question",
            "status",
            "network_settings_target_google_search",
            "network_settings_target_search_network",
            "network_settings_target_content_network",
            "local_currency",
        ]
        assert set(param_names) == set(expected)

    def test_get_customer_currency(self) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._google_ads_team_tools.execute_query_client"
        ) as mock_execute_query:
            mock_execute_query.return_value = str(
                {"12121212": [{"customer": {"currencyCode": "EUR"}}]}
            )
            currency = _get_customer_currency(
                user_id=-1, conv_id=-1, customer_id="12121212"
            )
            assert currency == "EUR"

    def test_check_currency_raises_exception_if_incorrect_currency(self) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._google_ads_team_tools.execute_query_client"
        ) as mock_execute_query:
            mock_execute_query.return_value = str(
                {"12121212": [{"customer": {"currencyCode": "EUR"}}]}
            )

            with pytest.raises(ValueError) as exc:
                _check_currency(
                    user_id=-1,
                    conv_id=-1,
                    customer_id="12121212",
                    local_currency="USD",
                )

            assert (
                str(exc.value)
                == """Error: Customer (12121212) account has set currency (EUR) which is different from the provided currency (local_currency='USD').
Please convert the budget to the customer's currency and ask the client for the approval with the new budget amount (in the customer's currency)."""
            )

    def test_check_currency_raises_exception_if_currency_is_none(self) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._google_ads_team_tools.execute_query_client"
        ) as mock_execute_query:
            mock_execute_query.return_value = str(
                {"12121212": [{"customer": {"currencyCode": "EUR"}}]}
            )

            with pytest.raises(ValueError) as exc:
                _check_currency(
                    user_id=-1,
                    conv_id=-1,
                    customer_id="12121212",
                    local_currency=None,
                )

            assert (
                str(exc.value)
                == """Error: Customer (12121212) account has set currency (EUR) which is different from the provided currency (local_currency=None).
Please convert the budget to the customer's currency and ask the client for the approval with the new budget amount (in the customer's currency)."""
            )

    @pytest.mark.parametrize("micros_var_name", [None, "budget_micros"])
    def test_add_currency_check_new(self, micros_var_name: Optional[str]) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.tools._google_ads_team_tools._get_customer_currency"
        ) as mock_get_customer_currency:
            mock_get_customer_currency.return_value = "EUR"

            f = MagicMock()

            if micros_var_name is None:
                f_with_check = add_currency_check(f)
                micros_var_name = "cpc_bid_micros"
            else:
                f_with_check = add_currency_check(f)

            context = Context(
                user_id=123,
                conv_id=456,
                clients_question_answer_list=[],
            )
            kwargs = {
                micros_var_name: 1000000,
                "customer_id": "12121212",
                "context": context,
            }
            f_with_check(
                local_currency="EUR",
                **kwargs,
            )
            mock_get_customer_currency.assert_called_once_with(
                user_id=123, conv_id=456, customer_id="12121212"
            )

            mock_get_customer_currency.reset_mock()
            f_with_check(
                customer_id="12121212",
                local_currency="EUR",
            )
            mock_get_customer_currency.assert_not_called()
            ERROR_MSG = r"Error: Customer \(12121212\) account has set currency \(EUR\) which is different from the provided currency \(local_currency='USD'\)"
            with pytest.raises(
                ValueError,
                match=ERROR_MSG,
            ):
                f_with_check(
                    local_currency="USD",
                    **kwargs,
                )

            f_with_check(
                customer_id="12121212",
                local_currency="USD",
            )
