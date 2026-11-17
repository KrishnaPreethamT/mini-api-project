from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class TripCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveller: str = Field(min_length=1)
    country: str = Field(min_length=1)
    budget_inr: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    travel_date: date

    @field_validator("travel_date")
    @classmethod
    def validate_travel_date(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("travel_date cannot be in the past")
        return value


class TripUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traveller: str | None = Field(default=None, min_length=1)
    country: str | None = Field(default=None, min_length=1)
    budget_inr: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    travel_date: date | None = None

    @field_validator("travel_date")
    @classmethod
    def validate_travel_date(cls, value: date | None) -> date | None:
        if value is not None and value < date.today():
            raise ValueError("travel_date cannot be in the past")
        return value


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    traveller: str
    country: str
    currency_code: str
    budget_inr: Decimal
    rate: Decimal | None = None
    budget_local: Decimal | None = None
    travel_date: date
    created_at: datetime

    @field_serializer("budget_inr", "rate", "budget_local", when_used="json")
    def serialize_amount(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None
