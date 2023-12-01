from typing import Literal, Optional

from pydantic import BaseModel, ValidationError, field_validator


class AdBase(BaseModel):
    customer_id: str
    ad_group_id: Optional[str] = None
    ad_id: Optional[str] = None
    name: Optional[str] = None
    cpc_bid_micros: Optional[int] = None
    status: Optional[Literal["ENABLED", "PAUSED"]] = None


class AdGroup(AdBase):
    ad_group_id: str
    

class AdGroupAd(AdGroup):
    ad_id: str


class Campaign(AdBase):
    campaign_id: str
