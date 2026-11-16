from decimal import Decimal, ROUND_HALF_UP


class TravelService:
    def __init__(self, countries_client, rates_client):
        self._countries_client = countries_client
        self._rates_client = rates_client

    async def get_country_details(self, country_name: str) -> dict[str, str]:
        return await self._countries_client.get_country_details(country_name)

    async def calculate_travel_budget(self, country_name: str, budget_inr: float) -> dict:
        country = await self._countries_client.get_country_details(country_name)
        exchange = await self._rates_client.get_exchange_rate("INR", country["currency"])

        budget = Decimal(str(budget_inr))
        local_budget = (budget * exchange["rate"]).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "country": country["country"],
            "capital": country["capital"],
            "currency": country["currency"],
            "exchange_rate": float(exchange["rate"]),
            "rate_date": exchange["date"],
            "budget_inr": budget_inr,
            "budget_local": float(local_budget),
        }
