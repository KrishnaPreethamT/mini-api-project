"""
Adapter for the CountriesNow public API.

Responsible for:
  - Knowing the CountriesNow URL structure
  - Making HTTP calls with httpx
  - Translating responses into plain dicts the rest of the app understands
  - Raising CountryNotFoundError / ExternalAPIError — never FastAPI's HTTPException
"""

import httpx

from config import COUNTRIESNOW_BASE_URL, REQUEST_TIMEOUT
from exceptions import CountryNotFoundError, ExternalAPIError


class CountriesNowClient:
    """Adapter that hides the CountriesNow API behind a clean interface."""

    def __init__(
        self,
        base_url: str = COUNTRIESNOW_BASE_URL,
        timeout: float = REQUEST_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get(self, path: str, params: dict | None = None) -> dict:
        """Issue a GET request and return the parsed JSON body."""
        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params)
        except httpx.TimeoutException:
            raise ExternalAPIError("CountriesNow request timed out")
        except httpx.RequestError as exc:
            raise ExternalAPIError(f"Could not connect to CountriesNow: {exc}")

        if response.status_code == 404:
            raise ExternalAPIError("CountriesNow returned 404")
        if response.status_code != 200:
            raise ExternalAPIError(
                f"CountriesNow returned unexpected status {response.status_code}"
            )

        try:
            return response.json()
        except ValueError:
            raise ExternalAPIError("CountriesNow returned invalid JSON")

    async def _query(self, path: str, country: str) -> dict:
        """Call a /q endpoint and check for the API-level error flag."""
        body = await self._get(path, params={"country": country})
        if body.get("error"):
            raise CountryNotFoundError(country)
        data = body.get("data")
        if not isinstance(data, dict):
            raise ExternalAPIError("Unexpected response shape from CountriesNow")
        return data

    # ------------------------------------------------------------------
    # Public methods (the Adapter interface)
    # ------------------------------------------------------------------

    async def get_currency(self, country: str) -> str:
        """Return the ISO currency code for *country*."""
        data = await self._query("currency/q", country)
        currency = data.get("currency")
        if not currency:
            raise ExternalAPIError(f"CountriesNow did not return a currency for {country!r}")
        return currency

    async def get_capital(self, country: str) -> str:
        """Return the capital city name for *country*."""
        data = await self._query("capital/q", country)
        capital = data.get("capital")
        if not capital:
            raise ExternalAPIError(f"CountriesNow did not return a capital for {country!r}")
        return capital

    async def get_country_name(self, country: str) -> str:
        """Return the canonical country name as CountriesNow spells it."""
        data = await self._query("currency/q", country)
        name = data.get("name")
        if not name:
            raise ExternalAPIError(f"CountriesNow did not return a name for {country!r}")
        return name
