from decimal import Decimal, ROUND_HALF_UP

from exceptions import TripNotFoundError
from repositories.trip_repository import TripRecord, TripRepository
from schemas import TripCreate, TripUpdate


class TripService:
    def __init__(self, repository, countries_client, rates_client):
        self._repository = repository
        self._countries_client = countries_client
        self._rates_client = rates_client

    async def create_trip(self, trip: TripCreate) -> TripRecord:
        country = await self._countries_client.get_country_details(trip.country)
        return self._repository.add(
            traveller=trip.traveller,
            country=country["country"],
            currency_code=country["currency"],
            budget_inr=trip.budget_inr,
            travel_date=trip.travel_date,
        )

    async def list_trips(self) -> list[dict]:
        trips = self._repository.list()
        rates_by_currency: dict[str, Decimal] = {}

        for trip in trips:
            if trip.currency_code not in rates_by_currency:
                exchange = await self._rates_client.get_exchange_rate(
                    "INR", trip.currency_code
                )
                rates_by_currency[trip.currency_code] = exchange["rate"]

        return [
            self._trip_with_rate(trip, rates_by_currency[trip.currency_code])
            for trip in trips
        ]

    async def get_trip(self, trip_id: int) -> TripRecord:
        trip = self._repository.get(trip_id)
        if trip is None:
            raise TripNotFoundError(f"Trip with id {trip_id} not found")
        return trip

    async def update_trip(self, trip_id: int, update: TripUpdate) -> TripRecord:
        changes = update.model_dump(exclude_unset=True, exclude_none=True)
        self._ensure_trip_exists(trip_id)

        if "country" in changes:
            country = await self._countries_client.get_country_details(changes["country"])
            changes["country"] = country["country"]
            changes["currency_code"] = country["currency"]

        trip = self._repository.update(trip_id, changes)
        if trip is None:
            raise TripNotFoundError(f"Trip with id {trip_id} not found")
        return trip

    async def delete_trip(self, trip_id: int) -> None:
        if not self._repository.delete(trip_id):
            raise TripNotFoundError(f"Trip with id {trip_id} not found")

    def _ensure_trip_exists(self, trip_id: int) -> TripRecord:
        trip = self._repository.get(trip_id)
        if trip is None:
            raise TripNotFoundError(f"Trip with id {trip_id} not found")
        return trip

    @staticmethod
    def _trip_with_rate(trip: TripRecord, rate: Decimal) -> dict:
        budget_local = (trip.budget_inr * rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return {
            "id": trip.id,
            "traveller": trip.traveller,
            "country": trip.country,
            "currency_code": trip.currency_code,
            "budget_inr": trip.budget_inr,
            "rate": rate,
            "budget_local": budget_local,
            "travel_date": trip.travel_date,
            "created_at": trip.created_at,
        }
