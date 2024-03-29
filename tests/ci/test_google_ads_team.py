import unittest
from typing import Any, Callable, Dict, Optional, Type, Union
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from captn.captn_agents.backend.teams._google_ads_team import (
    add_currency_check,
    check_currency,
    create_ad_group,
    create_campaign,
    create_keyword_for_ad_group,
    get_customer_currency,
    update_ad_group,
    update_ad_group_ad,
    update_ad_group_criterion,
)
from google_ads.model import AdGroup, AdGroupAd, AdGroupCriterion, Campaign


class TestGoogleAdsTeam:
    ERROR_MSG = r"Error: Customer \(12121212\) account has set currency \(EUR\) which is different from the provided currency \(local_currency='USD'\)"

    @pytest.mark.parametrize("micros_var_name", [None, "budget_micros"])
    def test_add_currency_check(self, micros_var_name: Optional[str]) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.teams._google_ads_team.get_customer_currency"
        ) as mock_get_customer_currency:
            mock_get_customer_currency.return_value = "EUR"

            f = MagicMock()

            if micros_var_name is None:
                f_with_check = add_currency_check(
                    f, user_id=123, conv_id=456, clients_question_answer_list=[]
                )
                micros_var_name = "cpc_bid_micros"
            else:
                f_with_check = add_currency_check(
                    f,
                    user_id=123,
                    conv_id=456,
                    clients_question_answer_list=[],
                    micros_var_name=micros_var_name,
                )

            f_with_check(
                customer_id="12121212",
                local_currency="EUR",
                **{micros_var_name: 1000000},
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

            with pytest.raises(
                ValueError,
                match=TestGoogleAdsTeam.ERROR_MSG,
            ):
                f_with_check(
                    customer_id="12121212",
                    local_currency="USD",
                    **{micros_var_name: 1000000},
                )

            f_with_check(
                customer_id="12121212",
                local_currency="USD",
            )

    def _test_add_currency_check_helper(
        self,
        f: Callable[..., Union[Dict[str, Any], str]],
        model: Type[BaseModel],
        micros_var_name: str,
        **kwargs: Any,
    ) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.teams._google_ads_team.get_customer_currency"
        ) as mock_get_customer_currency, unittest.mock.patch(
            "captn.captn_agents.backend.teams._google_ads_team.google_ads_create_update"
        ) as mock_google_ads_create_update:
            mock_get_customer_currency.return_value = "EUR"
            mock_google_ads_create_update.return_value = "Great success!"

            create_update_resource_for_llm = add_currency_check(
                f,
                user_id=123,
                conv_id=456,
                clients_question_answer_list=[],
                micros_var_name=micros_var_name,
            )

            endpoint = kwargs.pop("endpoint")
            if kwargs.get("set_headlines_and_descriptions_to_none", False):
                kwargs.pop("set_headlines_and_descriptions_to_none")
                retval = create_update_resource_for_llm(
                    **kwargs,
                )
                kwargs["headlines"] = None
                kwargs["descriptions"] = None
            else:
                retval = create_update_resource_for_llm(
                    **kwargs,
                )

            assert retval == "Great success!"

            kwargs.pop("local_currency")

            mock_google_ads_create_update.assert_called_once_with(
                user_id=123,
                conv_id=456,
                clients_approval_message="Yes",
                modification_question="Please approve...",
                ad=model(
                    **kwargs,
                ),
                clients_question_answer_list=[],
                endpoint=endpoint,
            )

            kwargs["local_currency"] = "USD"
            with pytest.raises(
                ValueError,
                match=TestGoogleAdsTeam.ERROR_MSG,
            ):
                create_update_resource_for_llm(
                    **kwargs,
                )

    def test_add_currency_check_on_create_keyword_for_ad_group(self) -> None:
        self._test_add_currency_check_helper(
            create_keyword_for_ad_group,
            AdGroupCriterion,
            "cpc_bid_micros",
            customer_id="12121212",
            ad_group_id="34343434",
            keyword_text="keyword_text",
            keyword_match_type="EXACT",
            clients_approval_message="Yes",
            modification_question="Please approve...",
            cpc_bid_micros=1000,
            local_currency="EUR",
            endpoint="/add-keywords-to-ad-group",
        )

    def test_add_currency_check_on_update_ad_group_ad(self) -> None:
        self._test_add_currency_check_helper(
            update_ad_group_ad,
            AdGroupAd,
            "cpc_bid_micros",
            customer_id="12121212",
            ad_group_id="34343434",
            ad_id="45454545",
            clients_approval_message="Yes",
            modification_question="Please approve...",
            cpc_bid_micros=1000,
            local_currency="EUR",
            set_headlines_and_descriptions_to_none=True,
            endpoint="/update-ad-group-ad",
        )

    def test_add_currency_check_on_update_ad_group(self) -> None:
        self._test_add_currency_check_helper(
            update_ad_group,
            AdGroup,
            "cpc_bid_micros",
            customer_id="12121212",
            ad_group_id="34343434",
            clients_approval_message="Yes",
            modification_question="Please approve...",
            cpc_bid_micros=1000,
            local_currency="EUR",
            endpoint="/update-ad-group",
        )

    def test_add_currency_check_on_create_ad_group(self) -> None:
        self._test_add_currency_check_helper(
            create_ad_group,
            AdGroup,
            "cpc_bid_micros",
            customer_id="12121212",
            campaign_id="34343434",
            name="name",
            clients_approval_message="Yes",
            modification_question="Please approve...",
            cpc_bid_micros=1000,
            local_currency="EUR",
            endpoint="/create-ad-group",
        )

    def test_add_currency_check_on_update_ad_group_criterion(self) -> None:
        self._test_add_currency_check_helper(
            update_ad_group_criterion,
            AdGroupCriterion,
            "cpc_bid_micros",
            customer_id="12121212",
            ad_group_id="34343434",
            criterion_id="45454545",
            clients_approval_message="Yes",
            modification_question="Please approve...",
            status="ENABLED",
            cpc_bid_micros=1000,
            local_currency="EUR",
            endpoint="/update-ad-group-criterion",
        )

    def test_add_currency_check_on_create_campaign(self) -> None:
        self._test_add_currency_check_helper(
            create_campaign,
            Campaign,
            "budget_amount_micros",
            customer_id="12121212",
            name="name",
            clients_approval_message="Yes",
            modification_question="Please approve...",
            budget_amount_micros=1000,
            local_currency="EUR",
            endpoint="/create-campaign",
        )


def test_get_customer_currency() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._google_ads_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.return_value = str(
            {"12121212": [{"customer": {"currencyCode": "EUR"}}]}
        )
        currency = get_customer_currency(user_id=-1, conv_id=-1, customer_id="12121212")
        assert currency == "EUR"


def test_check_currency_raises_exception_if_incorrect_currency() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._google_ads_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.return_value = str(
            {"12121212": [{"customer": {"currencyCode": "EUR"}}]}
        )

        with pytest.raises(ValueError) as exc:
            check_currency(
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


def test_check_currency_raises_exception_if_currency_is_none() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.teams._google_ads_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.return_value = str(
            {"12121212": [{"customer": {"currencyCode": "EUR"}}]}
        )

        with pytest.raises(ValueError) as exc:
            check_currency(
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
