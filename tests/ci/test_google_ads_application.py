import os
import unittest

import pytest
from fastapi import HTTPException, status

from google_ads.application import (
    MAX_HEADLINES_OR_DESCRIPTIONS_ERROR_MSG,
    _set_fields_ad_copy,
    _set_headline_or_description,
)
from google_ads.model import AdCopy

DUMMY = "dummy"
with unittest.mock.patch.dict(
    os.environ,
    {
        "AZURE_OPENAI_API_KEY_SWEDEN": DUMMY,
        "AZURE_API_ENDPOINT": DUMMY,
        "AZURE_API_VERSION": DUMMY,
        "AZURE_GPT4_MODEL": DUMMY,
        "AZURE_GPT35_MODEL": DUMMY,
        "INFOBIP_API_KEY": DUMMY,
        "INFOBIP_BASE_URL": DUMMY,
    },
    clear=True,
):
    from google_ads.application import (
        _check_if_customer_id_is_manager_or_exception_is_raised,
        create_geo_targeting_for_campaign,
    )
    from google_ads.model import GeoTargetCriterion


@pytest.mark.asyncio
async def test_add_geo_targeting_to_campaign_raises_exception_if_location_names_and_location_ids_are_none() -> (
    None
):
    geo_target = GeoTargetCriterion(customer_id="123", campaign_id="456")

    with pytest.raises(HTTPException) as exc:
        await create_geo_targeting_for_campaign(user_id=-1, model=geo_target)

    expected_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either location_names or location_ids must be provided.",
    )
    assert exc.value.status_code == expected_exception.status_code
    assert exc.value.detail == expected_exception.detail


@pytest.mark.asyncio
async def test_add_geo_targeting_to_campaign_raises_exception_if_location_ids_are_none() -> (
    None
):
    geo_target = GeoTargetCriterion(
        customer_id="123",
        campaign_id="456",
        location_names=["New York"],
        location_ids=None,
    )

    with unittest.mock.patch(
        "google_ads.application._get_geo_target_constant_by_names",
    ) as mock_get_geo_target_constant_by_names:
        with unittest.mock.patch(
            "google_ads.application._get_client",
        ) as mock_get_client:
            mock_get_geo_target_constant_by_names.return_value = None
            mock_get_client.return_value = None

            await create_geo_targeting_for_campaign(user_id=-1, model=geo_target)
            mock_get_geo_target_constant_by_names.assert_called_once_with(
                client=None, location_names=["New York"]
            )


@pytest.mark.asyncio
async def test_add_geo_targeting_to_campaign_raises_exception_if_location_ids_are_not_none() -> (
    None
):
    geo_target = GeoTargetCriterion(
        customer_id="123",
        campaign_id="456",
        location_names=None,
        location_ids=["7", "8"],
    )

    with unittest.mock.patch(
        "google_ads.application._create_locations_by_ids_to_campaign",
    ) as mock_create_locations_by_ids_to_campaign:
        with unittest.mock.patch(
            "google_ads.application._get_client",
        ) as mock_get_client:
            mock_create_locations_by_ids_to_campaign.return_value = None
            mock_get_client.return_value = None

            await create_geo_targeting_for_campaign(user_id=-1, model=geo_target)
            mock_create_locations_by_ids_to_campaign.assert_called_once_with(
                client=None,
                location_ids=["7", "8"],
                campaign_id="456",
                customer_id="123",
                negative=None,
            )


@pytest.mark.asyncio
async def test_add_geo_targeting_to_campaign_raises_exception_if_location_ids_are_not_none_and_criteria_is_negative() -> (
    None
):
    geo_target = GeoTargetCriterion(
        customer_id="123",
        campaign_id="456",
        location_names=None,
        location_ids=["7", "8"],
        negative=True,
    )

    with unittest.mock.patch(
        "google_ads.application._create_locations_by_ids_to_campaign",
    ) as mock_create_locations_by_ids_to_campaign:
        with unittest.mock.patch(
            "google_ads.application._get_client",
        ) as mock_get_client:
            mock_create_locations_by_ids_to_campaign.return_value = None
            mock_get_client.return_value = None

            await create_geo_targeting_for_campaign(user_id=-1, model=geo_target)
            mock_create_locations_by_ids_to_campaign.assert_called_once_with(
                client=None,
                location_ids=["7", "8"],
                campaign_id="456",
                customer_id="123",
                negative=True,
            )


@pytest.mark.asyncio
async def test_check_if_customer_id_is_manager_or_exception_is_raised_when_customer_is_not_manager() -> (
    None
):
    with unittest.mock.patch(
        "google_ads.application.search",
    ) as mock_search:
        mock_search.return_value = {
            "2324127278": [
                {
                    "customer": {"manager": True, "testAccount": True},
                }
            ]
        }
        skip_customer = await _check_if_customer_id_is_manager_or_exception_is_raised(
            user_id=-1, customer_id="1212112"
        )
        assert skip_customer


