from decimal import Decimal, InvalidOperation

from exceptions import ApiUnavailableError


class FrankfurterClient:
    def __init__(self, base_url: str, timeout: float):
        import httpx

        self._httpx = httpx
        self._base_url = base_url
        self._timeout = timeout

    async def get_exchange_rate(self, base_currency: str, target_currency: str) -> dict:
        url = f"{self._base_url}/rate/{base_currency}/{target_currency}"
        try:
            async with self._httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
        except self._httpx.TimeoutException as exc:
            raise ApiUnavailableError("External API request timed out") from exc
        except self._httpx.RequestError as exc:
            raise ApiUnavailableError("Unable to connect to Frankfurter") from exc

        if response.status_code != 200:
            raise ApiUnavailableError("Frankfurter is unavailable")

        try:
            result = response.json()
            rate = Decimal(str(result["rate"]))
            rate_date = result["date"]
        except (ValueError, KeyError, TypeError, InvalidOperation) as exc:
            raise ApiUnavailableError("Unable to read exchange rate information") from exc

        if not rate.is_finite() or rate <= 0:
            raise ApiUnavailableError("External API returned an invalid exchange rate")

        return {
            "base": result.get("base", base_currency),
            "quote": result.get("quote", target_currency),
            "rate": rate,
            "date": rate_date,
        }
