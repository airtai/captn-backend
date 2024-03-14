import unittest
from typing import Optional
from unittest.mock import MagicMock

import pytest

from captn.captn_agents.backend.google_ads_team import (
    add_currency_check,
    check_currency,
    create_keyword_for_ad_group,
    get_customer_currency,
)
from google_ads.model import AdGroupCriterion


class TestGoogleAdsTeam:
    @pytest.mark.parametrize("micros_var_name", [None, "budget_micros"])
    def test_add_currency_check(self, micros_var_name: Optional[str]) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.google_ads_team.get_customer_currency"
        ) as mock_get_customer_currency:
            mock_get_customer_currency.return_value = "EUR"

            f = MagicMock()

            if micros_var_name is None:
                f_with_check = add_currency_check(
                    f, user_id=123, conv_id=456, clients_question_answere_list=[]
                )
                micros_var_name = "cpc_bid_micros"
            else:
                f_with_check = add_currency_check(
                    f,
                    user_id=123,
                    conv_id=456,
                    clients_question_answere_list=[],
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
                match=r"Error: Customer \(12121212\) account has set currency \(EUR\) which is different from the provided currency \(local_currency='USD'\)",
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

    def test_add_currency_check_on_create_keyword_for_ad_group(self) -> None:
        with unittest.mock.patch(
            "captn.captn_agents.backend.google_ads_team.get_customer_currency"
        ) as mock_get_customer_currency, unittest.mock.patch(
            "captn.captn_agents.backend.google_ads_team.google_ads_create_update"
        ) as mock_google_ads_create_update:

            mock_get_customer_currency.return_value = "EUR"
            mock_google_ads_create_update.return_value = "Great success!"

            create_keyword_for_ad_group_llm = add_currency_check(
                create_keyword_for_ad_group,
                user_id=123,
                conv_id=456,
                clients_question_answere_list=[],
            )

            retval = create_keyword_for_ad_group_llm(
                customer_id="12121212",
                ad_group_id="34343434",
                keyword_text="keyword_text",
                keyword_match_type="EXACT",
                clients_approval_message="Yes",
                modification_question="Please approve the new CPC bid for the keyword",
                cpc_bid_micros=1000,
                local_currency="EUR",
            )
            assert retval == "Great success!"

            mock_google_ads_create_update.called_once_with(
                user_id=123,
                conv_id=456,
                clients_approval_message="Yes",
                modification_question="Please approve the new CPC bid for the keyword",
                ad=AdGroupCriterion(
                    customer_id="12121212",
                    ad_group_id="34343434",
                    status=None,
                    keyword_match_type="EXACT",
                    keyword_text="keyword_text",
                    negative=None,
                    bid_modifier=None,
                    cpc_bid_micros=1000,
                ),
                clients_question_answere_list=[],
                endpoint="/add-keywords-to-ad-group",
            )


def test_get_customer_currency() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.execute_query"
    ) as mock_execute_query:
        mock_execute_query.return_value = str(
            {"12121212": [{"customer": {"currencyCode": "EUR"}}]}
        )
        currency = get_customer_currency(user_id=-1, conv_id=-1, customer_id="12121212")
        assert currency == "EUR"


def test_check_currency_raises_exception_if_incorrect_currency() -> None:
    with unittest.mock.patch(
        "captn.captn_agents.backend.google_ads_team.execute_query"
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
        "captn.captn_agents.backend.google_ads_team.execute_query"
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
