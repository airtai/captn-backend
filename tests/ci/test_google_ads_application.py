import unittest

import pytest
from fastapi import HTTPException

from google_ads.application import create_geo_targeting_for_campaign
from google_ads.model import GeoTargetCriterion


@pytest.mark.asyncio
async def test_add_geo_targeting_to_campaign_raises_exception_if_location_names_and_location_ids_are_none() -> (
    None
):
    geo_target = GeoTargetCriterion(customer_id="123", campaign_id="456")

    with pytest.raises(HTTPException):
        await create_geo_targeting_for_campaign(user_id=-1, model=geo_target)


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
            )