@pytest.mark.asyncio
async def test_check_if_customer_id_is_manager_or_exception_is_raised_when_customer_is_manager() -> (
    None
):
    with unittest.mock.patch(
        "google_ads.application.search",
    ) as mock_search:
        mock_search.return_value = {
            "2324127278": [
                {
                    "customer": {"manager": False, "testAccount": True},
                }
            ]
        }
        skip_customer = await _check_if_customer_id_is_manager_or_exception_is_raised(
            user_id=-1, customer_id="1212112"
        )
        assert not skip_customer


@pytest.mark.asyncio
async def test_check_if_customer_id_is_manager_or_exception_is_raised_when_error_is_raised() -> (
    None
):
    with unittest.mock.patch(
        "google_ads.application.search",
    ) as mock_search:
        mock_search.side_effect = Exception("Goodle Ads API exception")
        skip_customer = await _check_if_customer_id_is_manager_or_exception_is_raised(
            user_id=-1, customer_id="1212112"
        )
        assert skip_customer


def test_set_headline_or_description_max_headlines() -> None:
    client = unittest.mock.MagicMock()
    headline_or_description = unittest.mock.MagicMock()
    headline_or_description.text = "h1"
    client.get_type.return_value = headline_or_description

    headline = {"text": "h1"}
    headlines = [headline] * 15
    update_field = "headlines"
    responsive_search_ad = {update_field: headlines}
    new_text = "h16"

    operation_update = unittest.mock.MagicMock()

    with pytest.raises(ValueError) as exc:
        _set_headline_or_description(
            client=client,
            update_field=update_field,
            operation_update=operation_update,
            new_text=new_text,
            responsive_search_ad=responsive_search_ad,
            update_existing_index=None,
        )

    assert (
        str(exc.value)
        == f"{MAX_HEADLINES_OR_DESCRIPTIONS_ERROR_MSG} {update_field}: 15"
    )


def test_set_headline_or_description_max_descriptions() -> None:
    client = unittest.mock.MagicMock()
    headline_or_description = unittest.mock.MagicMock()
    headline_or_description.text = "d1"
    client.get_type.return_value = headline_or_description

    headline = {"text": "d1"}
    headlines = [headline] * 4
    update_field = "descriptions"
    responsive_search_ad = {update_field: headlines}
    new_text = "d5"

    operation_update = unittest.mock.MagicMock()

    with pytest.raises(ValueError) as exc:
        _set_headline_or_description(
            client=client,
            update_field=update_field,
            operation_update=operation_update,
            new_text=new_text,
            responsive_search_ad=responsive_search_ad,
            update_existing_index=None,
        )
    assert (
        str(exc.value) == f"{MAX_HEADLINES_OR_DESCRIPTIONS_ERROR_MSG} {update_field}: 4"
    )


@pytest.mark.asyncio
async def test_set_fields_ad_copy_max_headlines_and_descriptions() -> None:
    client = unittest.mock.MagicMock()
    headline_or_description = unittest.mock.MagicMock()
    headline_or_description.text = "d1"
    client.get_type.return_value = headline_or_description

    model = AdCopy(
        customer_id="123",
        ad_id="456",
        headline="h16",
        description="d5",
    )

    with unittest.mock.patch(
        "google_ads.application.search",
    ) as mock_search:
        mock_search.return_value = {
            "123": [
                {
                    "adGroupAd": {
                        "ad": {
                            "responsiveSearchAd": {
                                "headlines": [
                                    {
                                        "text": "aaaa",
                                    },
                                    {
                                        "text": "b",
                                    },
                                    {
                                        "text": "c",
                                    },
                                    {
                                        "text": "d",
                                    },
                                    {
                                        "text": "e",
                                    },
                                    {
                                        "text": "f",
                                    },
                                    {
                                        "text": "g",
                                    },
                                    {
                                        "text": "h",
                                    },
                                    {
                                        "text": "i",
                                    },
                                    {
                                        "text": "j",
                                    },
                                    {
                                        "text": "k",
                                    },
                                    {
                                        "text": "l",
                                    },
                                    {
                                        "text": "m",
                                    },
                                    {
                                        "text": "n",
                                    },
                                    {
                                        "text": "o",
                                    },
                                ],
                                "descriptions": [
                                    {
                                        "text": "a",
                                    },
                                    {
                                        "text": "b",
                                    },
                                    {
                                        "text": "c",
                                    },
                                    {
                                        "text": "d",
                                    },
                                ],
                            },
                        },
                    }
                }
            ]
        }

        with pytest.raises(ValueError) as exc:
            await _set_fields_ad_copy(
                client=client,
                model_or_dict=model,
                operation=object,
                operation_update=object,
                user_id=-1,
            )

    assert (
        str(exc.value)
        == f"{MAX_HEADLINES_OR_DESCRIPTIONS_ERROR_MSG} headlines: 15\n{MAX_HEADLINES_OR_DESCRIPTIONS_ERROR_MSG} descriptions: 4"
    )
