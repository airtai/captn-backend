from typing import List, Literal, Optional

from fastapi import Query
from pydantic import BaseModel, Field, field_validator


class AdBase(BaseModel):
    customer_id: str
    name: Optional[str] = None
    status: Optional[Literal["ENABLED", "PAUSED"]] = None


class Campaign(AdBase):
    campaign_id: Optional[str] = None
    budget_amount_micros: Optional[int] = None
    network_settings_target_google_search: Optional[bool] = None
    network_settings_target_search_network: Optional[bool] = None
    # network_settings_target_partner_search_network: Optional[bool] = None
    network_settings_target_content_network: Optional[bool] = None


class AdGroup(Campaign):
    ad_group_id: Optional[str] = None
    cpc_bid_micros: Optional[int] = None


class AdGroupAd(AdGroup):
    ad_id: Optional[str] = None
    final_url: Optional[str] = None
    headlines: Optional[List[str]] = Field(Query(default=None), max_length=15)
    descriptions: Optional[List[str]] = Field(Query(default=None), max_length=4)
    path1: Optional[str] = None
    path2: Optional[str] = None

    @classmethod
    def validate_field(
        cls,
        field_name: str,
        field: Optional[List[str]],
        min_list_length: int,
        max_string_length: int,
    ) -> Optional[List[str]]:
        if field is not None:
            if len(field) < min_list_length:
                raise ValueError(
                    f"{field_name} must have at least {min_list_length} items!"
                )
            for item in field:
                if len(item) > max_string_length:
                    raise ValueError(
                        f"Each {field_name} must be less than {max_string_length} characters!\nLength of {item} is {len(item)}"
                    )

        return field

    @field_validator("headlines")
    def headlines_validator(cls, headlines: Optional[List[str]]) -> Optional[List[str]]:
        return cls.validate_field(
            field_name="headlines",
            field=headlines,
            min_list_length=3,
            max_string_length=30,
        )

    @field_validator("descriptions")
    def descriptions_validator(
        cls, descriptions: Optional[List[str]]
    ) -> Optional[List[str]]:
        return cls.validate_field(
            field_name="descriptions",
            field=descriptions,
            min_list_length=2,
            max_string_length=90,
        )


class AdCopy(AdBase):
    ad_id: str
    headline: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=90)
    update_existing_headline_index: Optional[int] = None
    update_existing_description_index: Optional[int] = None
    final_url: Optional[str] = None
    final_mobile_urls: Optional[str] = None
    path1: Optional[str] = None
    path2: Optional[str] = None


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
        "campaign",
        "ad_group",
        "ad",
        "ad_group_criterion",
        "campaign_criterion",
        "geo_target",
    ]


class GeoTargetCriterion(BaseModel):
    customer_id: Optional[str] = None
    campaign_id: Optional[str] = None
    location_ids: Optional[List[str]] = Field(Query(default=None))
    location_names: Optional[List[str]] = Field(Query(default=None))
