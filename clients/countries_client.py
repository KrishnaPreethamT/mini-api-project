from exceptions import ApiUnavailableError, CountryNotFoundError


class CountriesNowClient:
    def __init__(self, base_url: str, timeout: float):
        import httpx

        self._httpx = httpx
        self._base_url = base_url
        self._timeout = timeout

    async def get_country_details(self, country_name: str) -> dict[str, str]:
        currency_data = await self._get_country_data("currency", country_name)
        capital_data = await self._get_country_data("capital", country_name)

        country = currency_data.get("name")
        currency = currency_data.get("currency")
        capital = capital_data.get("capital")
        if not country or not currency or not capital:
            raise ApiUnavailableError("Country information is incomplete")

        return {"country": country, "currency": currency, "capital": capital}

    async def _get_country_data(self, category: str, country_name: str) -> dict:
        url = f"{self._base_url}/{category}/q"
        try:
            async with self._httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params={"country": country_name})
        except self._httpx.TimeoutException as exc:
            raise ApiUnavailableError("External API request timed out") from exc
        except self._httpx.RequestError as exc:
            raise ApiUnavailableError("Unable to connect to CountriesNow") from exc

        if response.status_code == 404:
            raise CountryNotFoundError(f"Country '{country_name}' not found")
        if response.status_code != 200:
            raise ApiUnavailableError("CountriesNow is unavailable")

        try:
            result = response.json()
        except ValueError as exc:
            raise ApiUnavailableError("CountriesNow returned an invalid response") from exc

        if not isinstance(result, dict):
            raise ApiUnavailableError("CountriesNow returned an invalid response")
        if result.get("error"):
            raise CountryNotFoundError(f"Country '{country_name}' not found")

        data = result.get("data")
        if not isinstance(data, dict):
            raise ApiUnavailableError("Unexpected response from CountriesNow")
        return data
