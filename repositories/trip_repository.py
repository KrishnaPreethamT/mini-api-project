from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from db import Trip


@dataclass(frozen=True)
class TripRecord:
    id: int
    traveller: str
    country: str
    currency_code: str
    budget_inr: Decimal
    travel_date: date
    created_at: datetime


class TripRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(
        self,
        traveller: str,
        country: str,
        currency_code: str,
        budget_inr: Decimal,
        travel_date: date,
    ) -> TripRecord:
        trip = Trip(
            traveller=traveller,
            country=country,
            currency_code=currency_code,
            budget_inr=budget_inr,
            travel_date=travel_date,
        )
        self._session.add(trip)
        self._session.flush()
        self._session.refresh(trip)
        return self._to_record(trip)

    def get(self, trip_id: int) -> TripRecord | None:
        trip = self._session.get(Trip, trip_id)
        return self._to_record(trip) if trip is not None else None

    def list(self) -> list[TripRecord]:
        trips = self._session.scalars(select(Trip).order_by(Trip.id)).all()
        return [self._to_record(trip) for trip in trips]

    def update(self, trip_id: int, changes: dict) -> TripRecord | None:
        trip = self._session.get(Trip, trip_id)
        if trip is None:
            return None

        for field, value in changes.items():
            setattr(trip, field, value)

        self._session.flush()
        self._session.refresh(trip)
        return self._to_record(trip)

    def delete(self, trip_id: int) -> bool:
        trip = self._session.get(Trip, trip_id)
        if trip is None:
            return False

        self._session.delete(trip)
        self._session.flush()
        return True

    @staticmethod
    def _to_record(trip: Trip) -> TripRecord:
        return TripRecord(
            id=trip.id,
            traveller=trip.traveller,
            country=trip.country,
            currency_code=trip.currency_code,
            budget_inr=trip.budget_inr,
            travel_date=trip.travel_date,
            created_at=trip.created_at,
        )
