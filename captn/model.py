from typing import Literal, Optional

from pydantic import BaseModel


class AdBase(BaseModel):
    customer_id: str
    name: Optional[str] = None
    status: Optional[Literal["ENABLED", "PAUSED"]] = None


class Campaign(AdBase):
    campaign_id: str


class AdGroup(AdBase):
    ad_group_id: str
    ad_id: Optional[str] = None
    cpc_bid_micros: Optional[int] = None


class AdGroupAd(AdGroup):
    ad_id: str
