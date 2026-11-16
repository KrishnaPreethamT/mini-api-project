"""
Adapter for the Frankfurter exchange-rate API.

Responsible for:
  - Knowing the Frankfurter URL structure
  - Making HTTP calls with httpx
  - Parsing the rate response into a plain dict
  - Raising ExternalAPIError — never FastAPI's HTTPException
"""

from decimal import Decimal, InvalidOperation

import httpx

from config import FRANKFURTER_BASE_URL, REQUEST_TIMEOUT
from exceptions import ExternalAPIError


class FrankfurterClient:
    """Adapter that hides the Frankfurter API behind a clean interface."""

    def __init__(
        self,
        base_url: str = FRANKFURTER_BASE_URL,
        timeout: float = REQUEST_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get(self, path: str) -> dict:
        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
        except httpx.TimeoutException:
            raise ExternalAPIError("Frankfurter request timed out")
        except httpx.RequestError as exc:
            raise ExternalAPIError(f"Could not connect to Frankfurter: {exc}")

        if response.status_code == 404:
            raise ExternalAPIError("Frankfurter returned 404 — unknown currency?")
        if response.status_code != 200:
            raise ExternalAPIError(
                f"Frankfurter returned unexpected status {response.status_code}"
            )

        try:
            return response.json()
        except ValueError:
            raise ExternalAPIError("Frankfurter returned invalid JSON")

    # ------------------------------------------------------------------
    # Public methods (the Adapter interface)
    # ------------------------------------------------------------------

    async def get_rate(self, from_currency: str, to_currency: str) -> dict:
        """
        Return a dict with keys: base, quote, rate (Decimal), date (str).

        Raises ExternalAPIError if the rate is missing or nonsensical.
        """
        body = await self._get(f"rate/{from_currency}/{to_currency}")

        try:
            rate = Decimal(str(body["rate"]))
            rate_date = body["date"]
        except (KeyError, TypeError, InvalidOperation):
            raise ExternalAPIError("Could not parse exchange rate from Frankfurter response")

        if not rate.is_finite() or rate <= 0:
            raise ExternalAPIError("Frankfurter returned an invalid exchange rate")

        return {
            "base": body.get("base", from_currency),
            "quote": body.get("quote", to_currency),
            "rate": rate,
            "date": rate_date,
        }
