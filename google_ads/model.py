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
    cpc_bid_micros: Optional[int] = None


class AdGroupAd(AdGroup):
    ad_id: str


class Criterion(AdBase):
    criterion_id: Optional[str] = None
    keyword_text: Optional[str] = None
    keyword_match_type: Optional[Literal["EXACT", "BROAD", "PHRASE"]] = None
    negative: Optional[bool] = None
    bid_modifier: Optional[float] = None


class AdGroupCriterion(Criterion):
    ad_group_id: str
    cpc_bid_micros: Optional[int] = None


class CampaignCriterion(Criterion):
    campaign_id: str
    negative: Optional[bool] = True
