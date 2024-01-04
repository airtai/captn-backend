from typing import Literal, Optional

from pydantic import BaseModel, Field


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


class AdCopy(AdBase):
    ad_id: str
    headline: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=90)
    update_existing_headline_index: Optional[int] = None
    update_existing_description_index: Optional[int] = None
    final_urls: Optional[str] = None
    final_mobile_urls: Optional[str] = None


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


class RemoveResource(BaseModel):
    customer_id: str
    parent_id: Optional[str] = None
    resource_id: str
    resource_type: Literal[
        "campaign", "ad_group", "ad", "ad_group_criterion", "campaign_criterion"
    ]
