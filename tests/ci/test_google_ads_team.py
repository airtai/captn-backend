import unittest

import pytest

from captn.captn_agents.backend.google_ads_team import (
    check_currency,
    get_customer_currency,
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


def test_check_currency() -> None:
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
