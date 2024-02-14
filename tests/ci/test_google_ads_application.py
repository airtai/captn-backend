import pytest
from fastapi import HTTPException

from google_ads.application import add_geo_targeting_to_campaign
from google_ads.model import GeoTarget


@pytest.mark.asyncio
async def test_add_geo_targeting_to_campaign_raises_exception_if_location_names_and_location_ids_are_none() -> None:
    geo_target = GeoTarget(customer_id="123", campaign_id="456")

    with pytest.raises(HTTPException):
        await add_geo_targeting_to_campaign(user_id=-1, model=geo_target)
