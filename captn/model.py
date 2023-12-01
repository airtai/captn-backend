from typing import Literal, Optional

from pydantic import BaseModel, ValidationError, field_validator


class AdBase(BaseModel):
    customer_id: Optional[str] = None
    ad_group_id: Optional[str] = None
    ad_id: Optional[str] = None
    name: Optional[str] = None
    cpc_bid_micros: Optional[int] = None
    status: Optional[Literal["ENABLED", "PAUSED"]] = None

    @field_validator("customer_id")
    def validate_customer_id(cls, v: str) -> str:
        if not v:
            raise ValidationError("Field required: customer_id is missing")
        return v

    @field_validator("ad_group_id")
    def validate_ad_group_id(cls, v: str) -> str:
        if not v:
            raise ValidationError("Field required: ad_group_id is missing")
        return v
