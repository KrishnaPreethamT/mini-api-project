"""
TravelService — Facade over CountriesNowClient and FrankfurterClient.

A route function calls one method here and gets back everything it needs.
The service knows nothing about HTTP requests or FastAPI; it only knows
about the two clients and the domain logic (budget conversion).
"""

from decimal import Decimal, ROUND_HALF_UP

from clients.countries_client import CountriesNowClient
from clients.frankfurter_client import FrankfurterClient


class TravelService:
    """
    Facade that orchestrates both API clients.

    Both clients are injected at construction time (dependency injection),
    so they can be swapped for fakes in tests without touching this class.
    """

    def __init__(
        self,
        countries_client: CountriesNowClient,
        frankfurter_client: FrankfurterClient,
    ) -> None:
        self._countries = countries_client
        self._fx = frankfurter_client

    # ------------------------------------------------------------------

    async def get_country_info(self, country: str) -> dict:
        """
        Return basic info about *country*.

        Returns:
            {country, currency, capital}

        Raises:
            CountryNotFoundError  — unknown country name
            ExternalAPIError      — upstream API problem
        """
        # Both calls can run conceptually in parallel, but keeping them
        # sequential is simpler for a Day-2 intern exercise.
        name     = await self._countries.get_country_name(country)
        currency = await self._countries.get_currency(country)
        capital  = await self._countries.get_capital(country)

        return {
            "country":  name,
            "currency": currency,
            "capital":  capital,
        }

    async def calculate_travel_budget(
        self, country: str, budget_inr: float
    ) -> dict:
        """
        Convert *budget_inr* into the local currency of *country*.

        Returns:
            {country, capital, currency, exchange_rate, rate_date,
             budget_inr, budget_local}

        Raises:
            CountryNotFoundError  — unknown country name
            ExternalAPIError      — upstream API problem
        """
        country_info  = await self.get_country_info(country)
        exchange_info = await self._fx.get_rate("INR", country_info["currency"])

        budget = Decimal(str(budget_inr))
        rate   = exchange_info["rate"]

        budget_local = (budget * rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "country":       country_info["country"],
            "capital":       country_info["capital"],
            "currency":      country_info["currency"],
            "exchange_rate": float(rate),
            "rate_date":     exchange_info["date"],
            "budget_inr":    budget_inr,
            "budget_local":  float(budget_local),
        }
