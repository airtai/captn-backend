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


class AdGroupCriterion(AdGroup):
    criterion_id: Optional[str] = None
    keyword_text: Optional[str] = None
    keyword_match_type: Optional[Literal["EXACT", "BROAD", "PHRASE"]] = None
    negative: Optional[bool] = None


class CampaignCriterion(Campaign):
    keyword_match_type: Optional[Literal["EXACT", "BROAD", "PHRASE"]] = None
    keyword_text: Optional[str] = None
    negative: Optional[bool] = True
    bid_modifier: Optional[float] = None
